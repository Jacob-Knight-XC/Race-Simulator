"""Geocode meet venues and attach elevation / weather via Open-Meteo."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable, Optional

USER_AGENT = "RaceSimulator/1.0 (DIII XC; weekly refresh)"

# Shared across one enrichment pass (city/state and venue repeats a lot).
_GEOCODE_CACHE: dict[str, tuple[Optional[float], Optional[float], Optional[float]]] = {}
_ELEV_CACHE: dict[tuple[float, float], Optional[float]] = {}
_WEATHER_CACHE: dict[tuple[float, float, str], tuple[Optional[float], Optional[float]]] = {}


def _get_json(url: str, timeout: int = 30) -> Optional[dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def parse_location_block(location_text: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (venue_name, city, state) from a TFRRS address block."""
    if not location_text:
        return None, None, None
    parts = [p.strip() for p in re.split(r"\n+", location_text) if p.strip()]
    if not parts:
        return None, None, None
    venue = parts[0]
    city = state = None
    for part in reversed(parts):
        match = re.search(r"([^,]+),\s*([A-Z]{2})(?:\s+\d{5})?", part)
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            break
    return venue, city, state


def geocode_meet(
    city: Optional[str],
    state: Optional[str],
    venue_name: Optional[str] = None,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (lat, lon, elevation_m) using Open-Meteo geocoding."""
    query_parts = [p for p in (city, state, "USA") if p]
    if not query_parts and venue_name:
        query_parts = [venue_name, "USA"]
    if not query_parts:
        return None, None, None
    query = ", ".join(query_parts)
    if query in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[query]
    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urllib.parse.urlencode({"name": query, "count": 1, "language": "en", "format": "json"})
    )
    payload = _get_json(url)
    if not payload or not payload.get("results"):
        _GEOCODE_CACHE[query] = (None, None, None)
        return None, None, None
    hit = payload["results"][0]
    lat = hit.get("latitude")
    lon = hit.get("longitude")
    elev = hit.get("elevation")
    if lat is None or lon is None:
        _GEOCODE_CACHE[query] = (None, None, None)
        return None, None, None
    if elev is None:
        elev = fetch_elevation(float(lat), float(lon))
    result = (float(lat), float(lon), float(elev) if elev is not None else None)
    _GEOCODE_CACHE[query] = result
    return result


def fetch_elevation(lat: float, lon: float) -> Optional[float]:
    key = (round(lat, 3), round(lon, 3))
    if key in _ELEV_CACHE:
        return _ELEV_CACHE[key]
    url = (
        "https://api.open-meteo.com/v1/elevation?"
        + urllib.parse.urlencode({"latitude": lat, "longitude": lon})
    )
    payload = _get_json(url)
    if not payload:
        _ELEV_CACHE[key] = None
        return None
    values = payload.get("elevation") or []
    elev = float(values[0]) if values else None
    _ELEV_CACHE[key] = elev
    return elev


def _to_iso_date(meet_date: Optional[str]) -> Optional[str]:
    if not meet_date:
        return None
    cleaned = meet_date.strip().strip("()")
    for fmt in ("%m/%d/%Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def fetch_daily_weather(
    lat: float, lon: float, meet_date: Optional[str]
) -> tuple[Optional[float], Optional[float]]:
    """Return (temp_c_mean, precip_mm) for the meet date."""
    iso = _to_iso_date(meet_date)
    if not iso:
        return None, None
    key = (round(lat, 3), round(lon, 3), iso)
    if key in _WEATHER_CACHE:
        return _WEATHER_CACHE[key]
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        + urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "start_date": iso,
                "end_date": iso,
                "daily": "precipitation_sum,temperature_2m_mean",
                "timezone": "auto",
            }
        )
    )
    payload = _get_json(url)
    if not payload or "daily" not in payload:
        _WEATHER_CACHE[key] = (None, None)
        return None, None
    daily = payload["daily"]
    temps = daily.get("temperature_2m_mean") or [None]
    precips = daily.get("precipitation_sum") or [None]
    temp = float(temps[0]) if temps and temps[0] is not None else None
    precip = float(precips[0]) if precips and precips[0] is not None else None
    result = (temp, precip)
    _WEATHER_CACHE[key] = result
    return result


def enrich_meet_row(row: dict[str, Any], pause_s: float = 0.05) -> dict[str, Any]:
    """Fill lat/lon/elevation/weather fields on a meet dict in place."""
    venue, city, state = parse_location_block(row.get("location_text"))
    row["venue_name"] = row.get("venue_name") or venue
    row["city"] = row.get("city") or city
    row["state"] = row.get("state") or state

    if row.get("lat") is None or row.get("lon") is None:
        cache_key = ", ".join(p for p in (row.get("city"), row.get("state"), "USA") if p)
        cache_hit = cache_key in _GEOCODE_CACHE
        lat, lon, elev = geocode_meet(row.get("city"), row.get("state"), row.get("venue_name"))
        if lat is not None:
            row["lat"] = lat
            row["lon"] = lon
        if elev is not None:
            row["elevation_m"] = elev
        if not cache_hit:
            time.sleep(pause_s)

    if row.get("lat") is not None and row.get("lon") is not None:
        if row.get("elevation_m") is None:
            elev_key = (round(float(row["lat"]), 3), round(float(row["lon"]), 3))
            cache_hit = elev_key in _ELEV_CACHE
            row["elevation_m"] = fetch_elevation(row["lat"], row["lon"])
            if not cache_hit:
                time.sleep(pause_s)
        if row.get("temp_c") is None or row.get("precip_mm") is None:
            iso = _to_iso_date(row.get("meet_date"))
            weather_key = (
                round(float(row["lat"]), 3),
                round(float(row["lon"]), 3),
                iso or "",
            )
            cache_hit = iso is not None and weather_key in _WEATHER_CACHE
            temp, precip = fetch_daily_weather(row["lat"], row["lon"], row.get("meet_date"))
            row["temp_c"] = temp
            row["precip_mm"] = precip
            row["weather_source"] = "open-meteo"
            if iso is not None and not cache_hit:
                time.sleep(pause_s)
    return row


def enrich_meet_rows(
    rows: list[dict[str, Any]],
    *,
    workers: int = 4,
    pause_s: float = 0.05,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> list[dict[str, Any]]:
    """
    Enrich many meet rows, reusing geocode/weather caches across the batch.

    Uses a small thread pool for network calls. Order of returned rows matches input.
    """
    if not rows:
        return []
    total = len(rows)
    enriched: list[Optional[dict[str, Any]]] = [None] * total

    def _work(index: int, row: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return index, enrich_meet_row(dict(row), pause_s=pause_s)

    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(_work, idx, row) for idx, row in enumerate(rows)]
        for fut in as_completed(futures):
            idx, result = fut.result()
            enriched[idx] = result
            completed += 1
            if on_progress and (completed == total or completed % 50 == 0):
                on_progress(completed, total)
    return [row for row in enriched if row is not None]

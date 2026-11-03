"""Geocode meet venues and attach elevation / weather via Open-Meteo."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Optional

USER_AGENT = "RaceSimulator/1.0 (DIII XC; weekly refresh)"


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
    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urllib.parse.urlencode({"name": query, "count": 1, "language": "en", "format": "json"})
    )
    payload = _get_json(url)
    if not payload or not payload.get("results"):
        return None, None, None
    hit = payload["results"][0]
    lat = hit.get("latitude")
    lon = hit.get("longitude")
    elev = hit.get("elevation")
    if lat is None or lon is None:
        return None, None, None
    if elev is None:
        elev = fetch_elevation(float(lat), float(lon))
    return float(lat), float(lon), float(elev) if elev is not None else None


def fetch_elevation(lat: float, lon: float) -> Optional[float]:
    url = (
        "https://api.open-meteo.com/v1/elevation?"
        + urllib.parse.urlencode({"latitude": lat, "longitude": lon})
    )
    payload = _get_json(url)
    if not payload:
        return None
    values = payload.get("elevation") or []
    return float(values[0]) if values else None


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
        return None, None
    daily = payload["daily"]
    temps = daily.get("temperature_2m_mean") or [None]
    precips = daily.get("precipitation_sum") or [None]
    temp = float(temps[0]) if temps and temps[0] is not None else None
    precip = float(precips[0]) if precips and precips[0] is not None else None
    return temp, precip


def enrich_meet_row(row: dict[str, Any], pause_s: float = 0.15) -> dict[str, Any]:
    """Fill lat/lon/elevation/weather fields on a meet dict in place."""
    venue, city, state = parse_location_block(row.get("location_text"))
    row["venue_name"] = row.get("venue_name") or venue
    row["city"] = row.get("city") or city
    row["state"] = row.get("state") or state

    if row.get("lat") is None or row.get("lon") is None:
        lat, lon, elev = geocode_meet(row.get("city"), row.get("state"), row.get("venue_name"))
        if lat is not None:
            row["lat"] = lat
            row["lon"] = lon
        if elev is not None:
            row["elevation_m"] = elev
        time.sleep(pause_s)

    if row.get("lat") is not None and row.get("lon") is not None:
        if row.get("elevation_m") is None:
            row["elevation_m"] = fetch_elevation(row["lat"], row["lon"])
            time.sleep(pause_s)
        if row.get("temp_c") is None or row.get("precip_mm") is None:
            temp, precip = fetch_daily_weather(row["lat"], row["lon"], row.get("meet_date"))
            row["temp_c"] = temp
            row["precip_mm"] = precip
            row["weather_source"] = "open-meteo"
            time.sleep(pause_s)
    return row

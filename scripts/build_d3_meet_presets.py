#!/usr/bin/env python3
"""
Build data/d3_meet_presets.json for NCAA DIII conference & regional quick-loads.

Regions: parse NCAA 2025-26 Regional Box Draws PDF text (or --pdf-text path)
         and map labels onto TFRRS team names in app/racedata.db.

Conferences: derive membership from the latest conference championship field
             stored in racedata.db (same TFRRS names the app already uses).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "app" / "racedata.db"
DEFAULT_OUT = ROOT / "data" / "d3_meet_presets.json"
DEFAULT_PDF_TEXT = Path("/tmp/d3_regions.txt")

REGION_ORDER = [
    ("I", "East"),
    ("II", "Mideast"),
    ("III", "Niagara"),
    ("IV", "Mid-Atlantic"),
    ("V", "Metro"),
    ("VI", "Great Lakes"),
    ("VII", "South"),
    ("VIII", "North"),
    ("IX", "Midwest"),
    ("X", "West"),
]

# Conference championship meet-name needles -> display label.
CONFERENCE_PATTERNS: list[tuple[str, list[str]]] = [
    ("American Rivers", ["american rivers"]),
    ("American Southwest", ["american southwest", "asc conference championship"]),
    ("C2C", ["coast-to-coast", "coast to coast"]),
    ("CCIW", ["cciw"]),
    ("CCS", ["collegiate conference of the south", "ccs conference", "ccs xc"]),
    ("Centennial", ["centennial conference"]),
    ("Conference of New England", ["conference of new england"]),
    ("Empire 8", ["empire 8", "empire eight"]),
    ("GNAC", ["great northeast", "gnac"]),
    ("HCAC", ["heartland collegiate", "hcac"]),
    ("Landmark", ["landmark conference"]),
    ("Liberty League", ["liberty league"]),
    ("Little East", ["little east"]),
    ("MAC (Middle Atlantic)", ["middle atlantic conference"]),
    ("MASCAC", ["mascac"]),
    ("MIAC", ["miac"]),
    ("Midwest Conference", ["midwest conference"]),
    ("NACC", ["northern athletics", "nacc"]),
    ("NCAC", ["north coast athletic"]),
    ("NESCAC", ["nescac"]),
    ("NEWMAC", ["newmac"]),
    ("NJAC", ["new jersey athletic conference", "njac cross", "njac championship"]),
    ("North Atlantic", ["north atlantic conference"]),
    ("Northwest Conference", ["northwest conference"]),
    ("OAC", ["ohio athletic conference"]),
    ("ODAC", ["old dominion athletic", "odac"]),
    ("PAC", ["presidents' athletic", "presidents athletic"]),
    ("SAA", ["southern athletic association", "saa xc", "saa championship"]),
    ("SCAC", ["southern collegiate athletic"]),
    ("SCIAC", ["sciac"]),
    ("Skyline", ["skyline conference"]),
    ("SUNYAC", ["sunyac"]),
    ("UAA", ["university athletic association", "uaa xc", "uaa cross"]),
    ("USA South", ["usa south"]),
    ("United East", ["united east"]),
    ("WIAC", ["wiac", "wisconsin intercollegiate"]),
    ("Michigan Intercollegiate (MIAA)", ["michigan intercollegiate"]),
]

# NCAA / PDF short labels -> normalized TFRRS-ish keys
ALIASES = {
    "umass dartmouth": "umass dartmouth",
    "umass boston": "umass boston",
    "rpi": "rpi",
    "ric": "rhode island college",
    "trinity ct": "trinity conn",
    "trinity (ct)": "trinity conn",
    "mcla": "mass liberal arts",
    "alfred st": "alfred state",
    "ozarks": "ozarks ark",
    "carroll": "carroll wis",
    "wash u": "washington u",
    "u of chicago": "u of chicago",
    "umhb": "mary hardin baylor",
    "psu behrend": "penn state behrend",
    "psu berks": "penn state berks",
    "psu altoona": "penn state altoona",
    "psu harrisburg": "penn state harrisburg",
    "wash jeff": "washington jefferson",
    "usmma": "merchant marine",
    "nvu lyndon": "vermont state lyndon",
    "castleton": "vermont state castleton",
    "suny poly": "suny polytechnic",
    "new paltz st": "new paltz",
    "plattsburgh st": "plattsburgh",
    "potsdam st": "potsdam",
    "oswego st": "oswego",
    "cortland st": "cortland",
    "brockport st": "brockport",
    "morrisville st": "morrisville",
    "buffalo st": "buffalo state",
    "keene st": "keene state",
    "worcester st": "worcester state",
    "bridgewater st": "bridgewater state",
    "framingham st": "framingham state",
    "plymouth st": "plymouth state",
    "westfield st": "westfield state",
    "fitchburg st": "fitchburg state",
    "eastern conn st": "eastern connecticut",
    "western conn st": "western connecticut",
    "conn college": "connecticut college",
    "regin ma": "regis ma",
    "illinois tech": "illinois tech",
    "ozarks": "university of the ozarks",
    "willamette": "willamette",
    "willamette": "willamette",
    "letourneau": "letourneau",
    "le tourneau": "letourneau",
    "st catherine mn": "st catherine",
    "st benedict": "saint benedict",
    "william smith": "william smith",
    "hobart": "hobart",
    "agnes scott": "agnes scott",
    "bryn mawr": "bryn mawr",
    "mount holyoke": "mount holyoke",
    "smith": "smith",
    "wellesley": "wellesley",
    "simmons": "simmons",
    "cairn": "cairn",
    "virginia wesleyan": "virginia wesleyan",
    "western new england": "western new england",
    "suny canton": "canton",
    "maine maritime": "maine maritime",
    "thomas college": "thomas",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("'", "'").replace("'", "'").replace("'", "'").replace("`", "'")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_db_teams(conn: sqlite3.Connection) -> dict[str, dict[str, str]]:
    teams: dict[str, dict[str, str]] = {"m": {}, "f": {}}
    for name, gender in conn.execute("SELECT team_name, gender FROM Teams"):
        teams[gender][norm(name)] = name
    return teams


def match_name(raw: str, lookup: dict[str, str]) -> str | None:
    n = norm(raw)
    if not n or len(n) < 3:
        return None
    if n in lookup:
        return lookup[n]
    alias = ALIASES.get(n)
    if alias:
        if alias in lookup:
            return lookup[alias]
        hits = [v for k, v in lookup.items() if alias == k or alias in k]
        if len(set(hits)) == 1:
            return hits[0]
    # Prefer unique substring containment for short official labels.
    contains = [v for k, v in lookup.items() if n in k or k in n]
    if len(set(contains)) == 1:
        return contains[0]
    close = get_close_matches(n, list(lookup.keys()), n=1, cutoff=0.90)
    if close:
        return lookup[close[0]]
    return None


def parse_regions(text: str) -> dict[str, list[str]]:
    text = (
        text.replace("'", "'")
        .replace("'", "'")
        .replace("'", "'")
        .replace("Regin (MA)", "Regis (MA)")
        .replace("Willamette", "Willamette")  # PDF sometimes drops an 'e'
    )
    parts = re.split(r"\n\s*REGION\s+([IVX]+)\s*\(([^)]+)\)\s*\n", text)
    regions: dict[str, list[str]] = {}
    it = iter(parts[1:])
    for num, name, body in zip(it, it, it):
        key = f"Region {num} ({name.title().replace('Mid-atlantic', 'Mid-Atlantic')})"
        if "Mid-Atlantic" not in key and "Mid Atlantic" in name.title():
            key = f"Region {num} (Mid-Atlantic)"
        # Normalize Mid-Atlantic casing from PDF
        for roman, label in REGION_ORDER:
            if roman == num:
                key = f"Region {roman} ({label})"
                break
        names: list[str] = []
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            low = line.lower()
            if low.startswith(("men", "women", "institution", "starting")):
                continue
            line = re.sub(r"\(\d+\)", " ", line)
            chunks = re.findall(
                r"([A-Za-z][A-Za-z0-9 .'/&\-()]+?)\s+(\d{1,2})\b", line
            )
            if chunks:
                for name_part, _box in chunks:
                    name_part = name_part.strip(" -")
                    if len(name_part) < 3:
                        continue
                    if name_part.lower() in {"men", "women", "institution", "box"}:
                        continue
                    # Drop fragments from bad splits (e.g. "s (ME)")
                    if re.fullmatch(r"s\s*\([^)]+\)", name_part, re.I):
                        continue
                    names.append(name_part)
            else:
                if re.match(r"^[A-Za-z][A-Za-z0-9 .'/&\-()]+$", line) and not re.search(
                    r"\d", line
                ):
                    if not re.fullmatch(r"s\s*\([^)]+\)", line, re.I):
                        names.append(line.strip())
        seen: set[str] = set()
        uniq: list[str] = []
        for item in names:
            k = norm(item)
            if k and k not in seen:
                seen.add(k)
                uniq.append(item)
        regions[key] = uniq
    return regions


def conference_fields_from_db(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute(
        """
        SELECT r.meet_name, r.meet_date, t.team_name, t.gender
        FROM Races r
        JOIN Athletes a ON a.athlete_id = r.athlete_id
        JOIN Teams t ON t.team_id = a.team_id
        WHERE lower(r.meet_name) LIKE '%championship%'
          AND lower(r.meet_name) NOT LIKE '%njcaa%'
          AND lower(r.meet_name) NOT LIKE '%naia%'
          AND lower(r.meet_name) NOT LIKE '%preview%'
          AND lower(r.meet_name) NOT LIKE '%invite%'
          AND lower(r.meet_name) NOT LIKE '%open%'
          AND lower(r.meet_name) NOT LIKE '%fhsaa%'
          AND lower(r.meet_name) NOT LIKE '%ihsaa%'
          AND lower(r.meet_name) NOT LIKE '%division 1%'
          AND lower(r.meet_name) NOT LIKE '%division 2%'
          AND lower(r.meet_name) NOT LIKE '%division i %'
          AND lower(r.meet_name) NOT LIKE '%division ii %'
          AND lower(r.meet_name) NOT LIKE '%eastern ma%'
          AND lower(r.meet_name) NOT LIKE '%high school%'
        """
    ).fetchall()

    meet_teams: dict[str, dict] = defaultdict(
        lambda: {"m": set(), "f": set(), "date": ""}
    )
    for meet, date, team, gender in rows:
        meet_teams[meet][gender].add(team)
        if date and str(date) > str(meet_teams[meet]["date"]):
            meet_teams[meet]["date"] = str(date)

    conferences: dict[str, dict] = {}
    for label, patterns in CONFERENCE_PATTERNS:
        candidates = []
        for meet, info in meet_teams.items():
            ml = meet.lower()
            if any(p in ml for p in patterns):
                # Avoid high-school MIAA / unrelated
                if "miaa" in ml and "michigan" not in ml and "intercollegiate" not in ml:
                    if label.startswith("Michigan"):
                        continue
                score = (
                    1 if "championship" in ml else 0,
                    info["date"],
                    len(info["m"]) + len(info["f"]),
                )
                candidates.append((score, meet, info))
        if not candidates:
            continue
        candidates.sort(reverse=True)
        _score, meet, info = candidates[0]
        if len(info["m"]) + len(info["f"]) < 4:
            continue
        conferences[label] = {
            "source_meet": meet,
            "m": sorted(info["m"]),
            "f": sorted(info["f"]),
        }
    return conferences


def build(db_path: Path, pdf_text: Path, out_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    db_teams = load_db_teams(conn)
    conferences = conference_fields_from_db(conn)
    conn.close()

    pdf_regions = parse_regions(pdf_text.read_text(encoding="utf-8", errors="replace"))
    regions_out: dict[str, dict] = {}
    unmatched: dict[str, list[str]] = defaultdict(list)

    for roman, label in REGION_ORDER:
        key = f"Region {roman} ({label})"
        raw_names = pdf_regions.get(key, [])
        matched_m: list[str] = []
        matched_f: list[str] = []
        for raw in raw_names:
            m = match_name(raw, db_teams["m"])
            f = match_name(raw, db_teams["f"])
            if m:
                matched_m.append(m)
            if f:
                matched_f.append(f)
            if not m and not f:
                unmatched[key].append(raw)
        regions_out[key] = {
            "m": sorted(set(matched_m)),
            "f": sorted(set(matched_f)),
            "source": "NCAA 2025-26 Division III Regional Box Draws",
        }

    payload = {
        "division": "d3",
        "season": "2025-26",
        "regions": regions_out,
        "conferences": {
            label: {
                "m": info["m"],
                "f": info["f"],
                "source_meet": info["source_meet"],
            }
            for label, info in sorted(conferences.items())
        },
    }
    # Unmatched labels are printed for maintainers but not shipped in the JSON.
    payload["_unmatched_region_labels"] = {k: v for k, v in unmatched.items() if v}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shipped = {k: v for k, v in payload.items() if not k.startswith("_")}
    out_path.write_text(json.dumps(shipped, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--pdf-text", type=Path, default=DEFAULT_PDF_TEXT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if not args.pdf_text.is_file():
        raise SystemExit(
            f"Missing PDF text at {args.pdf_text}. "
            "Download the NCAA box-draw PDF and pdftotext/pypdf it first."
        )
    payload = build(args.db, args.pdf_text, args.out)
    print(
        f"Wrote {args.out} "
        f"({len(payload['regions'])} regions, {len(payload['conferences'])} conferences)"
    )
    for key, reg in payload["regions"].items():
        print(f"  {key}: m={len(reg['m'])} f={len(reg['f'])}")
    for label, conf in payload["conferences"].items():
        print(f"  {label}: m={len(conf['m'])} f={len(conf['f'])}")
    unmatched = payload.get("unmatched_region_labels") or {}
    n = sum(len(v) for v in unmatched.values())
    print(f"Unmatched region labels: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

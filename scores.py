#!/usr/bin/env python3
"""
scores.py — Fetch World Cup 2026 results and events, update index.html

Two data sources:
  1. football-data.org  — full-time & half-time scores, match status/winner
  2. ESPN (no key)      — goal scorers, minutes, pen/OG flags, red cards

Usage:
  python3 scores.py --api-key YOUR_FOOTBALL_DATA_KEY
  (get a free key at https://www.football-data.org/)



cd /Users/geofffay/wc26                         
pip3 install requests                                                         
python3 scores.py --api-key ebfb2f93b2d84919a843ecf10ee2ee95




 x-apisports-key: 52b666d2295c611526945b634938150f
Site: https://geoffreyjfay-sudo.github.io/wc26/
===============================
"""

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")


API_BASE = "https://api.football-data.org/v4"
COMPETITION = "WC"
SEASON = 2026

# Map football-data.org team names → our HTML names
TEAM_NAME_MAP = {
    "Mexico": "Mexico",
    "South Korea": "South Korea",
    "South Africa": "South Africa",
    "Czechia": "Czechia",
    "Czech Republic": "Czechia",
    "Canada": "Canada",
    "Switzerland": "Switzerland",
    "Qatar": "Qatar",
    "Bosnia and Herzegovina": "Bosnia & Hz.",
    "Bosnia & Herzegovina": "Bosnia & Hz.",
    "Bosnia-Herzegovina": "Bosnia & Hz.",
    "Brazil": "Brazil",
    "Morocco": "Morocco",
    "Scotland": "Scotland",
    "Haiti": "Haiti",
    "United States": "USA",
    "USA": "USA",
    "Australia": "Australia",
    "Paraguay": "Paraguay",
    "Turkey": "Turkey",
    "Türkiye": "Turkey",
    "Germany": "Germany",
    "Curaçao": "Curaçao",
    "Curacao": "Curaçao",
    "Ivory Coast": "Ivory Coast",
    "Côte d'Ivoire": "Ivory Coast",
    "Ecuador": "Ecuador",
    "Netherlands": "Netherlands",
    "Japan": "Japan",
    "Sweden": "Sweden",
    "Tunisia": "Tunisia",
    "Spain": "Spain",
    "Cape Verde": "Cape Verde",
    "Cabo Verde": "Cape Verde",
    "Cape Verde Islands": "Cape Verde",
    "Saudi Arabia": "Saudi Arabia",
    "Uruguay": "Uruguay",
    "Belgium": "Belgium",
    "Egypt": "Egypt",
    "Iran": "Iran",
    "IR Iran": "Iran",
    "New Zealand": "New Zealand",
    "France": "France",
    "Senegal": "Senegal",
    "Iraq": "Iraq",
    "Norway": "Norway",
    "Argentina": "Argentina",
    "Algeria": "Algeria",
    "Austria": "Austria",
    "Jordan": "Jordan",
    "Portugal": "Portugal",
    "DR Congo": "DR Congo",
    "Congo DR": "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "Republic of Congo": "DR Congo",
    "Uzbekistan": "Uzbekistan",
    "England": "England",
    "Croatia": "Croatia",
    "Ghana": "Ghana",
    "Panama": "Panama",
    "Colombia": "Colombia",
}

# All 72 group fixtures: id → (home, away)
# Matches our HTML FIXTURES const exactly
FIXTURES = {
    "A1": ("Mexico", "South Africa"),
    "A2": ("South Korea", "Czechia"),
    "A3": ("Czechia", "South Africa"),
    "A4": ("Mexico", "South Korea"),
    "A5": ("Czechia", "Mexico"),
    "A6": ("South Africa", "South Korea"),
    "B1": ("Canada", "Bosnia & Hz."),
    "B2": ("Qatar", "Switzerland"),
    "B3": ("Switzerland", "Bosnia & Hz."),
    "B4": ("Canada", "Qatar"),
    "B5": ("Switzerland", "Canada"),
    "B6": ("Bosnia & Hz.", "Qatar"),
    "C1": ("Brazil", "Morocco"),
    "C2": ("Haiti", "Scotland"),
    "C3": ("Scotland", "Morocco"),
    "C4": ("Brazil", "Haiti"),
    "C5": ("Scotland", "Brazil"),
    "C6": ("Morocco", "Haiti"),
    "D1": ("USA", "Paraguay"),
    "D2": ("Australia", "Turkey"),
    "D3": ("USA", "Australia"),
    "D4": ("Turkey", "Paraguay"),
    "D5": ("Turkey", "USA"),
    "D6": ("Paraguay", "Australia"),
    "E1": ("Germany", "Curaçao"),
    "E2": ("Ivory Coast", "Ecuador"),
    "E3": ("Germany", "Ivory Coast"),
    "E4": ("Ecuador", "Curaçao"),
    "E5": ("Ecuador", "Germany"),
    "E6": ("Curaçao", "Ivory Coast"),
    "F1": ("Netherlands", "Japan"),
    "F2": ("Sweden", "Tunisia"),
    "F3": ("Netherlands", "Sweden"),
    "F4": ("Tunisia", "Japan"),
    "F5": ("Japan", "Sweden"),
    "F6": ("Netherlands", "Tunisia"),
    "G1": ("Belgium", "Egypt"),
    "G2": ("Iran", "New Zealand"),
    "G3": ("Belgium", "Iran"),
    "G4": ("New Zealand", "Egypt"),
    "G5": ("Egypt", "Iran"),
    "G6": ("New Zealand", "Belgium"),
    "H1": ("Spain", "Cape Verde"),
    "H2": ("Saudi Arabia", "Uruguay"),
    "H3": ("Spain", "Saudi Arabia"),
    "H4": ("Uruguay", "Cape Verde"),
    "H5": ("Cape Verde", "Saudi Arabia"),
    "H6": ("Uruguay", "Spain"),
    "I1": ("France", "Senegal"),
    "I2": ("Iraq", "Norway"),
    "I3": ("France", "Iraq"),
    "I4": ("Norway", "Senegal"),
    "I5": ("Norway", "France"),
    "I6": ("Senegal", "Iraq"),
    "J1": ("Argentina", "Algeria"),
    "J2": ("Austria", "Jordan"),
    "J3": ("Argentina", "Austria"),
    "J4": ("Jordan", "Algeria"),
    "J5": ("Algeria", "Austria"),
    "J6": ("Jordan", "Argentina"),
    "K1": ("Portugal", "DR Congo"),
    "K2": ("Uzbekistan", "Colombia"),
    "K3": ("Portugal", "Uzbekistan"),
    "K4": ("Colombia", "DR Congo"),
    "K5": ("Colombia", "Portugal"),
    "K6": ("DR Congo", "Uzbekistan"),
    "L1": ("England", "Croatia"),
    "L2": ("Ghana", "Panama"),
    "L3": ("England", "Ghana"),
    "L4": ("Panama", "Croatia"),
    "L5": ("Panama", "England"),
    "L6": ("Croatia", "Ghana"),
}

# Build reverse lookup: (home, away) → fixture_id
FIXTURE_LOOKUP = {v: k for k, v in FIXTURES.items()}

# ── ESPN (no key required) ───────────────────────────────────────────────────
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
GROUP_STAGE_START = date(2026, 6, 11)
GROUP_STAGE_END = date(2026, 6, 28)

ESPN_TEAM_MAP = {
    "Bosnia-Herzegovina": "Bosnia & Hz.",
    "United States": "USA",
    "Türkiye": "Turkey",
    "Czech Republic": "Czechia",
    "Republic of Korea": "South Korea",
    "Dem. Republic of Congo": "DR Congo",
    "DR Congo": "DR Congo",
    "Ivory Coast": "Ivory Coast",
    "Côte d'Ivoire": "Ivory Coast",
    "Cape Verde Islands": "Cape Verde",
    "Cabo Verde": "Cape Verde",
    "IR Iran": "Iran",
    "Curacao": "Curaçao",
}

def normalize_espn(name: str) -> str:
    return ESPN_TEAM_MAP.get(name, name)


def fetch_espn_events() -> dict:
    """Fetch goal/red-card events for completed WC 2026 group matches from ESPN."""
    events = {}
    today = date.today()
    end = min(today + timedelta(days=1), GROUP_STAGE_END)

    d = GROUP_STAGE_START
    while d <= end:
        date_str = d.strftime("%Y%m%d")
        try:
            resp = requests.get(ESPN_BASE, params={"dates": date_str}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  ESPN warning: could not fetch {date_str}: {exc}")
            d += timedelta(days=1)
            continue

        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            # Use homeAway field — don't rely on array order
            home_raw = away_raw = ""
            for c in competitors:
                if c.get("homeAway") == "home":
                    home_raw = c["team"]["displayName"]
                elif c.get("homeAway") == "away":
                    away_raw = c["team"]["displayName"]
            if not home_raw or not away_raw:
                home_raw = competitors[0]["team"]["displayName"]
                away_raw = competitors[1]["team"]["displayName"]

            home = normalize_espn(home_raw)
            away = normalize_espn(away_raw)

            fixture_id = FIXTURE_LOOKUP.get((home, away))
            if not fixture_id:
                continue

            # Map ESPN team id → our normalised name
            team_id_map = {
                str(c["team"]["id"]): normalize_espn(c["team"]["displayName"])
                for c in competitors
            }

            goals, reds = [], []
            for det in comp.get("details", []):
                is_goal = det.get("scoringPlay", False)
                is_red  = det.get("redCard", False)
                if not is_goal and not is_red:
                    continue

                minute = det.get("clock", {}).get("displayValue", "?")
                athletes = det.get("athletesInvolved", [])
                raw_name = (athletes[0].get("fullName") or athletes[0].get("displayName", "?")) if athletes else "?"
                # ESPN occasionally returns "Firstname null" — strip trailing " null"
                player = raw_name.removesuffix(" null").strip() if raw_name else "?"
                team_name = team_id_map.get(str(det.get("team", {}).get("id", "")), "")

                if is_goal:
                    goals.append({
                        "min": minute,
                        "player": player,
                        "team": team_name,
                        "pen": det.get("penaltyKick", False),
                        "og": det.get("ownGoal", False),
                    })
                elif is_red:
                    reds.append({
                        "min": minute,
                        "player": player,
                        "team": team_name,
                    })

            entry = {}
            if goals:
                entry["goals"] = goals
            if reds:
                entry["reds"] = reds
            if entry:
                events[fixture_id] = entry

        d += timedelta(days=1)

    return events


def patch_events_html(html_path: Path, events: dict) -> None:
    content = html_path.read_text(encoding="utf-8")
    events_json = json.dumps(events, indent=2, ensure_ascii=False)
    new_block = (
        "// AUTO_EVENTS_START\n"
        f"const AUTO_EVENTS = {events_json};\n"
        "// AUTO_EVENTS_END"
    )
    updated, n = re.subn(
        r"// AUTO_EVENTS_START.*?// AUTO_EVENTS_END",
        new_block,
        content,
        flags=re.DOTALL,
    )
    if n == 0:
        sys.exit(
            "Could not find AUTO_EVENTS block in HTML. "
            "Make sure // AUTO_EVENTS_START and // AUTO_EVENTS_END markers exist."
        )
    html_path.write_text(updated, encoding="utf-8")
    print(f"✓ Patched {len(events)} match event(s) into {html_path}")


def normalize(name: str) -> str:
    return TEAM_NAME_MAP.get(name, name)


def fetch_matches(api_key: str) -> list:
    headers = {"X-Auth-Token": api_key}
    params = {"season": SEASON, "stage": "GROUP_STAGE"}
    resp = requests.get(
        f"{API_BASE}/competitions/{COMPETITION}/matches",
        headers=headers,
        params=params,
        timeout=15,
    )
    if resp.status_code == 403:
        sys.exit("API key rejected (403). Check your key at football-data.org.")
    if resp.status_code == 404:
        sys.exit(
            "Competition/season not found (404). "
            "The free tier may not yet have WC 2026 — check football-data.org."
        )
    resp.raise_for_status()
    return resp.json().get("matches", [])


def build_scores(matches: list) -> dict:
    scores = {}
    unmatched = []

    for m in matches:
        status = m.get("status", "")
        if status not in ("FINISHED", "IN_PLAY", "PAUSED"):
            continue

        score_data = m.get("score", {})
        full_time = score_data.get("fullTime", {})
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")

        # For live games use current score
        if home_goals is None or away_goals is None:
            current = score_data.get("halfTime", {})
            home_goals = current.get("home")
            away_goals = current.get("away")

        if home_goals is None or away_goals is None:
            continue

        home_raw = m.get("homeTeam", {}).get("name", "")
        away_raw = m.get("awayTeam", {}).get("name", "")
        home = normalize(home_raw)
        away = normalize(away_raw)

        fixture_id = FIXTURE_LOOKUP.get((home, away))
        if fixture_id:
            ht = score_data.get("halfTime", {})
            ht_home = ht.get("home")
            ht_away = ht.get("away")
            entry = {
                "home": str(home_goals),
                "away": str(away_goals),
                "status": status,
                "winner": score_data.get("winner"),
            }
            if ht_home is not None and ht_away is not None:
                entry["ht_home"] = str(ht_home)
                entry["ht_away"] = str(ht_away)
            scores[fixture_id] = entry
        else:
            unmatched.append(f"{home_raw} ({home}) vs {away_raw} ({away})")

    if unmatched:
        print("Warning: could not match these fixtures to our IDs:")
        for u in unmatched:
            print(f"  {u}")
        print("Add entries to TEAM_NAME_MAP or FIXTURES if needed.")

    return scores


def patch_html(html_path: Path, scores: dict) -> None:
    content = html_path.read_text(encoding="utf-8")

    scores_json = json.dumps(scores, indent=2, ensure_ascii=False)
    new_block = (
        "// AUTO_SCORES_START\n"
        f"const AUTO_SCORES = {scores_json};\n"
        "// AUTO_SCORES_END"
    )

    updated, n = re.subn(
        r"// AUTO_SCORES_START.*?// AUTO_SCORES_END",
        new_block,
        content,
        flags=re.DOTALL,
    )

    if n == 0:
        sys.exit(
            "Could not find AUTO_SCORES block in HTML. "
            "Make sure the markers // AUTO_SCORES_START and // AUTO_SCORES_END exist."
        )

    html_path.write_text(updated, encoding="utf-8")
    print(f"✓ Patched {len(scores)} result(s) into {html_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch WC 2026 scores and update index.html"
    )
    parser.add_argument("--api-key", required=True, help="football-data.org API key")
    parser.add_argument(
        "--html",
        default="index.html",
        help="Path to index.html (default: ./index.html)",
    )
    args = parser.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        sys.exit(f"HTML file not found: {html_path}")

    print(f"Fetching WC {SEASON} group stage scores from football-data.org...")
    matches = fetch_matches(args.api_key)
    print(f"  {len(matches)} matches returned from API")
    scores = build_scores(matches)
    finished = sum(1 for s in scores.values() if s["home"] != "")
    print(f"  {finished} completed match(es) found")
    patch_html(html_path, scores)

    print("Fetching goal events from ESPN...")
    events = fetch_espn_events()
    print(f"  {len(events)} fixture(s) with events")
    patch_events_html(html_path, events)

    print("Done. Re-upload the HTML to Netlify/GitHub Pages to publish.")


if __name__ == "__main__":
    main()

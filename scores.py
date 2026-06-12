#!/usr/bin/env python3
"""
scores.py — Fetch World Cup 2026 results and update index.html

Fetches completed match scores from football-data.org and patches the
AUTO_SCORES block in the HTML so the page shows current results without
manual entry.




Get a free API key at: https://www.football-data.org/
The free tier (Tier One) includes World Cup data.

Usage:
cd /Users/geofffay/wc26                         
pip3 install requests                                                         
python3 scores.py --api-key ebfb2f93b2d84919a843ecf10ee2ee95


 Workflow going forward:                                                    
                         
  # 1. Update scores
  python3 scores.py --api-key YOUR_KEY                                          
   
  # 2. Push to GitHub (site updates automatically)                              
  git add index.html                                             
  git commit -m "Update scores"                                                 
  git push                                                                   
                                                                                
  The site reflects the new scores within ~30 seconds of pushing.     


https://geoffreyjfay-sudo.github.io/wc26/   

===============================
"""

import argparse
import json
import re
import sys
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
            scores[fixture_id] = {"home": str(home_goals), "away": str(away_goals)}
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

    print(f"Fetching WC {SEASON} group stage results...")
    matches = fetch_matches(args.api_key)
    print(f"  {len(matches)} matches returned from API")

    scores = build_scores(matches)
    finished = sum(1 for s in scores.values() if s["home"] != "")
    print(f"  {finished} completed match(es) found")

    patch_html(html_path, scores)
    print("Done. Re-upload the HTML to Netlify/GitHub Pages to publish.")


if __name__ == "__main__":
    main()

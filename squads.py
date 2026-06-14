#!/usr/bin/env python3
"""
squads.py — Fetch WC 2026 squad rosters and generate squads.html

Usage:
  python3 squads.py --api-key YOUR_KEY

Fetches squad data from api-football.com (free tier: 100 req/day).
Caches results in squads_cache.json so interrupted runs can resume.
Re-run with the same command to top up any failed fetches.
Generates squads.html with all 48 team rosters embedded — no live API calls from the page.
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")

API_BASE = "https://v3.football.api-sports.io"

GROUPS = {
    "A": ["Mexico", "South Korea", "South Africa", "Czechia"],
    "B": ["Canada", "Switzerland", "Qatar", "Bosnia & Hz."],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["USA", "Australia", "Paraguay", "Turkey"],
    "E": ["Germany", "Ecuador", "Ivory Coast", "Curaçao"],
    "F": ["Netherlands", "Japan", "Tunisia", "Sweden"],
    "G": ["Belgium", "Iran", "Egypt", "New Zealand"],
    "H": ["Spain", "Uruguay", "Saudi Arabia", "Cape Verde"],
    "I": ["France", "Senegal", "Norway", "Iraq"],
    "J": ["Argentina", "Austria", "Algeria", "Jordan"],
    "K": ["Portugal", "Colombia", "DR Congo", "Uzbekistan"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

TEAM_IDS = {
    "Mexico": 16, "South Korea": 17, "South Africa": 1531, "Czechia": 770,
    "Canada": 5529, "Switzerland": 15, "Qatar": 1569, "Bosnia & Hz.": 1113,
    "Brazil": 6, "Morocco": 31, "Scotland": 1108, "Haiti": 2386,
    "USA": 2384, "Australia": 20, "Paraguay": 2380, "Turkey": 777,
    "Germany": 25, "Ecuador": 2382, "Ivory Coast": 1501, "Curaçao": 5530,
    "Netherlands": 1118, "Japan": 12, "Tunisia": 28, "Sweden": 5,
    "Belgium": 1, "Iran": 22, "Egypt": 32, "New Zealand": 4673,
    "Spain": 9, "Uruguay": 7, "Saudi Arabia": 23, "Cape Verde": 1533,
    "France": 2, "Senegal": 13, "Norway": 1090, "Iraq": 1567,
    "Argentina": 26, "Austria": 775, "Algeria": 1532, "Jordan": 1548,
    "Portugal": 27, "Colombia": 8, "DR Congo": 1517, "Uzbekistan": 1568,
    "England": 10, "Croatia": 3, "Ghana": 1504, "Panama": 11,
}

# person → [(team, tier), ...]
DRAW = {
    "Aisling":   [("England", 1), ("Algeria", 2)],
    "Catherine": [("Portugal", 1), ("Iraq", 2), ("New Zealand", 3)],
    "Cooper":    [("Ecuador", 1), ("Canada", 2)],
    "Craig":     [("Germany", 1), ("Saudi Arabia", 2)],
    "David":     [("Mexico", 1), ("Panama", 2)],
    "Eimíle":    [("Colombia", 1), ("Qatar", 2)],
    "Elsie":     [("Senegal", 1), ("Norway", 2)],
    "Eric":      [("Iran", 1), ("Scotland", 2)],
    "Evelyn":    [("Switzerland", 1), ("Austria", 2)],
    "Geoff":     [("Spain", 1), ("Ivory Coast", 2), ("Haiti", 3)],
    "Jane":      [("France", 1), ("South Africa", 2), ("Bosnia & Hz.", 3)],
    "Julian":    [("Belgium", 1), ("Sweden", 2)],
    "Leighanne": [("Uruguay", 1), ("Australia", 2), ("Curaçao", 3)],
    "Matthew":   [("Argentina", 1), ("Uzbekistan", 2)],
    "Oliver":    [("Brazil", 1), ("Czechia", 2)],
    "Orlagh":    [("Morocco", 1), ("DR Congo", 2), ("Cape Verde", 3)],
    "Peter":     [("USA", 1), ("Egypt", 2)],
    "Ruairí":    [("Japan", 1), ("Tunisia", 2)],
    "Siobhan":   [("Turkey", 1), ("Paraguay", 2)],
    "Sue":       [("Croatia", 1), ("South Korea", 2), ("Ghana", 3)],
    "Wes":       [("Netherlands", 1), ("Jordan", 2)],
}

FLAGS = {
    "Argentina": "🇦🇷", "Spain": "🇪🇸", "France": "🇫🇷", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Portugal": "🇵🇹", "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪", "Germany": "🇩🇪", "Croatia": "🇭🇷", "Colombia": "🇨🇴",
    "Mexico": "🇲🇽", "Senegal": "🇸🇳", "Uruguay": "🇺🇾", "USA": "🇺🇸",
    "Japan": "🇯🇵", "Switzerland": "🇨🇭", "Iran": "🇮🇷", "Turkey": "🇹🇷",
    "Ecuador": "🇪🇨", "Austria": "🇦🇹", "South Korea": "🇰🇷", "Australia": "🇦🇺",
    "Algeria": "🇩🇿", "Egypt": "🇪🇬", "Canada": "🇨🇦", "Norway": "🇳🇴",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Sweden": "🇸🇪", "Paraguay": "🇵🇾", "Ivory Coast": "🇨🇮",
    "Czechia": "🇨🇿", "Panama": "🇵🇦", "Qatar": "🇶🇦", "DR Congo": "🇨🇩",
    "Uzbekistan": "🇺🇿", "Iraq": "🇮🇶", "Saudi Arabia": "🇸🇦", "South Africa": "🇿🇦",
    "Jordan": "🇯🇴", "Cape Verde": "🇨🇻", "Bosnia & Hz.": "🇧🇦", "Ghana": "🇬🇭",
    "Haiti": "🇭🇹", "Curaçao": "🇨🇼", "New Zealand": "🇳🇿", "Tunisia": "🇹🇳",
    "South Korea": "🇰🇷",
}

# Build lookups
TEAM_OWNER = {}
TEAM_TIER = {}
for person, teams in DRAW.items():
    for team, tier in teams:
        TEAM_OWNER[team] = person
        TEAM_TIER[team] = tier

POSITION_ORDER = ["Goalkeeper", "Defender", "Midfielder", "Attacker"]
POSITION_LABEL = {
    "Goalkeeper": "Goalkeepers",
    "Defender": "Defenders",
    "Midfielder": "Midfielders",
    "Attacker": "Forwards",
}
TIER_LABEL = {1: "Tier 1", 2: "Tier 2", 3: "Bonus"}


# ── API fetch ─────────────────────────────────────────────────────────────────

def fetch_squad(api_key, team_id, team_name):
    headers = {"x-apisports-key": api_key}
    try:
        resp = requests.get(
            f"{API_BASE}/players/squads",
            headers=headers,
            params={"team": team_id},
            timeout=15,
        )
        data = resp.json()
        if data.get("errors"):
            print(f"    API error: {data['errors']}")
            return None
        response = data.get("response", [])
        if response:
            return response[0]["players"]
        return []
    except Exception as e:
        print(f"    Request failed: {e}")
        return None


def fetch_all_squads(api_key, cache_path):
    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        cached = sum(1 for v in cache.values() if v is not None)
        print(f"  Loaded cache: {cached} teams already fetched")

    all_teams = [t for teams in GROUPS.values() for t in teams]
    needed = [t for t in all_teams if t not in cache or cache[t] is None]

    if not needed:
        print("  All teams cached — skipping API calls")
        return cache

    if len(needed) > 0:
        print(f"  Fetching {len(needed)} team(s) — ~{len(needed)*2}s")

    for team in needed:
        team_id = TEAM_IDS.get(team)
        if not team_id:
            print(f"  {team}: no ID")
            cache[team] = []
            cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
            continue

        print(f"  {team} (id={team_id})...", end=" ", flush=True)
        players = fetch_squad(api_key, team_id, team)
        if players is not None:
            cache[team] = players
            print(f"{len(players)} players")
        else:
            print("FAILED — will retry next run")
            # Don't cache None so next run retries
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        time.sleep(7)

    return cache


# ── HTML generation ───────────────────────────────────────────────────────────

def squad_html(team, players):
    """Render the expandable squad section for one team."""
    if players is None:
        return '<div class="squad-error">Squad data unavailable</div>'
    if not players:
        return '<div class="squad-error">No squad data found</div>'

    by_pos = {p: [] for p in POSITION_ORDER}
    for pl in players:
        pos = pl.get("position", "Attacker")
        if pos not in by_pos:
            pos = "Attacker"
        by_pos[pos].append(pl)

    for pos in POSITION_ORDER:
        by_pos[pos].sort(key=lambda p: p.get("number") or 99)

    html = ""
    for pos in POSITION_ORDER:
        group = by_pos[pos]
        if not group:
            continue
        html += f'<div class="pos-group"><div class="pos-label">{POSITION_LABEL[pos]}</div>'
        for pl in group:
            num = pl.get("number") or "—"
            name = pl.get("name", "Unknown")
            age = pl.get("age", "")
            age_str = f'<span class="pl-age">{age}</span>' if age else ""
            html += f'<div class="player-row"><span class="pl-num">{num}</span><span class="pl-name">{name}</span>{age_str}</div>'
        html += "</div>"
    return html


def generate_html(squads):
    tier_cls = {1: "t1", 2: "t2", 3: "t3"}

    groups_html = ""
    for grp_letter, teams in GROUPS.items():
        teams_html = ""
        for team in teams:
            flag = FLAGS.get(team, "🏳")
            owner = TEAM_OWNER.get(team, "")
            tier = TEAM_TIER.get(team, 2)
            tc = tier_cls.get(tier, "t2")
            players = squads.get(team)
            squad_inner = squad_html(team, players)
            safe_id = team.replace(" ", "-").replace("&", "and").replace(".", "").replace("ç", "c").replace("ã", "a")

            teams_html += f"""
    <div class="team-card">
      <div class="team-header" onclick="toggleSquad('{safe_id}', this)">
        <span class="team-flag">{flag}</span>
        <div class="team-info">
          <span class="team-name">{team}</span>
          <span class="owner-badge {tc}">{owner} · {TIER_LABEL[tier]}</span>
        </div>
        <span class="squad-arrow">▼</span>
      </div>
      <div class="squad-body" id="sq-{safe_id}">
        {squad_inner}
      </div>
    </div>"""

        groups_html += f"""
  <div class="group-block">
    <div class="group-heading">Group {grp_letter}</div>
    <div class="teams-list">{teams_html}
    </div>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Squad Lists — Family World Cup 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --dark:    #0d1a0e;
  --panel:   #132015;
  --border:  rgba(255,255,255,0.09);
  --gold:    #d4a017;
  --gold-lt: #f0c040;
  --cream:   #f0ead8;
  --muted:   rgba(240,234,216,0.45);
  --t1:      #f0c040;
  --t2:      #4dcf6a;
  --t3:      #ff8a8a;
  --green-lt: #4dcf6a;
}}
body {{ background: var(--dark); color: var(--cream); font-family: 'Inter', sans-serif; min-height: 100vh; }}

/* NAV */
.topnav {{
  background: rgba(9,18,8,0.92); border-bottom: 1px solid var(--border);
  padding: 10px 24px; display: flex; gap: 12px; align-items: center;
  position: sticky; top: 0; z-index: 100;
  backdrop-filter: blur(8px);
}}
.topnav a {{
  color: var(--muted); text-decoration: none; padding: 5px 14px; border-radius: 20px;
  border: 1px solid transparent; transition: all 0.15s;
  font-family: 'Bebas Neue', sans-serif; font-size: 0.9rem; letter-spacing: 0.07em;
}}
.topnav a:hover {{ color: var(--cream); border-color: var(--border); }}
.topnav a.active {{ background: var(--gold); color: var(--dark); border-color: var(--gold); }}

/* HEADER */
header {{
  background: linear-gradient(160deg, #0a2e0e 0%, #0d1a0e 60%);
  border-bottom: 2px solid var(--gold);
  padding: 36px 24px 28px; text-align: center; position: relative; overflow: hidden;
}}
header::before {{
  content: '⚽'; position: absolute; font-size: 260px; opacity: 0.04;
  top: -40px; right: -40px; line-height: 1; pointer-events: none;
}}
header h1 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2.2rem, 6vw, 4.2rem); letter-spacing: 0.06em;
  background: linear-gradient(135deg, var(--gold-lt), var(--gold));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; line-height: 1;
}}
header p {{ color: var(--muted); margin-top: 8px; font-size: 0.95rem; }}

/* LEGEND */
.legend {{
  display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;
  padding: 14px 24px; border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
}}
.leg-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: var(--muted); }}
.leg-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}

/* LAYOUT */
main {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px 60px; }}

/* GROUPS GRID */
.groups-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}}
@media(max-width: 900px) {{ .groups-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media(max-width: 560px) {{ .groups-grid {{ grid-template-columns: 1fr; }} }}

/* GROUP BLOCK */
.group-block {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}}
.group-heading {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1rem; letter-spacing: 0.12em; color: var(--gold-lt);
  padding: 8px 14px;
  background: rgba(255,255,255,0.04);
  border-bottom: 1px solid var(--border);
}}
.teams-list {{ display: flex; flex-direction: column; }}

/* TEAM CARD */
.team-card {{ border-bottom: 1px solid rgba(255,255,255,0.04); }}
.team-card:last-child {{ border-bottom: none; }}
.team-header {{
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; cursor: pointer;
  transition: background 0.15s; user-select: none;
}}
.team-header:hover {{ background: rgba(255,255,255,0.04); }}
.team-flag {{ font-size: 1.4rem; flex-shrink: 0; }}
.team-info {{ flex: 1; min-width: 0; }}
.team-name {{ display: block; font-weight: 600; font-size: 0.92rem; }}
.owner-badge {{
  display: inline-block; font-size: 0.68rem; padding: 1px 7px; border-radius: 8px;
  font-weight: 600; margin-top: 2px; letter-spacing: 0.02em;
}}
.owner-badge.t1 {{ background: rgba(240,192,64,0.2); color: var(--t1); border: 1px solid rgba(240,192,64,0.3); }}
.owner-badge.t2 {{ background: rgba(77,207,106,0.15); color: var(--t2); border: 1px solid rgba(77,207,106,0.25); }}
.owner-badge.t3 {{ background: rgba(255,138,138,0.15); color: var(--t3); border: 1px solid rgba(255,138,138,0.25); }}
.squad-arrow {{ color: var(--muted); font-size: 0.7rem; flex-shrink: 0; transition: transform 0.2s; }}
.squad-arrow.open {{ transform: rotate(180deg); }}

/* SQUAD BODY */
.squad-body {{ display: none; padding: 0 14px 12px; }}
.squad-body.open {{ display: block; }}
.squad-error {{ font-size: 0.8rem; color: var(--muted); font-style: italic; padding: 8px 0; }}

/* POSITION GROUP */
.pos-group {{ margin-top: 10px; }}
.pos-label {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 0.72rem; letter-spacing: 0.1em;
  color: var(--muted); margin-bottom: 4px;
  padding-bottom: 3px; border-bottom: 1px solid rgba(255,255,255,0.05);
}}
.player-row {{
  display: flex; align-items: baseline; gap: 8px;
  padding: 3px 0; font-size: 0.8rem;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}}
.player-row:last-child {{ border-bottom: none; }}
.pl-num {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 0.85rem; color: var(--gold-lt);
  min-width: 20px; text-align: right; flex-shrink: 0;
}}
.pl-name {{ flex: 1; color: var(--cream); }}
.pl-age {{ font-size: 0.72rem; color: var(--muted); flex-shrink: 0; }}
</style>
</head>
<body>

<nav class="topnav">
  <a href="index.html">📅 Calendar</a>
  <a href="index.html#standings">🏆 Standings</a>
  <a href="squads.html" class="active">👕 Squads</a>
</nav>

<header>
  <h1>Squad Lists 2026</h1>
  <p>All 48 teams · Click any team to expand their roster</p>
</header>

<div class="legend">
  <div class="leg-item"><div class="leg-dot" style="background:var(--t1)"></div> Tier 1 — Top Seed</div>
  <div class="leg-item"><div class="leg-dot" style="background:var(--t2)"></div> Tier 2</div>
  <div class="leg-item"><div class="leg-dot" style="background:var(--t3)"></div> Tier 3 Bonus</div>
</div>

<main>
  <div class="groups-grid">
{groups_html}
  </div>
</main>

<script>
function toggleSquad(id, headerEl) {{
  const body = document.getElementById('sq-' + id);
  const arrow = headerEl.querySelector('.squad-arrow');
  const open = body.classList.toggle('open');
  arrow.classList.toggle('open', open);
}}
</script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch WC 2026 squads and generate squads.html")
    parser.add_argument("--api-key", required=True, help="api-football.com API key")
    parser.add_argument("--cache", default="squads_cache.json", help="Cache file path")
    parser.add_argument("--output", default="squads.html", help="Output HTML file")
    args = parser.parse_args()

    cache_path = Path(args.cache)
    output_path = Path(args.output)

    print(f"Fetching WC 2026 squad rosters (48 teams, ~2s each)...")
    squads = fetch_all_squads(args.api_key, cache_path)

    fetched = sum(1 for v in squads.values() if v is not None and len(v) > 0)
    print(f"\nGenerating {output_path} ({fetched}/48 teams with data)...")
    html = generate_html(squads)
    output_path.write_text(html, encoding="utf-8")
    print(f"✓ Done — open {output_path} to view")


if __name__ == "__main__":
    main()

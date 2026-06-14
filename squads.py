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

def build_squad_data(squads):
    """Return squads dict as compact JSON for embedding in the page."""
    out = {}
    for team, players in squads.items():
        if not players:
            out[team] = []
            continue
        by_pos = {p: [] for p in POSITION_ORDER}
        for pl in players:
            pos = pl.get("position", "Attacker")
            if pos not in by_pos:
                pos = "Attacker"
            by_pos[pos].append({
                "n": pl.get("number") or 0,
                "name": pl.get("name", ""),
                "age": pl.get("age", ""),
                "photo": pl.get("photo", ""),
                "pos": pos,
            })
        for pos in POSITION_ORDER:
            by_pos[pos].sort(key=lambda p: p["n"] or 99)
        out[team] = [p for pos in POSITION_ORDER for p in by_pos[pos]]
    return out


def generate_html(squads):
    tier_cls = {1: "t1", 2: "t2", 3: "t3"}
    squad_data = build_squad_data(squads)
    squad_json = json.dumps(squad_data, ensure_ascii=False)

    # Build team tiles grouped by group
    groups_html = ""
    for grp_letter, teams in GROUPS.items():
        tiles = ""
        for team in teams:
            flag = FLAGS.get(team, "🏳")
            owner = TEAM_OWNER.get(team, "")
            tier = TEAM_TIER.get(team, 2)
            tc = tier_cls.get(tier, "t2")
            safe = team.replace('"', '\\"')
            tiles += f"""
      <div class="team-tile" onclick="openSquad('{safe}')">
        <span class="tile-flag">{flag}</span>
        <span class="tile-name">{team}</span>
        <span class="tile-owner {tc}">{owner}</span>
      </div>"""

        groups_html += f"""
    <div class="group-section">
      <div class="group-label">Group {grp_letter}</div>
      <div class="team-grid">{tiles}
      </div>
    </div>"""

    pos_label_js = json.dumps(POSITION_LABEL)

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
  --panel2:  #1a2e1c;
  --border:  rgba(255,255,255,0.09);
  --gold:    #d4a017;
  --gold-lt: #f0c040;
  --cream:   #f0ead8;
  --muted:   rgba(240,234,216,0.45);
  --t1:      #f0c040;
  --t2:      #4dcf6a;
  --t3:      #ff8a8a;
}}
body {{ background: var(--dark); color: var(--cream); font-family: 'Inter', sans-serif; min-height: 100vh; }}

/* ── NAV ── */
.topnav {{
  background: rgba(9,18,8,0.92); border-bottom: 1px solid var(--border);
  padding: 10px 24px; display: flex; gap: 8px; align-items: center;
  position: sticky; top: 0; z-index: 200; backdrop-filter: blur(8px);
}}
.topnav a {{
  color: var(--muted); text-decoration: none; padding: 5px 14px; border-radius: 20px;
  border: 1px solid transparent; transition: all 0.15s;
  font-family: 'Bebas Neue', sans-serif; font-size: 0.9rem; letter-spacing: 0.07em;
}}
.topnav a:hover {{ color: var(--cream); border-color: var(--border); }}
.topnav a.active {{ background: var(--gold); color: var(--dark); border-color: var(--gold); }}
.nav-short {{ display: none; }}
@media(max-width: 600px) {{
  .topnav {{ padding: 8px 8px; gap: 2px; }}
  .topnav a {{ padding: 5px 8px; font-size: 0.8rem; letter-spacing: 0.04em; }}
  .nav-full {{ display: none; }}
  .nav-short {{ display: inline; }}
}}

/* ── HEADER ── */
header {{
  background: linear-gradient(160deg, #0a2e0e 0%, #0d1a0e 60%);
  border-bottom: 2px solid var(--gold);
  padding: 36px 24px 28px; text-align: center; position: relative; overflow: hidden;
}}
header::before {{
  content: '👕'; position: absolute; font-size: 220px; opacity: 0.04;
  top: -30px; right: -20px; line-height: 1; pointer-events: none;
}}
header h1 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2.2rem, 6vw, 4.2rem); letter-spacing: 0.06em;
  background: linear-gradient(135deg, var(--gold-lt), var(--gold));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; line-height: 1;
}}
header p {{ color: var(--muted); margin-top: 8px; font-size: 0.95rem; }}

/* ── LEGEND ── */
.legend {{
  display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;
  padding: 14px 24px; border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
}}
.leg-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: var(--muted); }}
.leg-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

/* ── MAIN ── */
main {{ max-width: 1140px; margin: 0 auto; padding: 28px 16px 60px; }}

/* ── GROUP SECTION ── */
.group-section {{ margin-bottom: 36px; }}
.group-label {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.1rem; letter-spacing: 0.12em; color: var(--gold-lt);
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}}

/* ── TEAM TILES ── */
.team-grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}}
@media(max-width: 700px) {{ .team-grid {{ grid-template-columns: repeat(2, 1fr); }} }}

.team-tile {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 12px 14px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
}}
.team-tile:hover {{
  border-color: var(--gold);
  background: rgba(212,160,23,0.07);
  transform: translateY(-2px);
}}
.tile-flag {{ font-size: 2.4rem; line-height: 1; }}
.tile-name {{ font-weight: 600; font-size: 0.88rem; color: var(--cream); line-height: 1.2; }}
.tile-owner {{
  font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; font-weight: 600;
}}
.tile-owner.t1 {{ background: rgba(240,192,64,0.2); color: var(--t1); border: 1px solid rgba(240,192,64,0.3); }}
.tile-owner.t2 {{ background: rgba(77,207,106,0.15); color: var(--t2); border: 1px solid rgba(77,207,106,0.25); }}
.tile-owner.t3 {{ background: rgba(255,138,138,0.15); color: var(--t3); border: 1px solid rgba(255,138,138,0.25); }}

/* ── MODAL ── */
.modal-overlay {{
  display: none; position: fixed; inset: 0; z-index: 300;
  background: rgba(0,0,0,0.8); align-items: center; justify-content: center;
  padding: 16px; backdrop-filter: blur(4px);
}}
.modal-overlay.open {{ display: flex; }}
.modal-box {{
  background: var(--panel); border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px; max-width: 820px; width: 100%;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 32px 80px rgba(0,0,0,0.8);
  display: flex; flex-direction: column;
}}

/* Modal header */
.modal-head {{
  background: var(--panel2);
  border-bottom: 1px solid var(--border);
  padding: 20px 24px;
  display: flex; align-items: center; gap: 16px;
  position: sticky; top: 0; z-index: 1;
  border-radius: 14px 14px 0 0;
}}
.modal-flag {{ font-size: 3rem; line-height: 1; flex-shrink: 0; }}
.modal-title {{
  flex: 1;
}}
.modal-team-name {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 2rem; letter-spacing: 0.06em; color: var(--cream); line-height: 1;
}}
.modal-meta {{ font-size: 0.82rem; color: var(--muted); margin-top: 4px; }}
.modal-owner-badge {{
  font-size: 0.75rem; padding: 3px 10px; border-radius: 12px; font-weight: 600;
  margin-left: 8px;
}}
.modal-owner-badge.t1 {{ background: rgba(240,192,64,0.2); color: var(--t1); border: 1px solid rgba(240,192,64,0.3); }}
.modal-owner-badge.t2 {{ background: rgba(77,207,106,0.15); color: var(--t2); border: 1px solid rgba(77,207,106,0.25); }}
.modal-owner-badge.t3 {{ background: rgba(255,138,138,0.15); color: var(--t3); border: 1px solid rgba(255,138,138,0.25); }}
.modal-close {{
  background: rgba(255,255,255,0.08); border: none; color: rgba(240,234,216,0.6);
  border-radius: 50%; width: 34px; height: 34px; font-size: 1.1rem;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.15s; flex-shrink: 0;
}}
.modal-close:hover {{ background: rgba(255,255,255,0.18); color: var(--cream); }}

/* Modal body */
.modal-body {{ padding: 20px 24px 24px; }}
.positions-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}}
@media(max-width: 560px) {{ .positions-grid {{ grid-template-columns: 1fr; }} }}

.pos-section {{ }}
.pos-heading {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 0.85rem; letter-spacing: 0.12em; color: var(--muted);
  padding-bottom: 6px; margin-bottom: 8px;
  border-bottom: 1px solid var(--border);
}}

/* Player row */
.player-row {{
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}}
.player-row:last-child {{ border-bottom: none; }}
.pl-photo {{
  width: 40px; height: 40px; border-radius: 50%; object-fit: cover; flex-shrink: 0;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
}}
.pl-photo-empty {{
  width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
}}
.pl-num {{
  font-family: 'Bebas Neue', sans-serif; font-size: 1rem;
  color: var(--gold-lt); min-width: 22px; text-align: right; flex-shrink: 0;
}}
.pl-info {{ flex: 1; min-width: 0; }}
.pl-name {{ font-size: 0.85rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.pl-age {{ font-size: 0.72rem; color: var(--muted); }}
</style>
</head>
<body>

<nav class="topnav">
  <a href="index.html">📅 <span class="nav-full">Calendar</span><span class="nav-short">Cal</span></a>
  <a href="index.html#standings">🏆 <span class="nav-full">Standings</span><span class="nav-short">Table</span></a>
  <a href="index.html#group-tables-section">📋 Groups</a>
  <a href="index.html#results-entry-section">⚽ Results</a>
  <a href="squads.html" class="active">👕 Squads</a>
</nav>

<header>
  <h1>Squad Lists 2026</h1>
  <p>All 48 teams · Click any team to view their squad</p>
</header>

<div class="legend">
  <div class="leg-item"><div class="leg-dot" style="background:var(--t1)"></div> Tier 1 — Top Seed</div>
  <div class="leg-item"><div class="leg-dot" style="background:var(--t2)"></div> Tier 2</div>
  <div class="leg-item"><div class="leg-dot" style="background:var(--t3)"></div> Tier 3 Bonus</div>
</div>

<main>
{groups_html}
</main>

<!-- SQUAD MODAL -->
<div class="modal-overlay" id="squadModal" onclick="if(event.target===this)closeSquad()">
  <div class="modal-box">
    <div class="modal-head">
      <span class="modal-flag" id="modalFlag"></span>
      <div class="modal-title">
        <div class="modal-team-name" id="modalTeamName"></div>
        <div class="modal-meta" id="modalMeta"></div>
      </div>
      <button class="modal-close" onclick="closeSquad()">✕</button>
    </div>
    <div class="modal-body">
      <div class="positions-grid" id="modalSquad"></div>
    </div>
  </div>
</div>

<script>
const SQUADS = {squad_json};
const DRAW = {json.dumps({t: person for person, teams in DRAW.items() for t, _ in teams}, ensure_ascii=False)};
const TIERS = {json.dumps(TEAM_TIER, ensure_ascii=False)};
const FLAGS = {json.dumps(FLAGS, ensure_ascii=False)};
const POS_LABEL = {pos_label_js};
const POS_ORDER = {json.dumps(POSITION_ORDER)};
const TIER_LABEL = {json.dumps(TIER_LABEL)};
const TIER_CLS = {{1:"t1",2:"t2",3:"t3"}};

function openSquad(team) {{
  const players = SQUADS[team] || [];
  const flag = FLAGS[team] || '🏳';
  const owner = DRAW[team] || '';
  const tier = TIERS[team] || 2;
  const tc = TIER_CLS[tier] || 't2';

  document.getElementById('modalFlag').textContent = flag;
  document.getElementById('modalTeamName').textContent = team;
  document.getElementById('modalMeta').innerHTML =
    `${{owner ? `<span class="modal-owner-badge ${{tc}}">${{owner}} · ${{TIER_LABEL[tier]}}</span>` : ''}}`;

  // Group by position
  const byPos = {{}};
  for (const pos of POS_ORDER) byPos[pos] = [];
  for (const p of players) {{
    const pos = p.pos || 'Attacker';
    (byPos[pos] || (byPos['Attacker'])).push(p);
  }}

  let html = '';
  for (const pos of POS_ORDER) {{
    const group = byPos[pos];
    if (!group.length) continue;
    html += `<div class="pos-section"><div class="pos-heading">${{POS_LABEL[pos]}}</div>`;
    for (const p of group) {{
      const photo = p.photo
        ? `<img class="pl-photo" src="${{p.photo}}" alt="" loading="lazy" onerror="this.classList.add('pl-photo-empty');this.removeAttribute('src')">`
        : `<span class="pl-photo-empty"></span>`;
      html += `<div class="player-row">
        ${{photo}}
        <span class="pl-num">${{p.n || '—'}}</span>
        <div class="pl-info">
          <div class="pl-name">${{p.name}}</div>
          ${{p.age ? `<div class="pl-age">Age ${{p.age}}</div>` : ''}}
        </div>
      </div>`;
    }}
    html += '</div>';
  }}

  document.getElementById('modalSquad').innerHTML = html;
  document.getElementById('squadModal').classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeSquad() {{
  document.getElementById('squadModal').classList.remove('open');
  document.body.style.overflow = '';
}}

document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeSquad(); }});
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

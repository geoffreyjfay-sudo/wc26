# Family World Cup 2026 Sweepstake — Project Guide

This is a small family sweepstake project for the 2026 FIFA World Cup (USA/Canada/Mexico, 11 June – 19 July 2026). It is a set of self-contained HTML pages plus a couple of printable PDFs. There is **no build step, no framework, no server** — every page is a single HTML file that runs by double-clicking it or hosting it as a static file.

If you are Claude Code reading this: the goal is to keep these files simple, self-contained, and editable by a non-developer. Do not introduce a framework, a bundler, or a backend unless explicitly asked. Vanilla HTML/CSS/JS only. Keep all CSS and JS inline in each HTML file.

---

## The files

| File | What it is |
|------|-----------|
| `worldcup-calendar.html` | Main page. Day-by-day fixture calendar (all 72 group games, Irish kick-off times) **plus** an editable standings/leaderboard section lower down the same page. Filter bar to show one person's games. Scores entered here are saved to a cookie. Nav at top scrolls between Calendar and Standings sections. |
| `previews.html` | Standalone page of 72 WhatsApp-style match previews, one per group game. Each has a "Copy to WhatsApp" button. Filterable by family member. Football-fact-led banter with light family references. |
| `standings.html` | Earlier standalone version of the standings/results page. The calendar page now contains its own standings section, so this file is largely superseded — keep it or delete it, but the live one is inside `worldcup-calendar.html`. |
| `worldcup-draw.html` | The original randomised draw tool used to assign teams to people. The draw is **done** (results below), so this is now an archive/keepsake. Staged draw: bonus 6 first, then Tier 2, then Tier 1. Persists to a cookie. |
| `WorldCup-WallChart.pdf` | Printable A4 fixture wall chart with empty score boxes + a leaderboard tally sheet. For the younger players. |
| `WorldCup-Groups.pdf` | Single printable A4 page: all 12 group tables with flag, team name, and owner. |

### Hosting
These are static files. To host: drag the HTML files onto https://drop.netlify.com, or push to a GitHub repo and enable GitHub Pages. If hosting the multi-page set together, the nav links between `worldcup-calendar.html` and `previews.html` need both files in the same folder. **Cookies are per-browser/per-device** — the standings only persist on the device that entered them, so the intended use is one person running the live page on a shared screen.

---

## The rules

- **21 family members**, €5 each = **€105 pot**.
- Every person drew **2 teams**; 6 lucky people drew a **3rd bonus team**. All 48 teams assigned, one owner each.
- Teams were tiered by FIFA ranking: Tier 1 = top 21, Tier 2 = next 21, Tier 3 = bottom 6 (the bonus teams).
- **Prizes:** 🥇 Winner €60 · 🥈 Runner-up €25 · 🥉 Third place €10 · 😬 Worst-performing team €10.
- This is family fun and **includes children** — keep all copy friendly and age-appropriate. No drinking references, nothing unsuitable for kids.

---

## The draw results (source of truth)

Each person, their teams, and the tier each team was drawn in (1 = top seed, 2 = mid, 3 = bonus):

```
Aisling    — England (1), Algeria (2)
Catherine  — Portugal (1), Iraq (2), New Zealand (3)
Cooper     — Ecuador (1), Canada (2)
Craig      — Germany (1), Saudi Arabia (2)
David      — Mexico (1), Panama (2)
Eimíle     — Colombia (1), Qatar (2)
Elsie      — Senegal (1), Norway (2)
Eric       — Iran (1), Scotland (2)
Evelyn     — Switzerland (1), Austria (2)
Geoff      — Spain (1), Ivory Coast (2), Haiti (3)
Jane       — France (1), South Africa (2), Bosnia & Hz. (3)
Julian     — Belgium (1), Sweden (2)
Leighanne  — Uruguay (1), Australia (2), Curaçao (3)
Matthew    — Argentina (1), Uzbekistan (2)
Oliver     — Brazil (1), Czechia (2)
Orlagh     — Morocco (1), DR Congo (2), Cape Verde (3)
Peter      — USA (1), Egypt (2)
Ruairí     — Japan (1), Tunisia (2)
Siobhan    — Turkey (1), Paraguay (2)
Sue        — Croatia (1), South Korea (2), Ghana (3)
Wes        — Netherlands (1), Jordan (2)
```

The 6 bonus (Tier 3) holders: Catherine, Geoff, Jane, Leighanne, Orlagh, Sue.

---

## The family tree (for preview banter — get relationships right!)

Relationships have been a recurring source of mistakes. Use this as the canonical reference. **Everyone in the draw knows each other**, so previews should NOT over-explain relationships — mention them only as a light touch where they land. Lead with football facts instead.

- **Evelyn (80)** is the matriarch. Her four children: **Geoff (60)**, **Siobhan (58)**, **Wes (55)**, **Leighanne (40)**.
- **Geoff** is married to **Catherine (62)**. Their children: **David (40)**, **Aisling (35)**, **Eimíle (31)**.
- **David** is married to **Jane (38)**. Their children: **Oliver (7)**, **Cooper (6)**. Jane's mother is **Orlagh (67)**.
- **Aisling** is married to **Eric (35)**. Their son: **Julian (2)**.
- **Siobhan** is married to **Peter (57)**. Their son: **Matthew (30)**.
- **Wes** is married to **Sue (52)**. No children.
- **Leighanne** is married to **Craig (45)**. Their children: **Elsie (11)**, **Ruairí (7)**.

Key relationship facts that have tripped previews up before:
- Siobhan is **Aisling's aunt** (Geoff's sister), so she's Eric's aunt-in-law and the kids' great-aunt.
- Orlagh is **Oliver and Cooper's maternal grandmother** (Jane's mum) — a real grandmother, not "grandmother-in-law".
- Wes is **Julian's great-uncle** (Geoff's brother → Aisling's uncle → Julian's great-uncle).
- Eric is **Catherine's son-in-law** (married to her daughter Aisling).
- Evelyn is great-grandmother to Oliver, Cooper and Julian.

**Football-mad** (lean into this in their previews): Peter, Wes, Oliver.
**Apprentice soccer mom** (learning the game, good comic material): Jane.

---

## Self-derbies (a person owns BOTH teams in a fixture — they can't lose)

- **Siobhan** — Turkey v Paraguay (Group D), 19 June
- **Ruairí** — Tunisia v Japan (Group F), 20 June (note: official fixture is Tunisia v Japan, listed in the calendar)
- **Elsie** — Norway v Senegal (Group I), 22 June
- **Sue** — Croatia v Ghana (Group L), 27 June — closes the group stage

---

## Fixture data (official, Irish time)

The calendar uses the official FIFA schedule with Irish (IST = UTC+1) kick-off times. Dates are the Irish calendar date the game is played on (overnight US kick-offs roll to the next Irish date). The authoritative fixture array lives in the `FIXTURES` const inside `worldcup-calendar.html`, and the same data is mirrored in the `GROUPS` object used by the standings section. **If you edit fixtures, update both, and keep the per-group fixture IDs (A1, A2 … L6) consistent.**

Group make-up:

```
A: Mexico, South Korea, South Africa, Czechia
B: Canada, Switzerland, Qatar, Bosnia & Hz.
C: Brazil, Morocco, Scotland, Haiti
D: USA, Australia, Paraguay, Turkey
E: Germany, Ecuador, Ivory Coast, Curaçao
F: Netherlands, Japan, Tunisia, Sweden
G: Belgium, Iran, Egypt, New Zealand
H: Spain, Uruguay, Saudi Arabia, Cape Verde
I: France, Senegal, Norway, Iraq
J: Argentina, Austria, Algeria, Jordan
K: Portugal, Colombia, DR Congo, Uzbekistan
L: England, Croatia, Ghana, Panama
```

Knockouts (Round of 32 onward, from 28 June) are not yet built — the bracket depends on group results. This is the main outstanding feature (see below).

---

## Conventions to follow

- **Vanilla only.** Inline `<style>` and `<script>` in each HTML file. No npm, no build, no external JS libraries beyond Google Fonts (Bebas Neue + Inter/Crimson Pro) loaded via `<link>`.
- **No browser localStorage/sessionStorage** if a file might run inside the Claude.ai artifact sandbox — these files use **cookies** for persistence, which work everywhere. Keep using cookies.
- **Flags** are plain emoji inline in the HTML pages. In the PDFs they are rendered to PNGs from the Noto Color Emoji font (see the PDF generation note below).
- **Colour palette:** dark green background (`#0d1a0e` / `#132015`), gold accents (`#d4a017` / `#f0c040`), cream text (`#f0ead8`). Tier 1 = gold, Tier 2 = green, Tier 3 = red/pink.
- **Tone:** warm, fun, family-friendly, football-literate. Real World Cup history and team facts are the backbone of the previews; family jokes are seasoning.
- Team name spelling must stay consistent across files: `Bosnia & Hz.`, `DR Congo`, `Ivory Coast`, `South Korea`, `Cape Verde`, `Curaçao`, `Czechia`, `Türkiye` is written as `Turkey` here.

---

## Outstanding / possible next tasks

1. **Knockout bracket** — build the Round of 32 → Final as group results come in. Fixture structure (match numbers 73–104) is in the official FIFA schedule. Each knockout slot is defined by group position (e.g. "Group A winner v Group B runner-up"), so it can be auto-populated once the standings section can compute final group tables.
2. **Auto-compute group tables** — the standings section currently sums each owner's points; extending it to produce real group standings (and therefore qualifiers) would feed the bracket.
3. **Sync preview dates to Irish dates** — the previews currently use FIFA's listed dates; the calendar uses Irish dates. Worth aligning so a WhatsApp preview matches when the family actually watches.
4. **Add kick-off times to previews** — the calendar has Irish kick-off times; the previews don't yet.
5. **Live score entry polish** — optional: a simpler mobile-friendly score entry flow, or a way to share the current standings as an image/text for WhatsApp.
6. **Proof-read all previews** against the family tree and the official fixture list before each matchday (relationship errors and date errors have both occurred).

---

## PDF generation (if you need to regenerate the printables)

The two PDFs were generated with Python + `reportlab`. Flags were rasterised from the system **Noto Color Emoji** font via Pillow (`ImageFont.truetype(... NotoColorEmoji.ttf, size=109)`, draw with `embedded_color=True`, crop to bbox, save as PNG, embed in the table). On macOS the equivalent emoji font is **Apple Color Emoji** (`/System/Library/Fonts/Apple Color Emoji.ttc`) — note Pillow can be fussy with `.ttc`; installing Noto Color Emoji via Homebrew (`brew install font-noto-color-emoji`) is the reliable path. Reproduce only if asked; the current PDFs are fine.

---

## Quick start for Claude Code

```
# from the project folder
open worldcup-calendar.html      # main page — calendar + standings
open previews.html               # WhatsApp match previews
```

Most likely first request: build the knockout bracket, or update something in the previews/calendar. Read the relevant HTML file fully before editing — each is self-contained, and the data (DRAW, FIXTURES/GROUPS, FLAGS, BANTER/PREVIEWS) is defined in JS consts near the bottom of each file.

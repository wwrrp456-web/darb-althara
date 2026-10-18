# برومت Codex لتوليد أصول الفن الجديدة

انسخ كل ما تحت الخط إلى Codex (ChatGPT) واربطه بالمستودع `wwrrp456-web/darb-althara`، ويفضّل أن يعمل على فرع `main`.

---

You are working in the GitHub repo wwrrp456-web/darb-althara (branch: main). It is a static, offline-capable Arabic RTL browser board game "درب الثراء" (no build step; opens from file:// and via GitHub Pages). Your job is ART + minimal art wiring ONLY. Do NOT change game rules, numbers, state/save format, or any gameplay function in index.html.

## Style (must match exactly)
Match the existing sheets art/identity/icons-sheet.png (6x6) and art/identity/cards-sheet.png (3x3): warm 2D cartoon, thick dark-brown outlines (~#423329), soft shading, emerald / gold / coral / blue accents, ivory background (#fffaf0-like). NO text or letters inside any image (Arabic text stays in HTML). Icons must stay readable at 24 px: bold silhouette, one clear idea, centered with padding. Use your image-generation tool to produce the sheets (do not hand-draw SVG); regenerate a cell if it is off-style. Read art/README.md and styles/identity.css + styles/illustrated.css first to see how cells are positioned (background-position percentages), and scripts/identity.js (icons array, emoji groups, `families` map of decision-card art).

## Deliverables
1) art/identity/icons-extra-sheet.png — 5 columns x 3 rows = 15 icons, order left-to-right then top-to-bottom (file order, independent of RTL):
 1 investor (well-dressed investor figure holding a coin, small upward arrow; must look different from the red briefcase icon)
 2 tax audit (magnifying glass over a receipt/ledger)
 3 jail (small cell-bars window with a padlock)
 4 upgrade (small building with a crane and an up-arrow)
 5 bankruptcy (torn red-stamped ledger or empty wallet)
 6 jail-exit (open padlock + key)
 7 rat-race (cute running rat)
 8 fast-track (rocket)
 9 mood-great  10 mood-good  11 mood-neutral  12 mood-worried  13 mood-exhausted (round faces, same family as the existing "smile" icon, clearly distinguishable at 24 px)
 14 two-dice (two white dice)
 15 menu/more (replace the current stacked colored bars icon with a clear rounded hamburger/"more" button look)
2) art/identity/cards-extra-sheet.png — 2x2 scenes, same size/style/framing as cards-sheet.png cells: investor offer (investor handing a deal, coins), tax audit (inspector with magnifier and ledger, friendly not scary), jail/fine (cell bars with a character paying a fine), bankruptcy (character with empty pockets, closed shop, hopeful tone). Keep the multicultural, warm tone of the existing characters.
3) Optional, only if time allows: art/identity/jail-bars.png (transparent overlay that fits over a pawn from art/identity/pawns-sheet.png) and art/identity/landmark-levels-sheet.png (3x1 small badges: level 1/2/3 gold star + building tier).

## Wiring (minimal, art-only)
- scripts/identity.js: add the new icon names after the existing ones WITHOUT changing the index of existing icons (existing positions in icons-sheet.png stay as they are); map emoji -> new icons: 💹 (use this emoji for investor in index.html TILE "market" and the investor offer title), 🕵 -> audit (remove it from the "person" group), 🚔 -> jail, 🏗 -> upgrade (remove from "building"), 🐀 -> rat-race and 🚀 -> fast-track (remove 🐀 from "smile"; keep avatar handling for 🚀 as an avatar untouched — avatars are matched via avatarValues before icons), the five mood emojis used by hapState() in index.html -> mood-great..mood-exhausted, ☰ -> menu/more. If a new emoji must be introduced in index.html, change only the displayed emoji string, never logic.
- styles/illustrated.css (or a new styles/extra-icons.css linked after it): CSS for the 5x3 extra sheet using the same technique as the existing 6x6 icons (background-size 500% 300%, positions in % per cell, same .ui-icon / .illustrated-icon classes). For cards: extend `families` entries `market`, `audit`, `jail` (and add `bankrupt` if the game shows a bankruptcy card — see bankrupt() in index.html, it currently uses ack) so they use cards-extra-sheet.png cells; keep the 3x3 mapping for all other kinds.
- sw.js: add every new file to SHELL, bump VER (e.g. darb-light-illustrated-v11) and the ?v= query strings in index.html.
- art/README.md: document the new sheets, order and positions.
- Keep each PNG under ~2.5 MB (optimize), keep file:// working (no external fonts/CDNs).

## Verify and ship
- Run tools/verify_identity.py, tools/verify_cards.py, tools/verify_tabletop.py, tools/verify_upgrade.py (serve with `python3 -m http.server`; Playwright is available).
- Take screenshots at 390x844 and 1180x820 of: board with an investor tile, audit prompt, jail prompt (set p.jail=2 via window.__darb.G.players[0].jail=2 then roll), happiness bar for each mood, top-bar menu button, roll button with two dice. Confirm no clipped/blurry icons and no layout shifts.
- Commit with a clear message and push to main (no pull request). Report which files changed.

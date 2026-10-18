# مهام Codex لدرب الثراء (ملف واحد)

> للمستخدم: افتح Codex واكتب له فقط:
> **«اقرأ الملف docs/CODEX_TASKS.md في مستودع wwrrp456-web/darb-althara (فرع main) ونفّذ مراحله بالترتيب، واعمل commit بعد كل مرحلة وارفع إلى main بلا Pull Request.»**
> المراحل مستقلة: لو انتهى حدّ Codex في المنتصف تبقى المراحل المنجزة سليمة ومرفوعة، ويكمل لاحقاً من المرحلة التالية.

---

You are working in the GitHub repo `wwrrp456-web/darb-althara` (branch `main`): a static, offline-capable Arabic RTL browser board game "درب الثراء" (no build step; must work from `file://` and GitHub Pages). Read `art/README.md`, `index.html` (tabletop render near `window.DarbTabletop.paint`, the read-only `inspect` descriptions near "Read-only descriptions"), `scripts/tabletop.js`, `scripts/board-camera.js`, `scripts/identity.js`, `styles/tabletop.css`, `styles/illustrated.css` before starting.

## Global rules (apply to every phase)
- ART + presentation wiring ONLY. Never change game rules, numbers, state/save format, or gameplay functions. Inspection is READ-ONLY: it must never buy, move, answer or change state.
- Style = the existing identity: warm 2D cartoon, thick dark-brown outlines (~#423329), soft shading, emerald/gold/coral/blue accents, ivory background. NO text or letters inside any image (Arabic text stays in HTML).
- Generate images with your image-generation tool (do not hand-draw SVG); regenerate any cell that is off-style.
- **Performance is a hard requirement.** History: commit `5e8628c` added "interactive solid miniatures" and `8206b58` REMOVED them as "heavy miniature rendering". Do NOT repeat that. Forbidden: WebGL/three.js/canvas 3D, real 3D models, per-frame JavaScript, large stacks of CSS filters/box-shadows per piece, many live `preserve-3d` layers. Required: pre-rendered transparent PNG/WebP sprites that LOOK like small 3D miniatures (3/4 isometric view, a little thickness, soft contact shadow), placed and "stood up" with the same cheap technique the pawns already use (`.pawn-stand` counter-rotates against the table tilt). Each sprite sheet <= ~600 KB, all new art together <= ~2.5 MB. Target >= 50 fps on a mid phone (Playwright mobile emulation + CPU throttle 4x is acceptable evidence).
- Keep `file://` working (no external fonts/CDNs). Add every new asset to `sw.js` SHELL, bump `VER` and the `?v=` query strings, document the new sheets (order, grid, positions) in `art/README.md`.
- Verify with `tools/verify_*.py` (serve with `python3 -m http.server`; Playwright is available) plus screenshots at 390x844 and 1180x820. Commit after each phase with a clear message and `git push origin main` (no pull request).

## PHASE 1 — new icons (icons-extra-sheet) and PHASE 2 — new decision cards
### Style details
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


### Wiring for phases 1-2 (minimal, art-only)

- scripts/identity.js: add the new icon names after the existing ones WITHOUT changing the index of existing icons (existing positions in icons-sheet.png stay as they are); map emoji -> new icons: 💹 (use this emoji for investor in index.html TILE "market" and the investor offer title), 🕵 -> audit (remove it from the "person" group), 🚔 -> jail, 🏗 -> upgrade (remove from "building"), 🐀 -> rat-race and 🚀 -> fast-track (remove 🐀 from "smile"; keep avatar handling for 🚀 as an avatar untouched — avatars are matched via avatarValues before icons), the five mood emojis used by hapState() in index.html -> mood-great..mood-exhausted, ☰ -> menu/more. If a new emoji must be introduced in index.html, change only the displayed emoji string, never logic.
- styles/illustrated.css (or a new styles/extra-icons.css linked after it): CSS for the 5x3 extra sheet using the same technique as the existing 6x6 icons (background-size 500% 300%, positions in % per cell, same .ui-icon / .illustrated-icon classes). For cards: extend `families` entries `market`, `audit`, `jail` (and add `bankrupt` if the game shows a bankruptcy card — see bankrupt() in index.html, it currently uses ack) so they use cards-extra-sheet.png cells; keep the 3x3 mapping for all other kinds.
- sw.js: add every new file to SHELL, bump VER (e.g. darb-light-illustrated-v11) and the ?v= query strings in index.html.
- art/README.md: document the new sheets, order and positions.
- Keep each PNG under ~2.5 MB (optimize), keep file:// working (no external fonts/CDNs).


## PHASE 3 — 3D-looking miniatures: landmark buildings and the card decks on the table
Goal: the landmark buildings on the board, and the card decks on the table, keep the SAME illustrated drawing style of the current art, but look like small physical miniatures standing on the table (volume, thickness, soft shadow) — achieved with pre-rendered sprites, not real 3D.

3a) Landmark buildings — `art/identity/landmarks-sheet.png`, 4 columns x 2 rows, transparent background, file order left-to-right then top-to-bottom:
 1 cafe (مقهى الحي)  2 mall (مول الحي)  3 university (جامعة)  4 hospital (مستشفى خاص)
 5 hotel (فندق)  6 bank (بنك)  7 tower (برج الأعمال, taller/glassy)  8 airport (مطار, small terminal + plane)
 Each: one building as a miniature model on a small round/rounded base, 3/4 isometric view lit from the top-left, soft contact shadow baked in, readable at ~56 px wide and crisp at ~140 px (draw each cell at least 512x512). Consistent scale and viewing angle across all 8. No text on signs.
 Level markers — `art/identity/landmark-levels-sheet.png`, 3 columns x 1 row, transparent: small overlay pieces for upgrade levels 1/2/3 (gold flag, extra rooftop floor + banner, golden crown/spire), meant to be placed on top of any building. Game levels: `G.lmLv[key]` (0 = none, max 3; in the rat race only level 1 is allowed, 2-3 only in the fast track).
 Wiring: render a landmark tile as a standing sprite (same technique as `.pawn-stand`) instead of the flat icon, sized to the tile, with: an owner ring/marker in the owner's colour (`G.lm[key]` = owner player id) and the level overlay for `G.lmLv[key]`. Keep the flat icon as fallback if the image fails. Tile keys are `lm_cafe, lm_mall, lm_uni, lm_hospital, lm_hotel, lm_bank, lm_tower, lm_airport` (see `LAND` in index.html). Do not let sprites hide pawns: pawns keep a higher z-order.

3b) Card decks on the table — `art/identity/decks-sheet.png`, 3 columns x 1 row, transparent: a miniature stack of cards with visible thickness (slightly fanned top card, edge layers) for: family surprises (coral/pink), financial questions (teal), and a neutral third deck for decisions/offers (gold). Same 3/4 view and shadow as the buildings. Replace the current flat CSS `.tabletop-deck` look with these sprites while keeping the same positions/sizes and the existing labels in HTML.

## PHASE 4 — tap/click shows the data (inspection)
The camera already has a read-only inspector dialog: `#board-inspector` in index.html, opened by `scripts/board-camera.js` through `options.inspect(reference)` which returns `{title, subtitle, description, color, icon, details:[[label,value],...]}`. Extend it (do not build a new dialog):
- Tapping/clicking a landmark miniature (or its tile) shows: name, perk description (`LAND[key].d`), purchase price (`LAND[key].cost`) and down payment, base income and CURRENT income including upgrade (`LAND[key].inc` + upgrade; read the owner's asset), CURRENT visitor rent (`lmRent(key)` from `LAND[key].rent` and the level multipliers 1/1.4/1.9/2.5), current level and the cost of the next upgrade (`lmUpCost(key)`), the owner's name/avatar or "available for purchase". Use the existing numbers from game state; format with the existing `fmt()`.
- Tapping a deck shows: deck name, what kind of cards it holds, how many cards remain/used if the game tracks it (families/question decks `FDECK`/`QDECK` in index.html — expose a read-only getter, do not mutate), and one sentence on how it is triggered.
- Tapping a pawn already works or may be added the same way (name, profession, cash, passive income, jail status `p.jail`).
- Make tap targets >= 44 px even when the sprite is small (invisible padding), support keyboard (Enter/Space) and close with the existing close buttons. Dragging/pinching the camera must NOT open the inspector (only a clean tap does — check the existing drag threshold in board-camera.js).
- Add `aria-label` in Arabic to each interactive miniature.

## Acceptance checklist
- 8-player game, 2-player game, mobile (390x844) and iPad landscape (1180x820): buildings and decks visible, no overlap with pawns, no horizontal scroll, owner ring + level overlay correct after upgrading a landmark (use `window.__darb.upgradeLm(playerId,'hospital')` after giving cash).
- Inspector opens from landmark, deck and tile with correct live numbers, and never changes game state.
- No console errors; `file://` and `http` both work; offline cache includes the new files.
- Report: files changed, sheet sizes, measured fps/CPU before vs after.

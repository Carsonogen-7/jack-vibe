# Project notes for Claude Code

## What this is
A personal side project: a scoring formula ("Jack Vibe Score") tailored to Carson's friend Jack, an amateur food critic. Step one is this intake quiz, which collects Jack's stated priorities (sliders), forced-choice tradeoffs, and ratings of 7 made-up dishes with known category profiles. Later steps: fit weights from his ratings, then build a calculator Jack uses for real reviews and refine the weights as reviews accumulate.

## Design decisions to keep
- **Food first.** Score = food (8 categories) + restaurant (service, ambiance, speed, value). Jack sets the restaurant share, 0–40%, default 20%.
- **Stated vs revealed weights.** Sliders give stated weights. Dish ratings give revealed weights via regression against the `MEALS` profiles. Comparing the two is a feature, not a bug.
- **Quirks beyond a weighted average:** dealbreakers cap the score, price stance decides whether value is relative to cost.
- **Results travel as a text code** (`JACKVIBE2.` + base64 JSON), sent through the share sheet. No backend. If you change the payload shape, bump the version prefix and update `tools/decode.py`.

## Constraints
- Static site, no build step, single `index.html`. Keep it that way unless there's a reason.
- Must work well on iPhone Safari and as a home-screen app: safe-area insets, no horizontal scroll at 390px, tap targets ≥ 34px.
- Light and dark themes via CSS tokens on `:root`. Add colors as tokens, not literals.
- Answers persist in `localStorage` under `jack-palate-quiz-v2`, wrapped in try/catch.
- Bump `VERSION` in `sw.js` whenever `index.html` changes.

## Testing
`python3 -m http.server 8000`, then click through on desktop and at phone width. Generate a code and run it through `tools/decode.py` to confirm the round trip.

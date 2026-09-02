# TopBet × Sweet Bonanza — Landing Page

Interactive casino LP: the player hunts a 24-cell candy grid for **three copies
of one specific tile** — the 200%/150FS golden bomb — then lands on a bonus
reveal + TopBet registration form.

## The mechanic

- The player gets a **random 4–7 taps** per page load (`ATTEMPTS_MIN`/`MAX`).
- Only the bomb counts. Every other tile is a losing candy that stays face-up,
  desaturated, and cannot be tapped again.
- The round is **rigged to win**: the outcome of a tap is decided by *which tap
  it is*, not by what was seeded under that cell. Three of the allotted taps
  reveal a bomb and **the last tap is always the third bomb**, so the round ends
  on the win instead of fizzling out with taps to spare.
- One prize, no tiers: `200% Bonus + 150 Free Spins`.

Because nothing is pre-placed, the board can never be read ahead by inspecting
the DOM. See `newRound()` and `pick()` in `index.html`.

Everything ships as a single `index.html` — no framework, no bundler, and **no
external requests at runtime** (fonts and images are all local).

## Run it

```sh
python -m http.server 8123
# then open http://127.0.0.1:8123/index.html
```

Opening the file directly with `file://` also works.

## Sources

| Source | What it gave us |
|---|---|
| `CLAUDE-sweet-bonanza.md` | the original pick-a-cell brief, screen flow, animation list |
| Figma `mAJyDSaXdr9GO72b7FGvI8` node `3:559` | brand palette (Graphite `#22252A`, Signal Red, White, Black) |
| Figma node `3:1756` | typeface: **FiraGO** (light / semibold / heavy) |
| Figma node `3:2176` | the **Registration Form** component set — 22 Device × Tab × State variants |
| `assets/Symbols`, `assets/Gameart`, `assets/` | Pragmatic Play *Sweet Bonanza* art |

The registration card is built against `3:2828` (desktop, Bonus Open),
`3:2387` (mobile, Bonus Open), `3:2214` (error) and `3:2581` (success).

## Assets

`assets/Symbols/`, `assets/Gameart/` and `assets/Animations/` are the untouched
~333 MB originals and are **never referenced by the page**. Everything the page
loads is generated into `assets/web/` and `assets/fonts/`:

```sh
python scripts/build-assets.py
```

Needs `Pillow`, `fontTools` and `brotli`. The script is idempotent — it wipes and
rebuilds both output trees, prints a size report, and fails if the result
exceeds 600 KB. Current total: **~455 KB**.

It also composes `assets/web/og-image.jpg` (1200×630) for link previews, from
the same key visual the page uses. Pillow needs a real sfnt to draw text, so the
script strips the woff2 wrapper off FiraGO with fontTools on the fly. The card
carries the game logo, the offer and the winning tile but **not** the TopBet
wordmark — Pillow cannot rasterise SVG and there is no PNG of the mark in the
repo; the brand rides along in `og:title` / `og:site_name`.

Three things it deliberately skips:

- `assets/Animations/*.gif` — hard white (or black) matte, no transparency; they
  would render as white squares on the dark grid. The win "pop" is CSS.
- `assets/Gameart/*` UI layers (reel, frame, buy-feature, buttons) — full
  3554×1998 canvases that are ~95 % white plate.
- `assets/SWEET BONANZA_*.svg` — SVGator wrappers around base64 rasters whose
  layers start at `scale(0,0)` and only appear via CSS keyframes.

Fonts: fontsource's FiraGO "latin" files are mislabelled — each carries the full
2519-codepoint set at ~250 KB, so five weights would be 1.25 MB. The build
subsets them to the characters the page renders: **51 KB for all five**.

## Configuration

Every campaign-specific value is in the `CONFIG` object at the top of the
`<script>` block, and every user-facing string is in `COPY` beside it:

```js
BONUS_PCT: 200, MAX_BONUS: '1 000 000 UZS', FREE_SPINS: 150, FREEBET: '55 000 UZS'
TOTAL_CELLS: 24, BOMBS_TO_FIND: 3, ATTEMPTS_MIN: 4, ATTEMPTS_MAX: 7
DEMO_MODE: true, REGISTER_URL: 'https://example.com/register'
```

`DEMO_MODE: true` (current) shows the Figma "Registration Successful!" panel and
makes no network call. Set it to `false` and submit redirects to `REGISTER_URL`.

Set `ATTEMPTS_MIN === ATTEMPTS_MAX` for a fixed round length. `ATTEMPTS_MIN` must
stay `>= BOMBS_TO_FIND` — with fewer taps than bombs the round could never
complete, so `newRound()` clamps it and warns rather than hanging the grid.
`ATTEMPTS_MIN === BOMBS_TO_FIND` is legal and means every tap is a win.

## Deviations from the Figma component

All intentional — worth raising with the designer:

1. **Unfinished placeholders replaced.** The component ships `or up to (Сумма) +
   150 FS` and a literally truncated `Welcome Freebet 55 0...`. These now come
   from `CONFIG`. (FiraGO's fontsource build is latin-only, so the Cyrillic
   `(Сумма)` had no glyphs either.)
2. **Bonus emoji un-swapped.** Figma has 🎰 on *Sport Bonus* and ⚽ on *Casino
   Bonus*; the page uses ⚽ Sport / 🎰 Casino.
3. **FiraGO throughout.** The component itself uses Fira Sans + Roboto; the brand
   guide specifies FiraGO. Expect ~1–2 px optical drift vs the Figma renders.
4. **Focus / hover states invented** — none are defined in the design.
5. **Dropdown-open fill** uses the desktop `#202329` at both breakpoints; the
   mobile variant's `#12151c` makes open and closed look identical.
6. **US flag is drawn as inline SVG**, not the 🇺🇸 emoji — Windows ships no flag
   glyphs and renders the emoji as the letters "US".
7. The hardcoded `+1` country code is kept as designed; a real country picker is
   out of scope.

## Responsive

| Width | Grid | Controls | Card |
|---|---|---|---|
| < 768 px | 4 × 6, cells 75–89 px | 44 px | 350 px translucent panel, promo above it |
| ≥ 768 px | 6 × 4, cells ~110 px | 54 px | 500 px opaque card, promo inside |

The Sweet Bonanza lockup swaps with a `<picture>`: the two-line portrait art
below 600 px, the wide one-line version above it — the landscape version turns
into unreadable ribbon at phone widths.

Verified at 375 / 430 / 768 / 1440 with no horizontal overflow in any screen
state. `prefers-reduced-motion` disables the float, flip and confetti.

## Before it goes live

1. **Four placeholder URLs** — `example.com` on Terms of Service, Privacy Policy,
   "Log in" (in the markup) and `REGISTER_URL` (in `CONFIG`).
2. **`DEMO_MODE: true`** — flip to `false` once there is a real destination.
3. **`og:image` / `twitter:image` are relative.** Fine for Telegram, WhatsApp and
   local preview; Facebook and X need absolute URLs, so prefix them with the
   campaign domain at deploy.
4. **Phone field is hardcoded to 🇺🇸 `+1`** with a `201 555 0199` placeholder,
   exactly as the Figma component specifies — inconsistent with a UZS offer,
   which likely wants `+998`. Design decision, not a build one.
5. **No sounds.** The original brief lists `pick.mp3` / `scatter.mp3` / `win.mp3`;
   no audio exists in the repo.
6. **No analytics or conversion pixel** — none was requested.

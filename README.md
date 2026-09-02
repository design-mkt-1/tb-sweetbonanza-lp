# TopBet × Sweet Bonanza — Landing Page

Interactive casino LP: the player hunts a 12-tile candy grid for **three copies
of one specific tile** — the 200%/150FS golden bomb — then lands on a bonus
reveal + TopBet registration form. It fits a phone screen without scrolling.

## The mechanic

- The board is **12 tiles** (4 × 3) and the player gets a **random 3–5 taps** per
  page load (`ATTEMPTS_MIN`/`MAX`).
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

Deployed from `main` / root to GitHub Pages:
**https://design-mkt-1.github.io/tb-sweetbonanza-lp/**

The repo is private but a Pages site is public unless the account is on GitHub
Enterprise. Only `index.html`, `assets/web/**` and `assets/fonts/**` are served
as real files -- the ~280 MB of raw Pragmatic Play art is LFS-tracked, and Pages
does not resolve LFS, so those paths return 132-byte pointer files.

## Sources

| Source | What it gave us |
|---|---|
| `CLAUDE-sweet-bonanza.md` | the original pick-a-cell brief, screen flow, animation list |
| Figma `mAJyDSaXdr9GO72b7FGvI8` node `3:559` | brand palette (Graphite `#22252A`, Signal Red, White, Black) |
| Figma node `3:1756` | typeface: **FiraGO** (light / semibold / heavy) |
| Figma node `3:2176` | the **Registration Form** component set — 22 Device × Tab × State variants |
| `assets/Symbols`, `assets/Gameart`, `assets/` | Pragmatic Play *Sweet Bonanza* art |
| `assets/audio/_src` | five SFX generated with ElevenLabs (flip, bomb, win, error, success) |

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
exceeds 600 KB. Current total: **~554 KB**.

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

Sound: five SFX generated with ElevenLabs, kept in `assets/audio/_src/` and
published to `assets/web/audio/` by `build_audio()`. They are already web-sized
MP3s, so the build step is a copy — but it has to be a build step regardless,
because `main()` wipes `assets/web/` and anything dropped there by hand would not
survive the next run. **~146 KB for all five.** There is no `bomb-2`/`bomb-3`:
the three bombs replay one clip at `playbackRate` 1.0 / 1.13 / 1.26, which is the
escalating-reward effect for the price of one file.

The page plays them through `<audio>` elements, **not** Web Audio, and the reason
is iOS: the hardware Ring/Silent switch mutes an `AudioContext` outright, because
iOS files Web Audio under "ambient". `HTMLMediaElement` gets the "playback"
category and plays through the switch, the same way video does in Safari. Built
on Web Audio first, this feature was inaudible on every iPhone not already off
silent — which is most of them, on a page opened from an ad. The sibling
`fs-penalty` LP reached the same design for the same reason.

The trade is real: **iOS treats `HTMLMediaElement.volume` as read-only**, so
`SFX_GAIN` shapes the mix everywhere except the platform this was rewritten for.
A clip that is wrong on iPhone has to be fixed in the file, not in the code.

Three voices per sound, all primed inside the first gesture — iOS grants playback
per element, not per page, so cloning an unprimed element at tap time and hoping
it inherits the permission is not safe. Round-robin across the voices means a
retrigger takes a free element instead of cutting the previous one off. Unlock
listens on `pointerdown`, `touchend`, `click` and `keydown` so no single browser's
idea of activation is a single point of failure. Anything that can fail — a 404
on a clip, a refused `play()`, `localStorage` throwing in private mode — leaves
`playSfx` a silent no-op; no game state reads it.

Sound is on by default, muted for `prefers-reduced-motion` (the audience that
already has the confetti switched off), and the toggle in the masthead persists
to `localStorage` under `tb-sfx-muted`.

Fonts: fontsource's FiraGO "latin" files are mislabelled — each carries the full
2519-codepoint set at ~250 KB, so five weights would be 1.25 MB. The build
subsets them to the characters the page renders: **51 KB for all five**.

## Configuration

Every campaign-specific value is in the `CONFIG` object at the top of the
`<script>` block, and every user-facing string is in `COPY` beside it:

```js
BONUS_PCT: 200, MAX_BONUS: '1 000 000 UZS', FREE_SPINS: 150, FREEBET: '55 000 UZS'
TOTAL_CELLS: 12, BOMBS_TO_FIND: 3, ATTEMPTS_MIN: 3, ATTEMPTS_MAX: 5
DEMO_MODE: true, REGISTER_URL: 'https://example.com/register'
```

`DEMO_MODE: true` (current) shows the Figma "Registration Successful!" panel and
makes no network call. Set it to `false` and submit redirects to `REGISTER_URL`.

Set `ATTEMPTS_MIN === ATTEMPTS_MAX` for a fixed round length.
`ATTEMPTS_MIN === BOMBS_TO_FIND` is legal and means every tap is a win.

Two ways a config edit could make the round unwinnable, both clamped in
`newRound()` with a console warning rather than left to hang the grid:

- **fewer taps than bombs** — the third bomb never lands;
- **more taps than cells** — every tile ends up disabled with no win.

Neither can end the round: every tap disables a tile and the only exit is
`bombsFound >= BOMBS_TO_FIND`. There is no "out of taps" branch.

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
8. **The promo lockup is hidden inside the card below 768 px.** It repeats what
   the reveal block states directly above it, and it is 100 px the phone
   viewport cannot spare. Desktop keeps it, faithful to `3:2828`.
9. **The bonus dropdown overlays instead of expanding in-flow.** In the Figma
   component it is an in-flow block, which pushed the page down 147 px and
   forced a scroll the moment it was opened.

## Responsive

**The page does not scroll.** Every screen — the grid, the form (open dropdown
included) and the success panel — fits the viewport.

| Width | Grid | Controls | Card |
|---|---|---|---|
| < 768 px | 4 × 3, cells ~83–94 px | 44 px | 350 px translucent panel, no promo lockup |
| ≥ 768 px | 4 × 3, cells ~131 px | 54 px | 500 px opaque card, promo lockup inside |

The grid is sized by `fitGrid()` against whichever runs out first, width or
leftover height. **CSS container queries look like the right tool and are not**:
`100cqh` resolves to `0` when the container's block size comes from flex
distribution, which is exactly this layout — measured, not assumed. Cells stop
shrinking at 44 px; below that the page is allowed to scroll rather than become
untappable. `fitGrid` re-runs from a `ResizeObserver`, `resize`,
`orientationchange` and `document.fonts.ready` (the font swapping in changes the
hero height after first paint).

`body` uses `min-height: 100svh`, not `dvh` — `dvh` grows when the mobile browser
chrome auto-hides, so a layout that fits `dvh` still scrolls while the chrome is
showing.

Verified at 390×640, 390×690, 430×760 and 1440×900 with zero vertical or
horizontal overflow in every screen state. `prefers-reduced-motion` disables the
float, flip and confetti.

## Before it goes live

1. **Four placeholder URLs** — `example.com` on Terms of Service, Privacy Policy,
   "Log in" (in the markup) and `REGISTER_URL` (in `CONFIG`).
2. **`DEMO_MODE: true`** — flip to `false` once there is a real destination.
3. **`og:url` and the two image URLs are absolute to the GitHub Pages
   deployment.** Repoint them when the LP moves to the campaign domain.
4. **`<meta name="robots" content="noindex, nofollow">`** — correct for a review
   link, must come out before a real campaign launch.
5. **Phone field is hardcoded to 🇺🇸 `+1`** with a `201 555 0199` placeholder,
   exactly as the Figma component specifies — inconsistent with a UZS offer,
   which likely wants `+998`. Design decision, not a build one.
6. **No sounds.** The original brief lists `pick.mp3` / `scatter.mp3` / `win.mp3`;
   no audio exists in the repo.
7. **No analytics or conversion pixel** — none was requested.

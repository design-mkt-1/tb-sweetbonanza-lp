# LP — Sweet Bonanza: Găsește 3 scatter-uri și câștigă Free Spins

## Overview
Landing page interactiv de tip casino, inspirat din jocul Sweet Bonanza (Pragmatic Play).
Mechanic: userul alege 3 câmpuri dintr-o grilă de bomboane — caută scatter-uri (⭐).
Oricare ar fi rezultatul, userul câștigă un bonus (mai mic sau mai mare — winner framing mereu).
Flow: 1 interacțiune (3 tap-uri) → reveal → înregistrare.

---

## Stack
- HTML + CSS + Vanilla JS (un singur fișier `index.html`)
- Fără framework, fără bundler
- Mobile-first, responsive (375px → 1440px)
- Animații: CSS keyframes + JS pentru flip/reveal per câmp

---

## File structure
```
/
├── index.html
├── assets/
│   ├── img/
│   │   ├── logo.svg
│   │   ├── bg-bonanza.jpg        # background colorat, candy world
│   │   ├── character.png         # personaj bomboane (optional, desktop)
│   │   └── candies/
│   │       ├── strawberry.png
│   │       ├── blueberry.png
│   │       ├── apple.png
│   │       ├── lemon.png
│   │       ├── candy.png
│   │       ├── watermelon.png
│   │       ├── grape.png
│   │       └── scatter.png       # ⭐ scatter simbol
│   └── sounds/
│       ├── pick.mp3              # sunet la flip câmp
│       ├── scatter.mp3           # sunet special la găsit scatter
│       └── win.mp3
```

---

## Screens

### Screen 1 — Interacțiunea (Pick Grid)

**Layout:**
- Background: colorat, candy world (roz/violet/galben)
- Logo brand centrat sus
- Headline: `"Găsește 3 scatter-uri și câștigă Free Spins!"` — bold, alb cu text-shadow
- Sub: `"Alege 3 câmpuri din grilă"` — mic, alb/muted
- Counter vizibil: `"0 / 3 selectate"` — se updatează la fiecare tap

**Grid de bomboane:**
- 4 rânduri × 6 coloane = 24 câmpuri
- Fiecare câmp: card cu spatele (design neutru, semn "?") — la tap face flip 3D și arată conținutul
- Spatele câmpului: gradient roz/violet cu `?` alb
- Față câmpului: candy image sau scatter image
- Scatter-urile: 4 din 24 câmpuri (pozitii random la fiecare load)
- Câmpurile selectate nu mai pot fi re-selectate

**Comportament selecție:**
- Tap 1: flip câmp 1, counter → "1 / 3"
- Tap 2: flip câmp 2, counter → "2 / 3"
- Tap 3: flip câmp 3, counter → "3 / 3" → trigger automat tranziție spre Screen 2 (600ms delay)
- Nu există buton de confirm — al 3-lea tap declanșează automat reveal

**Outcome logic (totul e win):**
- 0 scatter din 3 selectate → bonus mic: `50 Free Spins + 100 RON`
- 1 scatter din 3 selectate → bonus mediu: `100 Free Spins + 250 RON`
- 2 scatter din 3 selectate → bonus mare: `150 Free Spins + 500 RON`
- 3 scatter din 3 selectate → bonus maxim: `200 Free Spins + 1000 RON` (imposibil, dar păstrat în code)
- În practică: valorile bonus sunt configurabile din CONFIG

---

### Screen 2 — Bonus Reveal + Reg Form

**Tranziție:** scale-up + fade din centrul gridului

**Layout:**
- Același background
- Animație: confetti colorat (CSS, particule roz/galben/verde)
- Scatter-counter vizibil: `"⭐ X scatter-uri găsite!"`
- Bonus reveal: `"Ai câștigat 150 Free Spins + 500 RON Bonus!"`
- Sub-text: `"Înregistrează-te pentru a revendica"`

**Reg Form:**
- Câmp: Număr de telefon (type=tel)
- Câmp: Parolă (type=password)
- Dropdown: Selectează bonus
- Buton CTA: `"Revendică bonusul →"` — roz (#D4537E), full-width
- Link: `"Ai deja cont? Conectează-te"`

**Form behavior:**
- Validare basic: telefon ≥ 8 cifre, parolă ≥ 6 caractere
- Submit → redirect la REGISTER_URL

---

## Visual style

| Token | Valoare |
|-------|---------|
| Background | `#1a0a2e` (fallback) |
| Accent primary | `#D4537E` (roz Sweet Bonanza) |
| Accent secondary | `#F5C842` (galben bomboane) |
| Accent tertiary | `#7B3FBE` (violet) |
| Text primary | `#FFFFFF` |
| Text muted | `rgba(255,255,255,0.6)` |
| Card back bg | `linear-gradient(135deg, #9B3FBE, #D4537E)` |
| Card back text | `#FFFFFF` |
| Card front bg | `#FFFFFF` |
| Card scatter bg | `#FFF8E7` |
| Card scatter border | `2px solid #F5C842` |
| Card selected overlay | `rgba(212, 83, 126, 0.15)` |
| Button bg | `#D4537E` |
| Button text | `#FFFFFF` |
| Input bg | `rgba(255,255,255,0.1)` |
| Input border | `rgba(255,255,255,0.2)` |
| Border radius buttons | `50px` |
| Border radius cards | `10px` |

---

## Animations

| Animație | Descriere |
|----------|-----------|
| `cardFloat` | Toate câmpurile flotează ușor (up/down, staggered delay) înainte de selecție |
| `cardFlip` | Flip 3D pe axa Y la tap (300ms, CSS perspective) |
| `scatterPop` | La găsit scatter: scale 1 → 1.3 → 1 + glow galben (100ms) |
| `counterBounce` | Counter-ul sare la fiecare selecție |
| `revealExpand` | Screen 2 expand din centru (scale 0.8 → 1 + fade, 400ms) |
| `confetti` | ~30 particule colorate explodează la reveal |
| `bonusPulse` | Textul bonusului pulsează ușor |

---

## Config variables

```js
const CONFIG = {
  REGISTER_URL: 'https://example.com/register',
  TOTAL_CELLS: 24,
  SCATTER_COUNT: 4,       // câte scatter-uri sunt ascunse în grilă
  PICKS_ALLOWED: 3,       // câte câmpuri poate alege userul
  BONUS_TIERS: [
    { scatters: 0, label: '50 Free Spins + 100 RON Bonus' },
    { scatters: 1, label: '100 Free Spins + 250 RON Bonus' },
    { scatters: 2, label: '150 Free Spins + 500 RON Bonus' },
    { scatters: 3, label: '200 Free Spins + 1,000 RON Bonus' },
  ],
  BRAND_NAME: 'WinBoss',
  LANG: 'ro',
};
```

---

## Copy (RO)

| Element | Text |
|---------|------|
| Headline | Găsește 3 scatter-uri și câștigă Free Spins! |
| Sub-headline | Alege 3 câmpuri din grilă |
| Counter | {n} / 3 selectate |
| Scatter found | ⭐ Scatter găsit! |
| Reveal title | Felicitări! |
| Reveal scatter count | ⭐ {n} scatter-uri găsite |
| Reveal bonus | {label bonus din tier} |
| Reveal sub | Înregistrează-te acum pentru a revendica |
| Form phone | Număr de telefon |
| Form password | Parolă |
| Form CTA | Revendică bonusul → |
| Form login link | Ai deja cont? Conectează-te |
| Disclaimer | 18+ \| Joacă responsabil \| T&C se aplică |

---

## Responsive breakpoints

| Breakpoint | Comportament |
|------------|-------------|
| < 430px | Grid 4×6 → celule mai mici (min 44px), padding redus |
| 430–768px | Grid normal, font-uri standard |
| > 768px | Character decorativ apare lateral, form limitat 420px, grid mai spațios |

---

## Notes
- Pozițiile scatter-urilor se randomizează la fiecare page load (`Math.random`)
- Câmpurile deja flipped nu răspund la tap suplimentar
- Al 3-lea tap blochează automat toate câmpurile rămase
- Disclaimerul 18+ fix jos sau sub CTA — vizibil mereu
- Nu stoca date local — submit direct spre REGISTER_URL

# Realify design system — extraction (R8)

Read-only capture of what **is** in the code today, with real values quoted from source, so R11
(agency reskin) and R13 (interior reskin) can conform exactly. **Target = the marketing system.**

Sources:
- **Marketing site** — `realify/site/ui.py` (`CSS`, `_nav()`, `_footer()`, `doc()`), `ui_platform.py`,
  `ui_pricing.py`, `signin_page()`. All marketing pages render through one shared shell (`ui.doc`).
- **Seller interior** — `frontend.html` (one static file, inline `<style>` + inline `<script>`),
  served verbatim by `realify/routers/pages.py::home()` (with a `<!--BUSY_MODAL-->` serve-time inject).
- **Shared component** — `realify/site/busy_modal.py` (`SNIPPET` → `window.RealifyBusy`).

> The two systems diverge on **every** primitive (palette, fonts, radius, shadow, accent). That
> divergence is the reason this doc exists. Section 1 is the core finding.

---

## 1. TWO SYSTEMS, SIDE BY SIDE (the core finding)

| Primitive | **Marketing (TARGET)** — `ui.py CSS` | **Seller interior** — `frontend.html :root` |
|---|---|---|
| Background | `--bg:#F7F4EE` (warm paper) | `--paper:#EDEFF3` (cool grey-blue) |
| Card | `--card:#FFFFFF` | `--card:#FFFFFF` |
| Text (ink) | `--ink:#1A1A1A` · secondary `--ink2:#6E675C` | `--ink:#15233B` · `--ink-2:#2C3A52` · `--muted:#5B6678` |
| Accent / CTA | `--blue:#C4785B` (terracotta), hover `--blue-d:#A9603F` | `--competitive:#1E5FA8` (indigo, tab/selection) · `--action:#0E7C66` (green, primary action) |
| Heading font | `--serif:Georgia,"Times New Roman",serif` | `"Space Grotesk"` (UI headings) + `Georgia,serif` (brief H1 only) |
| Body font | `-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif` | `"Inter",system-ui,sans-serif` |
| Mono | `ui-monospace,"SF Mono",Menlo,monospace` | `"IBM Plex Mono",ui-monospace,monospace` |
| Border-radius | `9px` buttons/inputs · `14px` cards (`.card`) | `--r:14px` · `--r-sm:9px` (many one-offs 8–12px) |
| Shadow | soft: `0 2px 6px rgba(26,26,26,.06),0 14px 40px rgba(26,26,26,.07)` (`.browser` in mockups; marketing cards are mostly flat + `1px` border) | `--shadow:0 1px 2px rgba(21,35,59,.04),0 6px 20px rgba(21,35,59,.06)` · hover `--shadow-h:0 2px 6px…,0 14px 36px rgba(21,35,59,.10)` |
| Pill / tag | sand: `.tag{color:var(--blue);background:#EFE7D9;border-radius:20px;padding:5px 12px;font:mono 11px/.1em uppercase}` | mono chips w/ `1px var(--line)` border, `border-radius:6–20px`; badges use family hues |
| Line / border | `--line:#E4DDD0` (warm) | `--line:#DCE1EA` · `--line-2:#E8EBF0` (cool) |

The seller interior also carries a **family-hue palette** with no marketing equivalent:
`--competitive:#1E5FA8 --demand:#0E7C66 --opportunity:#6B4FBB --news:#B0541A --critical:#C23B3B
--positive:#2E7D4F --warn:#B5791A`.

**Net:** warm-paper + terracotta + Georgia-serif + flat/9px (marketing) vs cool-grey + indigo/green +
Inter/Space-Grotesk + soft-shadow/14px (interior). A reskin means moving the interior + agency
surfaces onto the marketing column above.

---

## 2. TOKENS (target / marketing system)

`ui.py` defines the one marketing token block (`CSS = """…"""`, top of file):

```css
:root{--ink:#1A1A1A;--ink2:#6E675C;--muted:#6E675C;--bg:#F7F4EE;--soft:#EFE9DE;--card:#FFFFFF;
--line:#E4DDD0;--blue:#C4785B;--blue-d:#A9603F;--slate:#5B7B94;--green:#7A9E7E;--amber:#A9603F;--red:#B3402E;
--serif:Georgia,"Times New Roman",serif;--mono:ui-monospace,"SF Mono",Menlo,monospace}
```

- **Palette:** ink `#1A1A1A` / ink2 `#6E675C` / muted `#6E675C`; paper `#F7F4EE`; soft (section tint)
  `#EFE9DE`; card `#FFFFFF`; line `#E4DDD0`; **terracotta (primary)** `#C4785B` / hover `#A9603F`;
  **slate** `#5B7B94`; **sage** `#7A9E7E`; **amber/gold** `#A9603F`; **alert-red** `#B3402E`.
  Dark sections: bg `--ink`, text `#EDE7DB`, card `#242220`, border `#3A3631`, muted `#A39B8D`.
- **Fonts:** serif `Georgia,"Times New Roman",serif` (all h1–h3, `.logo`); sans (body) the
  `-apple-system…Inter…` stack; mono `ui-monospace,"SF Mono",Menlo,monospace` (`.kick .tag .label`).
- **Type scale:** h1 `46px/1.12`, h2 `30px/1.14`, h3 `19px`, `.sub` `17.5px`, body `~15–16px`, mono
  eyebrows `11px` uppercase (`.kick` letter-spacing `.18em`, `.label` `.14em`, `.tag` `.1em`).
- **Radii:** buttons/inputs `9px` (`.btn`), cards `14px` (`.card`), pills `20px`/`100px` (`.tag`/`.chip`).
- **Spacing:** `.wrap{max-width:1080px;padding:0 24px}`; `section{padding:64px 0}`; `.hero{88px 0 60px}`;
  grid gap `16px` (`.g2/.g3/.g4`).
- **Sand pill:** `.tag{background:#EFE7D9;color:var(--blue);border-radius:20px;padding:5px 12px}`.
- **Shadow:** marketing cards are flat (`1px solid var(--line)`); the only real elevation is the mockup
  `.browser` frame `0 2px 6px rgba(26,26,26,.06),0 14px 40px rgba(26,26,26,.07)`.

There is **no** `:root` var block on the interior side beyond `frontend.html`'s own (section 1) — the
two never share a token source.

---

## 3. SHELL / CHROME (seller app — `frontend.html`)

Markup skeleton (verbatim structure, lines ~870–913):

```html
<header class="mast"><div class="wrap">
  <div class="mast-row">
    <div class="brand">
      <img class="logo-img" src="/assets/logo.png" alt="Realify" />
      <span class="tab mono" id="surfaceLabel">INTELLIGENCE</span>
    </div>
    <div class="mast-right">
      <div><div class="greet">Good morning, Shiva</div><div class="stamp" id="mastStamp"></div></div>
      <button class="act-btn" id="pulseBtn">◉ Pulse</button>
      <button class="act-btn" id="actBtn">☷ Activity <span class="cnt" id="actCnt">0</span></button>
      <button class="act-btn" id="rulesBtn">⚙ Rules</button>
      <button class="act-btn" id="acctBtn">⚙ Account</button>
    </div>
  </div>
  <!-- status strip -->
  <div class="statusbar" id="statusbar"><div class="sb-left">
      <span class="sb-ready" id="sbReady">Checking workspace…</span>
      <span class="sb-sep">·</span><span class="sb-feeds" id="sbFeeds">Market feeds —</span>
    </div><span class="sb-stamp" id="sbStamp"></span></div>
  <!-- surface tabs -->
  <div class="surftabs">
    <button class="surftab on" data-surface="catalog">Product Catalog <span class="st-sub">your SKUs</span></button>
    <button class="surftab" data-surface="cmaa">Profit &amp; Ads <span class="st-sub">margin vs spend</span></button>
    <button class="surftab" data-surface="intelligence">Intelligence <span class="st-sub">your products</span></button>
    <button class="surftab" data-surface="research">Category Analyst <span class="st-sub">overnight memo</span></button>
    <button class="surftab" data-surface="channels">Channels <span class="st-sub">cross-channel</span></button>
  </div>
  <div class="thesis"> … The Realify Brief … </div>
</div></header>
```

Chrome CSS (quoted):

```css
header.mast{border-bottom:1px solid var(--line);background:linear-gradient(180deg,#fff,#fbfcfe);position:sticky;top:0;z-index:40}
.brand b{font-family:"Space Grotesk";font-weight:700;font-size:18px}        /* wordmark; live app uses /assets/logo.png */
.brand .tab{font-family:"IBM Plex Mono";font-size:11px;color:var(--faint);border:1px solid var(--line);border-radius:6px;padding:3px 7px}  /* context pill */
.greet{font-family:"Space Grotesk";font-weight:600;font-size:14px}
.stamp{font-family:"IBM Plex Mono";font-size:11px;color:var(--faint)}
.act-btn{display:flex;align-items:center;gap:7px;border:1px solid var(--line);background:#fff;border-radius:9px;padding:8px 13px;font-size:13px;font-weight:500;font-family:"Inter"}
.act-btn .cnt{font-family:"IBM Plex Mono";font-size:11px;background:var(--ink);color:#fff;border-radius:20px;padding:1px 7px}
.statusbar{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-top:14px}
.sb-ready{font-family:"Space Grotesk";font-weight:600;font-size:13px;color:var(--positive)}  /* .pending → var(--warn) */
.surftab{border:1px solid var(--line);background:#fff;border-radius:11px 11px 0 0;padding:10px 18px}
.surftab .st-sub{font-family:"IBM Plex Mono";font-size:10.5px;color:var(--faint);text-transform:uppercase;letter-spacing:.04em}
.surftab.on{color:var(--ink);border-bottom:2px solid var(--competitive);background:var(--paper)}
```

There is **no footer** on the seller interior. The marketing footer lives in `ui.py::_footer()`
(dark `logo(dark=True)` wordmark + Product/Legal/Contact columns + `© 2026 Realify.ai`).

The seller **logo mark** is either the CSS `.mark` (30px rounded-ink square with two strokes) or the
live `/assets/logo.png` image; marketing uses the text wordmark `logo()` (Georgia, terracotta dot).

---

## 4. COMPONENTS (seller interior — HTML+CSS as-is)

### Tappable metric card (KPI band, tap-to-filter)
```css
.kpi-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding-bottom:16px}
.kpi-card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:14px 15px;cursor:pointer;transition:border-color .15s,box-shadow .15s}
.kpi-card:hover{border-color:#c3cbd8}
.kpi-card.sel{border-color:var(--competitive);box-shadow:inset 0 0 0 1px var(--competitive),0 2px 8px rgba(30,95,168,.12);background:#fff}
.kpi-head .lbl{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}
```
Label (mono uppercase, `--faint`) + value + sub + optional tag; **selected** = indigo border + inset
ring. This is the "REVENUE ₹1.07cr" card. Marketing's dark `.metric` (in `ui.py`, `#242220` card,
`.mk/.mv/.mt` rows) is the visual opposite.

### Period toggle (60d / 30d / 7d)
```css
.kpi-window{display:flex;gap:3px;background:var(--line-2);border-radius:8px;padding:3px}
.kpi-window button{border:none;background:transparent;font-family:"IBM Plex Mono";font-size:11.5px}
.kpi-window button.on{background:#fff;color:var(--ink);font-weight:600;box-shadow:0 1px 2px rgba(0,0,0,.06)}
```

### SKU table row (dot + SKU link + columns + sparkline)
```css
.sku-tbl{width:100%;border-collapse:collapse;font-size:12px}
.sku-tbl thead th{text-align:right;border-bottom:2px solid var(--ink);color:var(--faint);font-size:10.5px;text-transform:uppercase}
.sku-tbl tbody td{padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap;vertical-align:middle}
.sku-tbl tr.sku-row{cursor:pointer}.sku-tbl tr.sku-row:hover{background:#F7F9FC}.sku-tbl tr.sku-row.open{background:#F2F6FB}
.sku-tbl .sku-caret{color:var(--faint);font-size:11px}
.sku-tbl .sku-title{max-width:300px;overflow:hidden;text-overflow:ellipsis}
.spark{height:18px;margin-top:9px;display:block;width:100%}       /* sparkSVG(points,color) inline SVG */
```
Expandable detail row `tr.sku-detail td{background:#FBFCFE}` with `.sku-detail-grid .dl/.dv` label/value.

### Profit & Ads action-tint cards (bucket colors, from `_CMBK` config)
```
FIX ADS      col:#B23A3A   (recoverable — overspend above break-even)
SCALE        col:#1E7A4D   (directional upside — room to scale)
CUT/DIVEST   col:#B23A3A   (ad bleed to stop)
FIX MARGIN   col:#8a5a12   (unit-economics fix; no ad money to recover)
```
(These are literal `col:` values in the `_CMBK` JS object; the four buckets tint their cards/rails.)

### Category-pulse card / family filter chips / brief
- **Category-pulse** cards tint by family hue (`--competitive/--demand/--opportunity/--news`), sparkline
  via `sparkSVG(c.spark,tcolor)`.
- **Family chips** — cohort chips in Profit & Ads (`_cmCohorts`: `below_cost`, `cannibalization`) and
  scope selects `.an-scope-sel select{font-family:"Space Grotesk";border:1px solid var(--line);border-radius:8px}`.
- **THE BRIEF (light):** `.thesis{background:var(--card);border:1px solid var(--line);border-radius:14px;
  box-shadow:0 1px 2px rgba(21,35,59,.05),0 6px 18px rgba(21,35,59,.05)}` with a 3px `.bar` on top and
  a Georgia-serif `h1`.
- **THE BRIEF / hero (dark):** the Category Analyst + CMAA heroes are the dark panels —
  `.an-hero{background:linear-gradient(180deg,#15233B,#1c2f4f);color:#fff;border-radius:14px;padding:22px 24px}`,
  eyebrow `.an-hero-k{color:#9db4d8;letter-spacing:.16em;text-transform:uppercase}`, narrative
  `.an-hero-narr{font-family:Georgia,serif;font-size:18px}`.

### Buttons
- **Interior secondary/outline** (only button style in the shell): `.act-btn` / `.refresh`
  (`1px var(--line)`, white, `9px`, Inter). There is **no filled primary** button class in the shell —
  primary actions are the tinted CMAA/apply buttons and the busy-modal button.
- **Marketing** (`ui.py`): `.btn{border-radius:9px;padding:11px 20px;font-weight:600}` ·
  `.btn-blue{background:var(--blue);color:#fff}` (primary) · `.btn-ghost{border:1.5px solid var(--ink)}`
  (secondary) · `.btn-big{padding:14px 28px;font-size:15.5px}` · `.btn-wide{width:100%}`.

### Banners & badges
```css
/* provenance badges (first-class) */
.pv-off{background:#eef7f0;color:#1f6b3b;border:1px solid #bfe0c8}       /* OFFICIAL / live source */
.pv-scr{background:#fdf3e7;color:#9a5b12;border:1px dashed #e0b784}      /* SCRAPED (dashed = distinct) */
.an-badge-coming{background:var(--warn-bg);color:var(--warn-text);border:1px solid var(--warn-border);border-radius:20px}  /* COMING */
/* live indicator */
.dotpulse{width:7px;height:7px;border-radius:50%;background:var(--positive)}  /* pulsing ring ::after */
/* analyst "coming" data-state tokens */
--warn-border:#E0B784; --warn-bg:#FDF3E7; --warn-text:#9A5B12;
```
Marketing badges: `.badge` + `.tag` (sand pill, section 2).

---

## 5. JS INTERACTION CONTRACTS (reuse these — do not reinvent)

- **Tab / surface switching** — `frontend.html` binds `.surftab[data-surface]`; switching sets
  `activeSurface` (values: `catalog|cmaa|intelligence|research|channels`), updates `#surfaceLabel`, the
  footer label, and shows the matching surface `<section>`. A reskin keeps the `data-surface` contract
  and the `activeSurface` values.
- **Metric-tap-to-filter** — `.kpi-card` click toggles `.sel` (indigo ring) and filters the SKU
  table/list to that metric's cohort; the KPI band + period `.kpi-window` (`60d/30d/7d`) drive the
  active window. Reuse the `.kpi-card`/`.kpi-card.sel` + `.kpi-window button.on` contract.
- **Busy modal — `window.RealifyBusy`** (`realify/site/busy_modal.py`, injected at `<!--BUSY_MODAL-->`
  in `frontend.html`, and inlined in the hub / queue). Signatures:
  ```js
  RealifyBusy.open(title, sub)                 // blocking overlay + focus trap + elapsed counter
  RealifyBusy.success(msg, cb)                  // ✓ → close → cb()
  RealifyBusy.error(msg)                        // reason + Close, re-enables the trigger
  RealifyBusy.run(btn, {title, sub, refresh}, doFetch)          // SYNC action: modal up until the
                                                               //   fetch resolves; success→refresh()
  RealifyBusy.runJob(btn, {title, sub}, startFetch, statusUrl, {refresh})   // ACCEPTED→chip→poll→done
  RealifyBusy.chip(title)                       // persistent non-blocking progress chip
  ```
  Invocation pattern (from the queue / hub):
  ```js
  RealifyBusy.run(e.currentTarget, {title:'Submitting decision', refresh:()=>location.reload()},
    ()=>fetch('/api/…',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(p)}));
  ```
  Any reskin routes long actions through `RealifyBusy` (blocking overlay = the "no double-fire" device;
  the thread stays free — async fetch only).

---

## 6. REUSE VERDICT (what R11 / R13 depend on)

**Is `frontend.html` one static file or partials?** One monolithic static file (~3.6k lines) with a
single inline `<style>` and inline `<script>`, served verbatim by `pages.home()` (only dynamic touch:
the `<!--BUSY_MODAL-->` placeholder is string-replaced at serve time with `busy_modal.SNIPPET`). No
Jinja/partials for the seller app.

**Marketing** is the opposite: `realify/site/ui.py` is already a shared shell — `doc(title, body,
active)` wraps every marketing page with `_nav()` + `_footer()` + the one `CSS` token block. Adding a
page = call `ui.doc`. So the marketing system already has a single shared shell + token source.

**Agency surfaces** (`agency_console.py` queue, `agency_admin.py` fleet/quality, `pages.py` superlogin
hub/gate) each **build their own `<html>`+`<style>` string inline** — CSS is **duplicated per route**
(`_ADMIN_CSS` in `agency_admin`, an inline `<style>` in the queue, `_SL_CSS` in `pages`). They do **not**
import `ui.CSS`; their palettes are hand-rolled (mix of the interior indigo/slate and ad-hoc values).
The **only** thing shared across all of them today is `busy_modal.SNIPPET`.

**Shareable TODAY (no refactor):** `busy_modal.SNIPPET` (already reused in frontend + hub + queue); and
any new *marketing* page via `ui.doc`.

**Needs refactor:** there is no single token file. The smallest path to one shared shell + tokens both
the interior and the agency surfaces can import:

1. **Extract** `ui.py`'s `:root{…}` block (+ button/pill/card primitives) into one constant, e.g.
   `realify/site/tokens.py::TOKENS` (a `:root` string) and `SHELL_CSS`. `ui.CSS` becomes
   `TOKENS + SHELL_CSS + …` (no visual change).
2. **Point the agency Python-rendered surfaces at it** — replace `_ADMIN_CSS` / `_SL_CSS` / the queue's
   inline `<style>` with `from realify.site.tokens import TOKENS, SHELL_CSS`. Because these are already
   Python string builders, this is a **small, mechanical** change and immediately unifies R11's surfaces
   onto the marketing tokens.
3. **Converge the seller interior (`frontend.html`)** — it can't import Python. Either (a) inject the
   shared tokens the same way the busy modal is injected (`<!--TOKENS-->` placeholder replaced in
   `home()`), or (b) serve the tokens as a linked static stylesheet. This is the **larger** R13 step and
   also implies re-tokenizing `frontend.html`'s `:root` values from the interior palette to the
   marketing palette.

**Bottom line for R11/R13:** the agency surfaces' styles are inline/duplicated but are Python strings,
so once `tokens.py` exists they can point at the same token source with a one-line import each (R11 is
cheap). The seller interior is a static monolith with its own divergent `:root`; converging it needs the
placeholder-inject (or linked stylesheet) plus a value-level re-tokenization (R13 is the real work).
`RealifyBusy` and the `data-surface`/`.kpi-card.sel` JS contracts are already shared and must be reused
by both.

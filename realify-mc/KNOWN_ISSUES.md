# Realify MC — Known issues / patch log

## [OPEN] Demo SKUs must force IN locale (US market option invalid for demo)
- **Reported:** 2026-06-26 (Shiva)
- **Severity:** low (UX/data coherence), pre-existing
- **Symptom:** On onboarding, choosing **Demo SKUs** ("Use demo SKUs", `#optDemo`,
  `data-src="sample"`) while the market selector is set to **United States** produces an
  incoherent state: money formats as USD ($) over the bundled **Autofy** catalog, which is
  entirely India-mapped (amazon.in, ₹ pricing, IN categories from `realify/seller_data.json`).
- **Repro:** login → keep "Use demo SKUs" selected → set market dropdown to
  "United States — amazon.com ($)" → provision → feed shows $ over IN catalog.
- **Root cause:** `login.html` — the `#country` select (lines ~87–90) offers both IN and US
  independent of the chosen source. The demo/sample path posts
  `{mode:'synthetic', source:'sample', country:<US>}` (login.html ~line 230) even though the
  sample dataset is IN-only. There is no coupling between source=sample and locale.
- **Proposed fix (next build):** when `#optDemo` (source=sample) is selected, lock the market
  to IN — disable the US `<option>` (and/or disable the whole `#country` select, forcing
  value "IN"), with a short hint ("Demo catalog is India-only"). Re-enable full country choice
  only when `#optUpload` (source=upload) is selected, since uploaded data may be US. Keep the
  server tolerant: if `source=='sample'` and `country!='IN'`, coerce to IN server-side in the
  `/api/onboard` handler as a backstop.
- **Files:** `login.html` (optDemo/optUpload click handlers + `#country` markup); backstop in
  `run.py` `/api/onboard`.

  - **STATUS: FIXED 2026-06-26** — server coerces sample→IN in `/api/onboard`; frontend
    `lockMarket()` disables the US option and forces IN whenever Demo is selected.

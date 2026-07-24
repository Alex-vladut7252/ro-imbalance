# RO Imbalance — Estimated Imbalance Prices (static)

A static, always-on dashboard of Romanian balancing-market imbalance data, sourced
**only** from the public Transelectrica **DAMAS** reports — no invented numbers, no
interpolation, no ML.

- **Live page:** GitHub Pages (see repo Settings → Pages).
- **Data:** `data/<YYYY-MM-DD>.json`, one file per delivery day, ~1 year back.
- **Refresh:** a GitHub Action (`.github/workflows/refresh.yml`) fetches today +
  yesterday from DAMAS every ~30 min and commits the JSON. DAMAS has no CORS, so the
  fetch runs on the Action runner (server-side), not in the browser.

Volumes are shown in MW (DAMAS publishes MWh per 15-min ISP → ×4). Reserve prices
(`P …`) are shown only for the direction actually activated.

## Regenerate the full archive locally

`build_data.py` exports `damas_imbalance_history` (from the Flask app's SQLite DB)
to the per-day JSON files.

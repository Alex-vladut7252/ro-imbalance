# -*- coding: utf-8 -*-
"""Export the DAMAS archive (damas_imbalance_history) to compact per-day JSON for the
static GitHub Pages site. Raw DAMAS values (MWh/Lei) — the page applies x4 + gating."""
import sqlite3, json, os
DB = r"C:/Users/vladu/Desktop/dev/_archive/energy_prediction/energy_data.db"
OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)

# compact key map: raw DAMAS field -> short json key (page maps back)
FIELDS = [
    ("interval_from", "t"), ("neg_price", "np"), ("pos_price", "pp"),
    ("afrr_up_activated", "au"), ("afrr_down_activated", "ad"),
    ("mfrr_up_activated", "mu"), ("mfrr_down_activated", "md"),
    ("afrr_up_price", "pau"), ("afrr_down_price", "pad"),
    ("mfrr_up_price", "pmu"), ("mfrr_down_price", "pmd"),
    ("system_imbalance", "si"), ("netting_import", "ni"), ("netting_export", "ne"),
    ("sum_qup", "qu"), ("sum_qdn", "qd"), ("sum_qup_pup", "cu"), ("sum_qdown_pdn", "cd"),
]

c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
dates = [r[0] for r in c.execute("SELECT DISTINCT date FROM damas_imbalance_history ORDER BY date")]
written = 0
for d in dates:
    rows = c.execute("SELECT * FROM damas_imbalance_history WHERE date=? ORDER BY isp", (d,)).fetchall()
    out = []
    for r in rows:
        rec = {}
        for src, k in FIELDS:
            v = r[src]
            if v is not None:
                rec[k] = round(v, 3) if isinstance(v, float) else v
        out.append(rec)
    with open(os.path.join(OUT, f"{d}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    written += 1
c.close()

with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
    json.dump({"dates": dates}, f, separators=(",", ":"))
print(f"wrote {written} day files + index.json  ({dates[0]} .. {dates[-1]})")

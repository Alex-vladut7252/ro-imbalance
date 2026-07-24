# -*- coding: utf-8 -*-
"""Refresh recent days of the DAMAS imbalance archive (run by GitHub Actions).
Stdlib only. Fetches today + yesterday (RO) from the public DAMAS reports and writes
compact per-day JSON into data/, then updates data/index.json. Raw values only."""
import json, os, urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

B = "https://newmarkets.transelectrica.ro/usy-durom-publicreportg01/00121002500000000000000000000100"
UA = "Mozilla/5.0 (compatible; ro-imbalance/1.0; +github-actions)"
RO, UTC = ZoneInfo("Europe/Bucharest"), ZoneInfo("UTC")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

FIELDS = [("neg_price","np","estimatedPriceNegativeImbalance"),
          ("pos_price","pp","estimatedPricePositiveImbalance"),
          ("system_imbalance","si","estimatedSystemImbalance"),
          ("netting_import","ni","imbalanceNettingImport"),
          ("netting_export","ne","imbalanceNettingExport"),
          ("sum_qup","qu","sumQup"),("sum_qdn","qd","sumQdn"),
          ("sum_qup_pup","cu","sumQupPup"),("sum_qdown_pdn","cd","sumQdownPdn")]

def get(rep, f, t):
    u = f"{B}/publicReport/{rep}?timeInterval.from={f}&timeInterval.to={t}&pageInfo.pageSize=10000"
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r).get("itemList", [])

def rng(date_str):
    ls = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=RO)
    le = ls + timedelta(days=1)
    return (ls.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            le.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z"))

def isp_of(ti):
    try:
        s = datetime.fromisoformat(ti["from"].replace("Z", "+00:00")).astimezone(RO)
        return s.hour * 4 + s.minute // 15 + 1
    except Exception:
        return None

def by_isp(items):
    m = {}
    for r in items:
        if r.get("id"):
            k = r.get("ISP") or isp_of(r.get("timeInterval", {}))
            if k:
                m[k] = r
    return m

def num(x):
    return round(x, 3) if isinstance(x, (int, float)) else None

def build_day(date_str):
    f, t = rng(date_str)
    imb = get("estimatedImbalancePrices", f, t)
    marg = by_isp(get("marginalPricesOverview", f, t))
    act = by_isp(get("activatedBalancingEnergyOverview", f, t))
    out = []
    for r in imb:
        if not r.get("id"):
            continue
        isp = r.get("ISP", 0)
        if not isp:
            continue
        if not isinstance(r.get("estimatedPriceNegativeImbalance"), (int, float)):
            continue  # unsettled -> skip, never fake a 0
        m, a, ti = marg.get(isp, {}), act.get(isp, {}), r.get("timeInterval", {})
        rec = {"t": ti.get("from")}
        for _, k, src in FIELDS:
            v = num(r.get(src))
            if v is not None:
                rec[k] = v
        for k, src in [("au","aFRR_Up"),("ad","aFRR_Down"),("mu","mFRR_Up"),("md","mFRR_Down")]:
            v = num(a.get(src))
            if v is not None:
                rec[k] = v
        for k, src in [("pau","aFRR_Up"),("pad","aFRR_Down")]:
            v = num(m.get(src))
            if v is not None:
                rec[k] = v
        pmu = m.get("mFRR_Up") if m.get("mFRR_Up") is not None else m.get("mFRR_Up_Scheduled")
        pmd = m.get("mFRR_Down") if m.get("mFRR_Down") is not None else m.get("mFRR_Down_Scheduled")
        if num(pmu) is not None: rec["pmu"] = num(pmu)
        if num(pmd) is not None: rec["pmd"] = num(pmd)
        out.append(rec)
    return out

now = datetime.now(RO)
targets = [(now - timedelta(days=1)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")]
changed = []
for d in targets:
    try:
        rows = build_day(d)
        if rows:
            with open(os.path.join(DATA, f"{d}.json"), "w", encoding="utf-8") as fp:
                json.dump(rows, fp, separators=(",", ":"))
            changed.append(f"{d} ({len(rows)} ISP)")
    except Exception as e:
        print(f"  {d}: {e}")

dates = sorted(fn[:-5] for fn in os.listdir(DATA) if fn.endswith(".json") and fn != "index.json")
with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as fp:
    json.dump({"dates": dates, "updated": now.strftime("%Y-%m-%d %H:%M %Z")}, fp, separators=(",", ":"))
print("refreshed:", ", ".join(changed) or "nothing", "| total days:", len(dates))

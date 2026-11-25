"""Builds the compact JSON embedded in docs/index.html (the live dashboards) from the reconciled KPI set.
Run after compute_kpis.py:  python scripts/build_showcase_data.py"""
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ref = json.load(open(os.path.join(ROOT, "scripts", "kpi_reference.json")))


def clean(o):
    """Replace NaN with None so the embedded JSON is valid."""
    if isinstance(o, float) and math.isnan(o):
        return None
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


rows = ref["retail_monthly_cat_region"]
months = sorted({r["YearMonth"] for r in rows})
cats = sorted({r["Category"] for r in rows})
regs = ["North", "West", "South", "East", "Online"]
tgt = {(r["YearMonth"], r["Category"], r["Region"]): r["TargetAmount"] for r in ref["retail_target_cat_region"]}
retail = [[months.index(r["YearMonth"]), cats.index(r["Category"]), regs.index(r["Region"]), round(r["Net"]),
           round(r["Cost"]), round(r["Gross"]), round(tgt.get((r["YearMonth"], r["Category"], r["Region"]), 0))]
          for r in rows]
data = clean({
    "months": months, "cats": cats, "regs": regs, "retail": retail,
    "pnl": sorted(ref["finance_2025_pnl_groups"], key=lambda x: x["GroupSort"]),
    "finMonthly": [r for r in ref["finance_monthly_net_income"] if r["YearMonth"] >= "2024-01"],
    "opex": ref["finance_2025_opex_by_cc"],
    "le": ref["finance_2025_latest_estimate_net_income"],
    "supplyYear": ref["supply_by_year"],
    "supplyMonthly": ref["supply_monthly"],
    "suppliers": ref["supply_2025_suppliers"],
    "inv": ref["supply_inventory_monthly"],
    "invLast": ref["supply_inventory_last"],
})
js = json.dumps(data, separators=(",", ":"))
p = os.path.join(ROOT, "docs", "index.html")
html = open(p).read()
html = re.sub(r"/\*DATA\*/.*?/\*END\*/", lambda m: "/*DATA*/" + js + "/*END*/", html, flags=re.S)
open(p, "w").write(html)
print(f"Embedded {len(js) / 1024:.0f} KB of data into docs/index.html")

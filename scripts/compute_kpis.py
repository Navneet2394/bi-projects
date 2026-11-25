"""
Independent KPI calculation used for reconciliation.

Applies the same cleaning rules as the Power Query / SQL layer (remove duplicate source lines,
map missing customers to Unknown), then recomputes every headline KPI and finding quoted in the
project READMEs. Output: scripts/kpi_reference.json
"""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "01-retail-ecommerce-sales", "data")
F = os.path.join(ROOT, "02-finance-pnl-budget-variance", "data")
S = os.path.join(ROOT, "03-procurement-supply-chain-otif", "data")
out = {}


def ratio(a, b):
    return round(float(a) / float(b), 4) if b else None


# ============================ 01 Retail ============================
raw = pd.read_csv(f"{R}/FactSales.csv", keep_default_na=False, na_values=[""])
fs = raw.drop_duplicates(subset="SalesOrderLineKey").copy()
fs["CustomerKey"] = fs.CustomerKey.fillna(-1).astype(int)
out["retail_data_quality"] = {"raw_lines": len(raw), "duplicate_lines_removed": len(raw) - len(fs),
                              "lines_without_customer": int(raw.CustomerKey.isna().sum())}
dd = pd.read_csv(f"{R}/DimDate.csv")
dp = pd.read_csv(f"{R}/DimProduct.csv")
ds = pd.read_csv(f"{R}/DimStore.csv")
dc = pd.read_csv(f"{R}/DimCustomer.csv", keep_default_na=False)
tg = pd.read_csv(f"{R}/FactSalesTarget.csv")
f = (fs.merge(dd[["DateKey", "Year", "YearMonth", "MonthNo"]], left_on="OrderDateKey", right_on="DateKey")
       .merge(dp, on="ProductKey").merge(ds, on="StoreKey").merge(dc, on="CustomerKey"))
f["Net"] = f.SalesAmount.where(~f.IsReturned, 0)
f["NetCost"] = f.CostAmount.where(~f.IsReturned, 0)
tg["YearMonth"] = tg.MonthStartDate.str[:7]
tg["Year"] = tg.MonthStartDate.str[:4].astype(int)
tg = tg.merge(ds[["StoreKey", "Region"]], on="StoreKey")


def summ(v):
    net, cost, gross = v.Net.sum(), v.NetCost.sum(), v.SalesAmount.sum()
    orders = v.OrderNumber.nunique()
    return {"NetSales": round(net, 2), "GrossSales": round(gross, 2), "GrossMargin": round(net - cost, 2),
            "GM%": ratio(net - cost, net), "ReturnRate": ratio(gross - net, gross), "Orders": int(orders),
            "AOV": round(net / orders, 2), "ActiveCustomers": int(v[v.CustomerKey > 0].CustomerKey.nunique()),
            "AvgDiscount": round(float(v.DiscountPct.mean()), 4)}


out["retail_by_year"] = {int(y): summ(v) for y, v in f.groupby("Year")}
for y in (2024, 2025):
    out["retail_by_year"][y]["Target"] = round(tg[tg.Year == y].TargetAmount.sum(), 2)
    out["retail_by_year"][y]["Attainment"] = ratio(out["retail_by_year"][y]["NetSales"], out["retail_by_year"][y]["Target"])
    out["retail_by_year"][y]["YoY"] = ratio(out["retail_by_year"][y]["NetSales"] - out["retail_by_year"][y - 1]["NetSales"],
                                            out["retail_by_year"][y - 1]["NetSales"])
f25, f24 = f[f.Year == 2025], f[f.Year == 2024]
for dim in ["Category", "Region", "Channel", "Segment", "LoyaltyTier"]:
    d = {}
    for k, v in f25.groupby(dim):
        s = summ(v)
        py = f24[f24[dim] == k].Net.sum()
        s["YoY"] = ratio(s["NetSales"] - py, py)
        s["Share"] = ratio(s["NetSales"], f25.Net.sum())
        if dim == "Region":
            t = tg[(tg.Year == 2025) & (tg.Region == k)].TargetAmount.sum()
            s["Target"], s["Attainment"] = round(t, 2), ratio(s["NetSales"], t)
        if dim == "LoyaltyTier":
            s["OrdersPerCustomer"] = ratio(v.OrderNumber.nunique(), v.CustomerKey.nunique())
        d[k] = s
    out[f"retail_2025_by_{dim.lower()}"] = d
disc = f25.groupby("DiscountPct").apply(lambda v: pd.Series({"Net": v.Net.sum(), "GM%": ratio(v.Net.sum() - v.NetCost.sum(), v.Net.sum())}))
disc["Share"] = (disc.Net / disc.Net.sum()).round(4)
out["retail_2025_by_discount"] = {f"{k:.0%}": {"GM%": r["GM%"], "Share": r["Share"]} for k, r in disc.iterrows()}
fash = f25[f25.Category == "Fashion"].groupby("Channel").apply(lambda v: ratio(v.SalesAmount.sum() - v.Net.sum(), v.SalesAmount.sum()))
out["retail_2025_fashion_return_rate"] = fash.to_dict()
out["retail_monthly"] = f.groupby("YearMonth").agg(Net=("Net", "sum"), Cost=("NetCost", "sum")).round(2).reset_index().to_dict("records")
out["retail_target_monthly"] = tg.groupby("YearMonth").TargetAmount.sum().round(2).reset_index().to_dict("records")
out["retail_monthly_cat_region"] = (f.groupby(["YearMonth", "Category", "Region"])
                                    .agg(Net=("Net", "sum"), Cost=("NetCost", "sum"), Gross=("SalesAmount", "sum"))
                                    .round(2).reset_index().to_dict("records"))
out["retail_target_cat_region"] = (tg.groupby(["YearMonth", "Category", "Region"]).TargetAmount.sum()
                                   .round(2).reset_index().to_dict("records"))

# ============================ 02 Finance ============================
ff = pd.read_csv(f"{F}/FactFinance.csv")
fa = pd.read_csv(f"{F}/DimAccount.csv")
fc = pd.read_csv(f"{F}/DimCostCenter.csv")
g = ff.merge(fa, on="AccountKey").merge(fc, on="CostCenterKey")
g["Year"] = g.DateKey // 10000
g["YearMonth"] = (g.DateKey // 100).astype(str).str[:4] + "-" + (g.DateKey // 100).astype(str).str[4:]
g["Signed"] = g.Amount * g.PnLSign * g.NaturalSign
pnl = g[g.Year == 2025].pivot_table(index=["GroupSort", "AccountGroup"], columns="Scenario", values="Signed",
                                    aggfunc="sum").fillna(0).reset_index()
out["finance_2025_pnl_groups"] = pnl.round(2).to_dict("records")
mo = g[g.Scenario.isin(["Actual", "Budget"])].pivot_table(index="YearMonth", columns="Scenario", values="Signed",
                                                           aggfunc="sum").reset_index()
out["finance_monthly_net_income"] = mo.round(2).to_dict("records")
cc = g[(g.Year == 2025) & g.Scenario.isin(["Actual", "Budget"]) & (g.AccountGroup == "Operating Expenses")]
out["finance_2025_opex_by_cc"] = cc.pivot_table(index="CostCenter", columns="Scenario", values="Amount",
                                                aggfunc="sum").round(2).reset_index().to_dict("records")
acc = g[(g.Year == 2025) & g.Scenario.isin(["Actual", "Budget"])].pivot_table(index=["AccountName", "AccountGroup"],
                                                                              columns="Scenario", values="Signed", aggfunc="sum")
acc["Var"] = acc.Actual - acc.Budget
out["finance_2025_by_account"] = acc.round(2).reset_index().sort_values("Var").to_dict("records")
le = g[(g.Year == 2025) & (((g.Scenario == "Actual") & (g.DateKey < 20250701)) | ((g.Scenario == "Forecast") & (g.DateKey >= 20250701)))]
out["finance_2025_latest_estimate_net_income"] = round(le.Signed.sum(), 2)

# ============================ 03 Supply chain ============================
po = pd.read_csv(f"{S}/FactPurchaseOrderLine.csv", parse_dates=["PromisedDate", "ReceivedDate"])
sp = pd.read_csv(f"{S}/DimSupplier.csv")
po = po.merge(sp, on="SupplierKey")
po["OnTime"] = po.ReceivedDate <= po.PromisedDate
po["InFull"] = po.ReceivedQty >= po.OrderedQty
po["OTIF"] = po.OnTime & po.InFull
po["DaysLate"] = (po.ReceivedDate - po.PromisedDate).dt.days.clip(lower=0)
po["Year"] = po.OrderDateKey // 10000
po["YearMonth"] = po.PromisedDate.dt.strftime("%Y-%m")
po["Import"] = po.Country != "India"
agg = dict(Lines=("POLineKey", "count"), OnTime=("OnTime", "mean"), InFull=("InFull", "mean"),
           OTIF=("OTIF", "mean"), Spend=("LineValue", "sum"))
out["supply_by_year"] = po.groupby("Year").agg(**agg).round(4).reset_index().to_dict("records")
out["supply_monthly"] = po[po.PromisedDate <= "2025-12-31"].groupby("YearMonth").agg(**agg).round(4).reset_index().to_dict("records")
p25 = po[po.Year == 2025]
late = p25[p25.DaysLate > 0]
s25 = p25.groupby(["SupplierName", "Country", "Tier", "Category"]).agg(
    Lines=("POLineKey", "count"), OTIF=("OTIF", "mean"), OnTime=("OnTime", "mean"), InFull=("InFull", "mean"),
    Spend=("LineValue", "sum")).reset_index()
s25 = s25.merge(late.groupby("SupplierName").DaysLate.mean().rename("AvgDaysLateWhenLate").reset_index(), how="left")
out["supply_2025_suppliers"] = s25.round(4).sort_values("OTIF").to_dict("records")
out["supply_2025_by_tier"] = p25.groupby("Tier").OTIF.mean().round(4).to_dict()
out["supply_2025_import_vs_domestic"] = {("Import" if k else "Domestic"): round(v, 4) for k, v in p25.groupby("Import").OTIF.mean().items()}
out["supply_otif_by_promised_month_2024_25"] = po[po.PromisedDate.dt.year.isin([2024, 2025])].groupby(po.PromisedDate.dt.month).OTIF.mean().round(4).to_dict()
spend_low = s25[s25.OTIF < 0.75].Spend.sum()
out["supply_2025_spend_below_75_otif"] = {"Spend": round(spend_low, 2), "Share": ratio(spend_low, s25.Spend.sum())}
inv = pd.read_csv(f"{S}/FactInventorySnapshot.csv")
ss = pd.read_csv(f"{S}/SafetyStock.csv")
pr = pd.read_csv(f"{S}/DimProduct.csv")
inv = inv.merge(ss, on=["WarehouseKey", "ProductKey"]).merge(pr[["ProductKey", "Category", "UnitCost"]], on="ProductKey")
inv["Value"] = inv.OnHandUnits * inv.UnitCost
inv["BelowSafety"] = inv.OnHandUnits < inv.SafetyStockUnits
last = inv[inv.SnapshotDateKey == inv.SnapshotDateKey.max()]
out["supply_inventory_last"] = {"SnapshotDateKey": int(last.SnapshotDateKey.max()), "Value": round(float(last.Value.sum()), 2),
                                "StockoutRiskPct": round(float(last.BelowSafety.mean()), 4)}
out["supply_inventory_monthly"] = inv.groupby("SnapshotDateKey").agg(Value=("Value", "sum"), BelowSafety=("BelowSafety", "mean")).round(4).reset_index().to_dict("records")
oct25 = inv[inv.SnapshotDateKey == 20251031]
out["supply_oct2025_below_safety_by_category"] = oct25.groupby("Category").BelowSafety.mean().round(4).to_dict()

with open(os.path.join(ROOT, "scripts", "kpi_reference.json"), "w") as fh:
    json.dump(out, fh, indent=1, default=str)
print(json.dumps({k: out[k] for k in ["retail_data_quality", "retail_by_year"]}, indent=1, default=str))

"""
Data generator for the BI Projects repository.

Creates one consistent synthetic dataset for an Indian omni-channel retailer,
"Northwind Omni Retail" (all amounts in INR), and writes it to the /data folder of each project:

  01 Retail & e-commerce sales   : orders, products, stores, customers, monthly sales plan
  02 Finance P&L                 : actuals derived from the same sales and costs; budget from the sales plan
  03 Procurement & supply chain  : purchase orders and inventory for the same products

Business scenarios built into the data (what the reports are expected to reveal):
  - Online grows ~25% a year; physical stores 3-12% depending on region.
  - East region relies on heavier discounting, earns the lowest margin and misses its plan.
  - Electronics is the largest category but has the thinnest margin; Fashion has high margin and
    high returns, especially online.
  - Discounts above 15% erase most of the margin; festive months (Oct-Nov) bring peak sales and
    deeper discounts.
  - Marketing overspends during the 2025 festive campaign; COGS runs above plan because of the
    discount-heavy mix.
  - Import suppliers have longer lead times and miss more deliveries; pre-festive peak (Sep-Oct)
    lowers on-time delivery; two transactional suppliers have poor in-full performance.

Real-world data issues deliberately present in the raw extracts (cleaned in Power Query / SQL):
  - FactSales.csv contains exact duplicate lines from a double-loaded source batch.
  - Some online guest orders have a blank CustomerKey (mapped to an "Unknown" customer).

Usage:  pip install pandas numpy  ->  python scripts/generate_data.py
Deterministic: the same seed always produces the same data.
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P1, P2, P3 = "01-retail-ecommerce-sales", "02-finance-pnl-budget-variance", "03-procurement-supply-chain-otif"
YEARS = [2023, 2024, 2025]
SEED = int(os.environ.get("SEED", 7))
rng = np.random.default_rng(SEED)


def out(project, name, df):
    path = os.path.join(ROOT, project, "data", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  {project}/data/{name:<28} {len(df):>8,} rows")


# =========================================================================== #
# Shared dimensions
# =========================================================================== #
def dim_date():
    d = pd.DataFrame({"Date": pd.date_range("2023-01-01", "2025-12-31", freq="D")})
    d["DateKey"] = d.Date.dt.strftime("%Y%m%d").astype(int)
    d["Year"] = d.Date.dt.year
    d["Quarter"] = "Q" + d.Date.dt.quarter.astype(str)
    d["MonthNo"] = d.Date.dt.month
    d["Month"] = d.Date.dt.strftime("%b")
    d["YearMonth"] = d.Date.dt.strftime("%Y-%m")
    d["WeekdayNo"] = d.Date.dt.weekday + 1
    d["Weekday"] = d.Date.dt.strftime("%a")
    d["IsWeekend"] = d.WeekdayNo >= 6
    fy = np.where(d.MonthNo >= 4, d.Year + 1, d.Year)          # Indian FY: April-March
    d["FiscalYear"] = "FY" + pd.Series(fy % 100).astype(str).str.zfill(2)
    d["IsFestiveSeason"] = d.MonthNo.isin([10, 11])
    d["Date"] = d.Date.dt.date
    return d


CATS = {  # category: (sub-categories with price range INR, base gross margin, return rate, units range)
    "Electronics": ({"Mobiles": (8000, 40000), "Laptops": (30000, 75000), "Audio": (1000, 12000),
                     "Accessories": (300, 3000)}, 0.17, 0.03, (1, 1)),
    "Home": ({"Kitchen": (500, 8000), "Furniture": (5000, 60000), "Decor": (300, 4000)}, 0.30, 0.04, (1, 2)),
    "Fashion": ({"Menswear": (500, 4000), "Womenswear": (600, 5000), "Footwear": (800, 6000)}, 0.50, 0.09, (1, 3)),
    "Grocery": ({"Staples": (50, 800), "Beverages": (40, 500), "Snacks": (20, 300)}, 0.18, 0.01, (2, 8)),
    "Beauty": ({"Skincare": (200, 2500), "Haircare": (150, 1500)}, 0.48, 0.02, (1, 3)),
}
BRANDS = {"Electronics": ["Voltix", "Nexa", "Orbit"], "Home": ["Casa", "Woodline", "Hearth"],
          "Fashion": ["Threadly", "Urbano", "Kaya"], "Grocery": ["DailyFresh", "Annapurna"],
          "Beauty": ["Glowe", "Herbana"]}


def dim_product():
    rows, k = [], 1
    for cat, (subs, gm, rr, _) in CATS.items():
        for sub, (lo, hi) in subs.items():
            for i in range(12):
                price = round(float(np.exp(rng.uniform(np.log(lo), np.log(hi)))), -1 if hi > 1000 else 0)
                margin = np.clip(gm + rng.normal(0, 0.03), 0.05, 0.7)
                cost = round(price * (1 - margin), 2)
                rows.append([k, f"SKU-{k:05d}", f"{rng.choice(BRANDS[cat])} {sub} {chr(65 + i)}{rng.integers(10, 99)}",
                             sub, cat, rng.choice(BRANDS[cat]), price, cost,
                             "A" if price > 20000 else ("B" if price > 3000 else "C")])
                k += 1
    return pd.DataFrame(rows, columns=["ProductKey", "SKU", "ProductName", "SubCategory", "Category", "Brand",
                                       "ListPrice", "UnitCost", "ABCClass"])


REGIONS = {  # region: cities, annual growth, avg extra discount, base orders per year (2023)
    "North": (["Delhi", "Chandigarh", "Lucknow"], 1.07, 0.00, 3600),
    "West": (["Mumbai", "Pune", "Ahmedabad"], 1.12, -0.01, 3800),
    "South": (["Bengaluru", "Chennai", "Hyderabad"], 1.11, 0.00, 3700),
    "East": (["Kolkata", "Bhubaneswar"], 1.03, 0.05, 2600),
    "Online": (["Online"], 1.25, 0.03, 3400),
}


def dim_store():
    rows, k = [], 1
    for reg, (cities, *_ ) in REGIONS.items():
        for c in cities:
            fmts = ["Online"] if reg == "Online" else ["Flagship", "Express"]
            for f in fmts:
                name = "Northwind Online Store" if reg == "Online" else f"{c} {f}"
                code = "ST-ONL" if reg == "Online" else f"ST-{k:03d}"
                open_date = "2019-04-01" if reg == "Online" else f"{rng.integers(2012, 2021)}-{rng.integers(1, 13):02d}-01"
                rows.append([k, code, name, c, reg, f, open_date, f"rm.{reg.lower()}@northwind.example"])
                k += 1
    return pd.DataFrame(rows, columns=["StoreKey", "StoreCode", "StoreName", "City", "Region", "Format",
                                       "OpenDate", "RegionalManagerEmail"])


def dim_customer(n=6000):
    tiers = rng.choice(["No Tier", "Silver", "Gold", "Platinum"], n, p=[.50, .30, .15, .05])
    home = rng.choice(list(REGIONS), n, p=[.21, .22, .22, .13, .22])
    c = pd.DataFrame({
        "CustomerKey": np.arange(1, n + 1),
        "CustomerCode": [f"C{i:06d}" for i in range(1, n + 1)],
        "Segment": rng.choice(["Consumer", "Corporate", "Small Business"], n, p=[.75, .15, .10]),
        "LoyaltyTier": tiers,
        "HomeRegion": home,
        "SignupDate": (pd.Timestamp("2020-01-01") + pd.to_timedelta(rng.integers(0, 2000, n), "D")).date,
    })
    unknown = pd.DataFrame([{"CustomerKey": -1, "CustomerCode": "UNKNOWN", "Segment": "Unknown",
                             "LoyaltyTier": "Unknown", "HomeRegion": "Unknown", "SignupDate": None}])
    return pd.concat([unknown, c], ignore_index=True)


# =========================================================================== #
# 01 Retail
# =========================================================================== #
SEASON = {1: 1.0, 2: 0.9, 3: 1.1, 4: 1.0, 5: 1.0, 6: 0.95, 7: 1.0, 8: 1.0, 9: 1.05, 10: 1.6, 11: 1.5, 12: 1.15}
CAT_MIX = {"Store": [.26, .24, .34, .08, .08], "Online": [.30, .14, .40, .05, .11]}
TIER_FREQ = {"No Tier": 1.0, "Silver": 1.6, "Gold": 2.8, "Platinum": 4.5, "Unknown": 0}


def retail(date, prod, store, cust):
    dates = pd.to_datetime(date.Date)
    cats = list(CATS)
    prod_by_cat = {c: prod[prod.Category == c] for c in cats}
    lines, order_no = [], 100000
    real_cust = cust[cust.CustomerKey > 0]
    for reg, (cities, growth, extra_disc, base_orders) in REGIONS.items():
        reg_stores = store[store.Region == reg]
        s_w = np.where(reg_stores.Format == "Flagship", 1.3, 1.0); s_w = s_w / s_w.sum()
        pool = real_cust if reg == "Online" else real_cust[real_cust.HomeRegion == reg]
        c_w = pool.LoyaltyTier.map(TIER_FREQ).values; c_w = c_w / c_w.sum()
        channel = "Online" if reg == "Online" else "Store"
        for y in YEARS:
            yd = date[date.Year == y]
            w = yd.MonthNo.map(SEASON).values * np.where(yd.IsWeekend & (channel == "Store"), 1.25, 1.0)
            n_orders = int(base_orders * growth ** (y - 2023))
            day_idx = rng.choice(len(yd), n_orders, p=w / w.sum())
            st_idx = rng.choice(len(reg_stores), n_orders, p=s_w)
            cu_idx = rng.choice(len(pool), n_orders, p=c_w)
            for i in range(n_orders):
                order_no += 1
                drow = yd.iloc[day_idx[i]]
                cust_row = pool.iloc[cu_idx[i]]
                ck = int(cust_row.CustomerKey)
                if channel == "Online" and rng.random() < 0.02:
                    ck = None                                     # guest checkout: key missing in source
                corp = cust_row.Segment == "Corporate"
                n_lines = min(5, 1 + rng.poisson(0.6 + (0.8 if corp else 0)))
                festive = drow.MonthNo in (10, 11)
                base_d = 0.04 + extra_disc + (0.05 if festive else 0) + (0.02 if channel == "Online" else 0)
                for ln in range(1, n_lines + 1):
                    cat = rng.choice(cats, p=CAT_MIX[channel])
                    pr = prod_by_cat[cat].iloc[rng.integers(len(prod_by_cat[cat]))]
                    lo, hi = CATS[cat][3]
                    qty = int(rng.integers(lo, hi + 1)) * (2 if corp and cat != "Electronics" else 1)
                    disc = float(np.clip(round(rng.normal(base_d, 0.05) / 0.05) * 0.05, 0, 0.30))
                    rr = CATS[cat][2] * (1.6 if channel == "Online" else 1.0)
                    lines.append([order_no, ln, int(drow.DateKey), int(pr.ProductKey), int(reg_stores.iloc[st_idx[i]].StoreKey),
                                  ck, channel, qty, pr.ListPrice, disc,
                                  round(qty * pr.ListPrice * (1 - disc), 2), round(qty * pr.UnitCost, 2),
                                  bool(rng.random() < rr)])
    f = pd.DataFrame(lines, columns=["OrderNumber", "LineNumber", "OrderDateKey", "ProductKey", "StoreKey",
                                     "CustomerKey", "Channel", "Quantity", "UnitPrice", "DiscountPct",
                                     "SalesAmount", "CostAmount", "IsReturned"])
    f = f.sort_values(["OrderDateKey", "OrderNumber", "LineNumber"]).reset_index(drop=True)
    f.insert(0, "SalesOrderLineKey", np.arange(1, len(f) + 1))
    f["OrderNumber"] = "SO" + f.OrderNumber.astype(str)
    f["CustomerKey"] = f.CustomerKey.astype("Int64")
    clean = f.copy()
    # Source issue: one batch (2-3 Mar 2025) was loaded twice -> exact duplicate lines
    dup = f[f.OrderDateKey.isin([20250302, 20250303])]
    raw = pd.concat([f, dup]).sort_values(["SalesOrderLineKey"]).reset_index(drop=True)
    return clean, raw


def sales_plan(clean, store, prod):
    """Monthly plan per store x category for 2024 and 2025 = prior-year actual x planned growth."""
    x = clean[~clean.IsReturned].merge(prod[["ProductKey", "Category"]], on="ProductKey")
    x["Y"] = x.OrderDateKey // 10000
    x["M"] = x.OrderDateKey // 100 % 100
    a = x.groupby(["Y", "M", "StoreKey", "Category"], as_index=False).SalesAmount.sum()
    a = a.merge(store[["StoreKey", "Region"]], on="StoreKey")
    plan_growth = {"North": 1.07, "West": 1.10, "South": 1.10, "East": 1.08, "Online": 1.18}
    rows = []
    for y in (2024, 2025):
        py = a[a.Y == y - 1]
        for r in py.itertuples():
            rows.append([f"{y}-{r.M:02d}-01", r.StoreKey, r.Category, round(r.SalesAmount * plan_growth[r.Region], -2)])
    return pd.DataFrame(rows, columns=["MonthStartDate", "StoreKey", "Category", "TargetAmount"])


# =========================================================================== #
# 02 Finance (derived from retail)
# =========================================================================== #
def finance(clean, plan, store, prod):
    acc = pd.DataFrame([
        (4000, "Product Sales (Gross)", "Revenue", 1, 1, 1),
        (4100, "Extended Warranty & Services", "Revenue", 1, 1, 1),
        (4900, "Returns & Allowances", "Revenue", 1, 1, -1),
        (5000, "Cost of Goods Sold", "COGS", 2, -1, 1),
        (5100, "Freight & Fulfilment", "COGS", 2, -1, 1),
        (6000, "Salaries & Wages", "Operating Expenses", 3, -1, 1),
        (6100, "Rent & Utilities", "Operating Expenses", 3, -1, 1),
        (6200, "Marketing & Promotions", "Operating Expenses", 3, -1, 1),
        (6300, "IT & Software", "Operating Expenses", 3, -1, 1),
        (6400, "Travel & Admin", "Operating Expenses", 3, -1, 1),
        (7000, "Depreciation", "D&A", 4, -1, 1),
        (8000, "Interest Expense", "Finance Cost", 5, -1, 1),
        (9000, "Income Tax", "Tax", 6, -1, 1),
    ], columns=["AccountKey", "AccountName", "AccountGroup", "GroupSort", "PnLSign", "NaturalSign"])
    cc = pd.DataFrame({
        "CostCenterKey": range(1, 9),
        "CostCenter": ["Retail North", "Retail West", "Retail South", "Retail East", "E-Commerce",
                       "Corporate Finance", "Corporate IT", "Marketing HQ"],
        "Region": ["North", "West", "South", "East", "Online", None, None, None],
        "Division": ["Retail"] * 4 + ["Digital"] + ["Corporate"] * 3,
        "Owner": ["A. Mehta", "R. Iyer", "S. Rao", "P. Das", "K. Shah", "N. Gupta", "V. Nair", "L. Kapoor"],
    })
    reg2cc = dict(zip(cc.Region, cc.CostCenterKey))
    x = clean.merge(store[["StoreKey", "Region"]], on="StoreKey").merge(prod[["ProductKey", "Category"]], on="ProductKey")
    x["MonthKey"] = x.OrderDateKey // 100 * 100 + 1
    x["Ret"] = np.where(x.IsReturned, x.SalesAmount, 0.0)
    x["NetCost"] = np.where(x.IsReturned, 0.0, x.CostAmount)
    x["NetSales"] = x.SalesAmount - x.Ret
    x["ElecNet"] = np.where(x.Category == "Electronics", x.NetSales, 0.0)
    g = x.groupby(["MonthKey", "Region"], as_index=False)[["SalesAmount", "Ret", "NetCost", "NetSales", "ElecNet"]].sum()

    rows = []
    def add(dk, a, c, sc, v):
        rows.append([int(dk), a, c, sc, round(float(v), 2)])

    months = sorted(g.MonthKey.unique())
    # ---- Actuals: revenue and COGS straight from the sales ledger
    for r in g.itertuples():
        c = reg2cc[r.Region]
        add(r.MonthKey, 4000, c, "Actual", r.SalesAmount)
        add(r.MonthKey, 4900, c, "Actual", r.Ret)
        add(r.MonthKey, 4100, c, "Actual", r.ElecNet * 0.03)
        add(r.MonthKey, 5000, c, "Actual", r.NetCost)
        add(r.MonthKey, 5100, c, "Actual", r.NetSales * (0.045 if r.Region == "Online" else 0.012))
    # ---- Budget (2024-2025): from the sales plan with plan assumptions
    p = plan.merge(store[["StoreKey", "Region"]], on="StoreKey")
    p["MonthKey"] = pd.to_datetime(p.MonthStartDate).dt.strftime("%Y%m%d").astype(int)
    pc = x[x.MonthKey < 20240101].groupby("Region").apply(lambda v: v.NetCost.sum() / v.NetSales.sum())
    pb = p.groupby(["MonthKey", "Region"], as_index=False).TargetAmount.sum()
    for r in pb.itertuples():
        c = reg2cc[r.Region]
        net = r.TargetAmount
        ret_rate = 0.05 if r.Region == "Online" else 0.03
        gross = net / (1 - ret_rate)
        add(r.MonthKey, 4000, c, "Budget", gross)
        add(r.MonthKey, 4900, c, "Budget", gross * ret_rate)
        add(r.MonthKey, 4100, c, "Budget", net * 0.42 * 0.035)              # plan: 3.5% attach on electronics
        add(r.MonthKey, 5000, c, "Budget", net * (pc[r.Region] - 0.005))     # plan: 0.5 pp better margin
        add(r.MonthKey, 5100, c, "Budget", net * (0.040 if r.Region == "Online" else 0.012))
    # ---- Operating costs: run-rate model, budget = plan, actual = plan +/- noise and known overruns
    sal = {1: 1.4e6, 2: 1.5e6, 3: 1.5e6, 4: 1.0e6, 5: 0.9e6, 6: 1.1e6, 7: 1.3e6, 8: 0.7e6}
    rent = {1: 0.9e6, 2: 1.0e6, 3: 0.95e6, 4: 0.6e6, 5: 0.25e6}
    for mk in months:
        y, m = mk // 10000, mk // 100 % 100
        infl = 1.07 ** (y - 2023)
        festive = m in (10, 11)
        for c in range(1, 9):
            items = {6000: sal[c] * infl}
            if c in rent:
                items[6100] = rent[c] * 1.05 ** (y - 2023)
            if c == 8:
                items[6200] = 2.6e6 * infl * (2.2 if festive else 1.0)
            if c == 5:
                items[6200] = 1.2e6 * 1.2 ** (y - 2023) * (1.8 if festive else 1.0)   # performance marketing
            if c == 7:
                items[6300] = 1.1e6 * infl
            items[6400] = 0.12e6 * infl
            if c in (1, 2, 3, 4, 5, 7):
                items[7000] = (0.35e6 if c != 7 else 0.5e6) * (1.04 ** (y - 2023))
            if c == 6:
                items[8000] = 0.45e6
            # scale the run-rate model to company size (opex ~13% of revenue, D&A ~1.3%)
            items = {a: v * {7000: 0.155, 8000: 0.22}.get(a, 0.166) for a, v in items.items()}
            for a, v in items.items():
                over = 1.0
                if a == 6200 and y == 2025 and festive:
                    over = 1.28                                               # festive campaign overspend
                actual = v * over * rng.normal(1.0, 0.03)
                add(mk, a, c, "Actual", actual)
                if y >= 2024:
                    add(mk, a, c, "Budget", v)
    f = pd.DataFrame(rows, columns=["DateKey", "AccountKey", "CostCenterKey", "Scenario", "Amount"])
    # ---- Tax: 25.17% of positive monthly PBT, booked to Corporate Finance
    sign = acc.set_index("AccountKey")[["PnLSign", "NaturalSign"]].prod(axis=1)
    tax_rows = []
    for (dk, sc), v in f.groupby(["DateKey", "Scenario"]):
        pbt = (v.Amount * v.AccountKey.map(sign)).sum()
        tax_rows.append([dk, 9000, 6, sc, round(max(pbt, 0) * 0.2517, 2)])
    f = pd.concat([f, pd.DataFrame(tax_rows, columns=f.columns)], ignore_index=True)
    # ---- Rolling forecast made after June 2025 close: Jul-Dec = budget re-phased with H1 learnings
    fc = f[(f.Scenario == "Budget") & (f.DateKey >= 20250701)].copy()
    fc["Scenario"] = "Forecast"
    fc.loc[fc.AccountKey == 5000, "Amount"] *= 1.012
    fc.loc[fc.AccountKey == 6200, "Amount"] *= 1.10
    fc["Amount"] = fc.Amount.round(2)
    f = pd.concat([f, fc], ignore_index=True).sort_values(["DateKey", "Scenario", "CostCenterKey", "AccountKey"])
    return acc, cc, f.reset_index(drop=True)


# =========================================================================== #
# 03 Procurement & supply chain (same products)
# =========================================================================== #
def supply(clean, prod):
    sup = pd.DataFrame([
        (1, "Shenzhen Brightway Electronics", "China", "Electronics", "Strategic", 35, 0.86, 0.95),
        (2, "Hanoi Digital Components", "Vietnam", "Electronics", "Preferred", 30, 0.82, 0.93),
        (3, "Pune Tech Distributors", "India", "Electronics", "Strategic", 7, 0.93, 0.97),
        (4, "Delhi Gadget Wholesale", "India", "Electronics", "Transactional", 6, 0.80, 0.80),
        (5, "Ningbo HomeWorks", "China", "Home", "Preferred", 40, 0.78, 0.94),
        (6, "Jodhpur Woodcraft", "India", "Home", "Strategic", 14, 0.92, 0.96),
        (7, "Moradabad Kitchenware", "India", "Home", "Preferred", 10, 0.88, 0.95),
        (8, "Tiruppur Apparel Mills", "India", "Fashion", "Strategic", 12, 0.94, 0.97),
        (9, "Dhaka Garments Export", "Bangladesh", "Fashion", "Preferred", 28, 0.81, 0.92),
        (10, "Agra Footwear Co", "India", "Fashion", "Transactional", 9, 0.83, 0.79),
        (11, "Annapurna Foods", "India", "Grocery", "Strategic", 3, 0.95, 0.96),
        (12, "Kolkata FMCG Traders", "India", "Grocery", "Transactional", 4, 0.85, 0.88),
        (13, "Herbana Naturals", "India", "Beauty", "Preferred", 8, 0.91, 0.95),
        (14, "Seoul Beauty Labs", "South Korea", "Beauty", "Preferred", 25, 0.84, 0.94),
    ], columns=["SupplierKey", "SupplierName", "Country", "Category", "Tier", "ContractLeadTimeDays",
                "_ontime", "_infull"])
    wh = pd.DataFrame({"WarehouseKey": range(1, 6),
                       "Warehouse": ["DC Delhi", "DC Mumbai", "DC Bengaluru", "DC Kolkata", "DC Bengaluru E-Com"],
                       "Region": ["North", "West", "South", "East", "Online"],
                       "CapacityUnits": [60000, 70000, 65000, 35000, 80000]})
    reg2wh = dict(zip(wh.Region, wh.WarehouseKey))
    # demand per product x warehouse x month (units sold) drives replenishment
    s = clean.merge(pd.read_csv(os.path.join(ROOT, P1, "data", "DimStore.csv"))[["StoreKey", "Region"]], on="StoreKey")
    s["MonthKey"] = s.OrderDateKey // 100
    dem = s.groupby(["MonthKey", "Region", "ProductKey"], as_index=False).Quantity.sum()
    item = prod[["ProductKey", "Category", "ABCClass", "UnitCost"]].copy()
    cat_sups = {c: sup[sup.Category == c] for c in CATS}
    po_rows, k = [], 1
    for r in dem.itertuples():
        y, m = r.MonthKey // 100, r.MonthKey % 100
        cat = item.at[r.ProductKey - 1, "Category"]
        cs = cat_sups[cat]
        w = np.where(cs.Tier == "Strategic", 2.0, np.where(cs.Tier == "Preferred", 1.3, 0.7))
        sp = cs.iloc[rng.choice(len(cs), p=w / w.sum())]
        n_po = 1 if r.Quantity < 8 else 2
        for j in range(n_po):
            od = pd.Timestamp(year=y, month=m, day=1) - pd.Timedelta(days=int(sp.ContractLeadTimeDays) + int(rng.integers(0, 20)))
            if od < pd.Timestamp("2023-01-01") or od > pd.Timestamp("2025-11-30"):
                continue
            qty = max(1, int(round(r.Quantity / n_po * rng.uniform(0.92, 1.06))))
            promised = od + pd.Timedelta(days=int(sp.ContractLeadTimeDays))
            peak = promised.month in (9, 10)
            p_on = sp._ontime - (0.10 if peak else 0) - (0.04 if sp.Country != "India" and peak else 0)
            on = rng.random() < p_on
            delay = int(rng.integers(-3, 1)) if on else int(rng.integers(1, 6 if sp.Country == "India" else 15))
            infull = rng.random() < sp._infull
            recv_q = qty if infull else max(0, int(qty * rng.uniform(0.5, 0.95)))
            po_rows.append([k, f"PO{400000 + k // 3}", int(od.strftime("%Y%m%d")), promised.date(),
                            (promised + pd.Timedelta(days=delay)).date(), int(sp.SupplierKey), int(r.ProductKey),
                            reg2wh[r.Region], qty, recv_q, round(qty * item.at[r.ProductKey - 1, "UnitCost"], 2)])
            k += 1
    po = pd.DataFrame(po_rows, columns=["POLineKey", "PONumber", "OrderDateKey", "PromisedDate", "ReceivedDate",
                                        "SupplierKey", "ProductKey", "WarehouseKey", "OrderedQty", "ReceivedQty",
                                        "LineValue"]).sort_values("POLineKey")
    # month-end inventory snapshot: cover vs next-month demand; electronics A-class runs thin before festive
    avg = dem.groupby(["Region", "ProductKey"]).Quantity.mean().rename("AvgMonthly").reset_index()
    avg = avg.merge(item, on="ProductKey")
    avg["SafetyStockUnits"] = np.ceil(avg.AvgMonthly * 0.5).astype(int).clip(lower=2)
    snaps = pd.date_range("2023-01-31", "2025-12-31", freq="ME")
    inv_rows = []
    for sd in snaps:
        thin = sd.month in (9, 10)
        for r in avg.itertuples():
            cover = rng.normal(1.3, 0.45)
            if thin and r.Category == "Electronics":
                cover -= 0.45
            inv_rows.append([int(sd.strftime("%Y%m%d")), reg2wh[r.Region], r.ProductKey,
                             int(max(0, round(r.AvgMonthly * cover)))])
    inv = pd.DataFrame(inv_rows, columns=["SnapshotDateKey", "WarehouseKey", "ProductKey", "OnHandUnits"])
    ss = avg[["Region", "ProductKey", "SafetyStockUnits"]].copy()
    ss["WarehouseKey"] = ss.Region.map(reg2wh)
    return sup.drop(columns=["_ontime", "_infull"]), wh, po, inv, ss[["WarehouseKey", "ProductKey", "SafetyStockUnits"]]


if __name__ == "__main__":
    print("Generating data ...")
    date = dim_date(); prod = dim_product(); store = dim_store(); cust = dim_customer()
    for p in (P1, P2, P3):
        out(p, "DimDate.csv", date)
    out(P1, "DimProduct.csv", prod); out(P1, "DimStore.csv", store); out(P1, "DimCustomer.csv", cust)
    clean, raw = retail(date, prod, store, cust)
    out(P1, "FactSales.csv", raw)
    plan = sales_plan(clean, store, prod)
    out(P1, "FactSalesTarget.csv", plan)
    out(P1, "SecurityUserRegion.csv", pd.DataFrame({
        "UserPrincipalName": [f"rm.{r.lower()}@northwind.example" for r in REGIONS] + ["cfo@northwind.example"],
        "Region": list(REGIONS) + ["ALL"]}))
    acc, cc, fin = finance(clean, plan, store, prod)
    out(P2, "DimAccount.csv", acc); out(P2, "DimCostCenter.csv", cc); out(P2, "FactFinance.csv", fin)
    out(P2, "DimScenario.csv", pd.DataFrame({"Scenario": ["Actual", "Budget", "Forecast"], "ScenarioSort": [1, 2, 3]}))
    sup, wh, po, inv, ss = supply(clean, prod)
    out(P3, "DimSupplier.csv", sup); out(P3, "DimWarehouse.csv", wh)
    out(P3, "DimProduct.csv", prod)
    out(P3, "FactPurchaseOrderLine.csv", po); out(P3, "FactInventorySnapshot.csv", inv)
    out(P3, "SafetyStock.csv", ss)
    print("Done.")

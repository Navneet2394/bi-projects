# Data Dictionary · Project 01

| Table | Grain | Key columns | Notes |
|---|---|---|---|
| DimDate | 1 row per day, 2023-01-01 → 2025-12-31 | DateKey (yyyymmdd) | Indian fiscal year (FY24 = Apr-2023 → Mar-2024); `IsFestiveSeason` = October–November |
| DimProduct | 1 row per SKU (180) | ProductKey | 5 categories, 15 sub-categories; `ABCClass` by price (A > ₹20,000, B > ₹3,000) |
| DimStore | 1 row per store (22 physical + 1 online) | StoreKey | Region ∈ North, West, South, East, Online; Format ∈ Flagship, Express, Online |
| DimCustomer | 1 row per customer (6,000) + Unknown (−1) | CustomerKey | Segment, LoyaltyTier (No Tier / Silver / Gold / Platinum), HomeRegion |
| FactSales | 1 row per order line | OrderNumber + LineNumber | SalesAmount = Quantity × UnitPrice × (1 − DiscountPct); `IsReturned` flags full-line returns |
| FactSalesTarget | Month × Store × Category (2024–2025) | MonthStartDate, StoreKey, Category | Plan = prior-year net sales × planned growth (stores 7–10%, online 18%) |
| SecurityUserRegion | User × Region | UserPrincipalName | `ALL` = unrestricted |

## Business rules
- **Net Sales** excludes returned lines; **Gross Sales** includes them.
- **Gross Margin** = Net Sales − cost of non-returned lines.
- **Orders** = distinct OrderNumber. An order has 1–5 lines sharing the same date, store, customer and channel.
- **Active Customers** excludes the Unknown member (guest checkouts).
- Currency: INR.

## Known source issues (handled in Power Query and SQL staging)
| ID | Issue | Rows | Treatment |
|---|---|---:|---|
| DQ-1 | A source batch for 2–3 March 2025 was loaded twice | 207 duplicate lines | Keep one row per `SalesOrderLineKey` |
| DQ-2 | Online guest checkouts have no customer | 420 lines | Map to `CustomerKey = -1` (Unknown) |

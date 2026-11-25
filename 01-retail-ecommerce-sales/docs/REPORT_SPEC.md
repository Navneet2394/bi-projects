# Report specification · Retail & E-commerce Sales

Filters on every page: Year (default 2025), Region, Channel, Category. Currency: ₹ in Cr/L. Theme: `../../04-governance-kit/theme`.
Expected values are for **2025, all filters cleared**; they come from the reconciled KPI set.

## Page 1 · Executive Overview
| Visual | Fields / measures | Expected value |
|---|---|---|
| KPI card | Net Sales + KPI Card Subtitle | ₹34.79 Cr · ▲ 12.7% vs PY |
| KPI card | Target Attainment % | 101.7% |
| KPI card | Gross Margin % | 22.0% |
| KPI card | Return Rate % | 5.2% |
| KPI card | Orders · Average Order Value | 21,515 · ₹16,172 |
| Line chart | YearMonth × Net Sales, Target | Peaks in Oct–Nov each year; no target line in 2023 |
| Bar chart | Region × Target Attainment % (conditional colour) | East 90.3% red; Online 107.0% green |

## Page 2 · Channel & Region
| Visual | Fields / measures | Expected value |
|---|---|---|
| Clustered bar | Channel × Net Sales YoY % | Online +26.2%, Store +9.2% |
| Table | Region: Net Sales, YoY %, Gross Margin %, Effective Discount %, Return Rate % | East −2.5% YoY, 19.9% margin |
| Scatter | Region: Effective Discount % (x) vs Gross Margin % (y), size = Net Sales | East and Online bottom-right |

## Page 3 · Category & Product
| Visual | Fields / measures | Expected value |
|---|---|---|
| Combo chart | Category: Net Sales (bars), Gross Margin % (line) | Electronics 47.0% share / 10.8%; Fashion 44.7% |
| 100% bar | Category share of Net Sales vs share of Gross Margin | Electronics 47.0% vs 23.2% |
| Decomposition tree | Gross Margin by Category → SubCategory → Brand | |
| Pareto | Product Rank, Cumulative Sales %, ABC Class | |

## Page 4 · Target Tracker (RLS-filtered)
| Visual | Fields / measures | Expected value |
|---|---|---|
| Matrix | Region / Store × Month: Net Sales, Target, Target Gap, Target Status Colour | Region totals: East 90.3%, North 106.4%, Online 107.0%, South 98.9%, West 102.2% |

## Page 5 · Discounts & Returns
| Visual | Fields / measures | Expected value |
|---|---|---|
| Column chart | FactSales[DiscountPct] × Gross Margin % | 0%: 27.1%, 5%: 23.7%, 10%: 19.5%, 15%: 14.9%, 20%: 9.5% |
| Bar chart | Category × Return Rate % (split by Channel) | Fashion 13.0% online / 8.9% store |

## Page 6 · Customers
| Visual | Fields / measures | Expected value |
|---|---|---|
| Table | Segment: Net Sales, Average Order Value, Gross Margin % | Corporate ₹30,102 / 24.6% |
| Bar chart | LoyaltyTier × orders per customer (Orders ÷ Active Customers) | Platinum 10.3, No Tier 2.7 (exclude Unknown) |

## Drill-through and tooltips
- **Store detail** drill-through (from any store or region visual): monthly trend vs target, category mix, discount and return rate.
- **Report-page tooltip** on regions: 12-month net sales sparkline and attainment.

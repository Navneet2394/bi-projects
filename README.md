# BI Projects · Navneet Shubham

Three connected Power BI projects for one fictional Indian omni-channel retailer, *Northwind Omni Retail*.
Together they show how I take a business problem from raw data to a decision: SQL and Power Query for data
preparation, a star-schema model, DAX, security, and reports that answer specific stakeholder questions.

**▶ Live interactive dashboards:** https://navneet2394.github.io/bi-projects/
**Portfolio:** https://navneet2394.github.io · **LinkedIn:** [linkedin.com/in/navneet1994](https://www.linkedin.com/in/navneet1994)

| # | Project | Business question | Headline finding | Live |
|---|---|---|---|---|
| 01 | [Retail & E-commerce Sales](01-retail-ecommerce-sales/) | Is our growth profitable, and where is margin lost? | Sales +12.7% and 101.7% of plan, but margin flat at 22.0%: growth comes from discounted online sales and low-margin electronics; East misses plan | [Open](https://navneet2394.github.io/bi-projects/#retail) |
| 02 | [Finance P&L: Budget vs Actual](02-finance-pnl-budget-variance/) | Are we on budget, and why not? | Revenue +1.7% vs budget, yet net income −6.4%: returns, product margin and the festive campaign | [Open](https://navneet2394.github.io/bi-projects/#finance) |
| 03 | [Procurement & Supply Chain OTIF](03-procurement-supply-chain-otif/) | Which suppliers put the shelves at risk? | OTIF 80.9% vs 90% target; transactional and import suppliers slip before the festive peak | [Open](https://navneet2394.github.io/bi-projects/#supply) |
| 04 | [BI Governance Kit](04-governance-kit/) | How should a BI team build and release reports? | Standards, release flow, performance checklist, report theme | n/a |

## How the projects connect
```
Order lines (01) ──► Revenue, returns and COGS in the P&L (02)
Sales plan  (01) ──► Revenue and COGS budget (02)
Products    (01) ──► Purchase orders and inventory (03)
```
The same company, products and transactions run through all three, so a regional sales problem in Project 01
also shows up in the P&L in Project 02.

## Inside each project
```
<project>/
├── README.md     Business context, stakeholders, findings, recommendations, model, reconciliation
├── data/         CSV extracts (raw, including the source issues that get cleaned)
├── sql/          SQL Server DDL, views, staging and reconciliation queries
├── powerquery/   Power Query (M): parameterised loads, cleaning, incremental refresh
├── dax/          Measure library grouped by display folder
└── docs/         REPORT_SPEC.md (page-by-page visuals and expected values), build and security notes
```
Every figure quoted in the READMEs is reconciled three ways: DAX, SQL, and an independent Python
calculation (`scripts/compute_kpis.py`).

## Reproducing the data
```bash
pip install pandas numpy
python scripts/generate_data.py        # rebuilds every CSV (deterministic)
python scripts/compute_kpis.py         # independent KPI calculation for reconciliation
python scripts/build_showcase_data.py  # refreshes the live dashboard data in docs/
```

## Tech
Power BI Desktop & Service · DAX · Power Query (M) · SQL Server · Python (pandas) · Git

## Data note
All companies, people and figures are fictional (synthetic data, INR). No employer or client data is used anywhere.

## Licence
MIT. See [LICENSE](LICENSE).

# Build & Deployment Guide · Project 01

> The model is kept as text sources (M, DAX, SQL) rather than a binary `.pbix`, so every change is reviewable in Git.
> The report is saved as a **Power BI Project (.pbip)**, which stores the model (TMDL) and report (PBIR) as text.
> These steps reproduce the report from scratch, e.g. for a new environment or a code review.

## 1. Load data (10 min)
1. Home › Transform data › Manage Parameters › New: `pDataFolder` (Text) = full path to `data\` **ending with a backslash**.
2. New Blank Query › Advanced Editor › paste `fnLoadCsv` from `powerquery/queries.pq`; name it `fnLoadCsv`.
3. Create one blank query per table (DimDate, DimProduct, DimStore, DimCustomer, FactSales, FactSalesTarget, SecurityUserRegion) and paste the matching block.
4. Disable load for `fnLoadCsv`. Close & Apply.

## 2. Model (10 min)
| From (many) | To (one) | Cardinality | Filter direction |
|---|---|---|---|
| FactSales[OrderDateKey] | DimDate[DateKey] | *:1 | Single |
| FactSales[ProductKey] | DimProduct[ProductKey] | *:1 | Single |
| FactSales[StoreKey] | DimStore[StoreKey] | *:1 | Single |
| FactSales[CustomerKey] | DimCustomer[CustomerKey] | *:1 | Single |
| FactSalesTarget[MonthStartDate] | DimDate[Date] | *:1 | Single |
| FactSalesTarget[StoreKey] | DimStore[StoreKey] | *:1 | Single |

- `SecurityUserRegion` stays **disconnected** (used only inside the RLS expression).
- Table tools › **Mark as date table** › DimDate[Date].
- Sort `DimDate[Month]` by `MonthNo`; hide all key columns; set `DimStore[City]` Data category = City.
- Create table `_Measures` (Enter data, one dummy column; delete the column after adding measures).

## 3. Measures (15 min)
**Option A (manual):** copy each measure from `dax/measures.dax`.
**Option B (Tabular Editor 2, free):** External Tools › Tabular Editor › C# Script:
```csharp
// Paste measure blocks as name|expression lines into a file first, or add one by one:
var t = Model.Tables["_Measures"];
t.AddMeasure("Gross Sales", "SUM ( FactSales[SalesAmount] )", "1 Base");
// ...repeat; set FormatString e.g. m.FormatString = "#,0";
```
Formats: currency measures `#,0`, % measures `0.0%`.

Also create:
- **Top N parameter:** Modeling › New parameter › Numeric range, name `TopN`, 5–25, step 5, default 10.
- **MetricSelector table:** Modeling › New table, then paste the `DATATABLE` expression in the comment above `[Selected Metric]`.

## 4. Report (30–45 min)
Follow the page-by-page specification in `REPORT_SPEC.md`. Design details applied:
- Import the theme `../04-governance-kit/theme/northwind-corporate.json` (View › Themes › Browse).
- Use **bookmarks** for a chart/table toggle, **field parameters** for axis switching, a **drill-through** Store page and a **report-page tooltip**.
- Conditional formatting using `[Target Status Colour]` (Format › Cell elements › Field value).
- Add alt text to every visual and set a logical tab order (Accessibility).
- Turn on **Performance Analyzer** and keep every visual under 500 ms.

## 5. Validate
Compare every card with the expected values in `REPORT_SPEC.md` and the reconciliation table in `README.md` (or run `sql/02_validation_queries.sql`).

## 6. Publish
1. Set up RLS (see `RLS.md`) and test with *View as*.
2. Publish to a workspace (Pro or PPU is enough). Configure scheduled refresh; for CSV on a PC you need an on-premises gateway. Use the SharePoint variant of `fnLoadCsv` to avoid one.
3. Public sharing via **Publish to web** is appropriate only for synthetic data such as this, and only where the tenant admin allows it. It must never be used for company data.

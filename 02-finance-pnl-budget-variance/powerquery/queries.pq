// Project 02 · Power Query (M). Same pattern as Project 01: create pDataFolder + fnLoadCsv first.

// ---------- FactFinance ----------
let
    Source = fnLoadCsv("FactFinance.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"DateKey", Int64.Type}, {"AccountKey", Int64.Type}, {"CostCenterKey", Int64.Type},
        {"Scenario", type text}, {"Amount", Currency.Type}}, "en-US")
in
    Typed

// ---------- DimAccount ----------
let
    Source = fnLoadCsv("DimAccount.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"AccountKey", Int64.Type}, {"AccountName", type text}, {"AccountGroup", type text},
        {"GroupSort", Int64.Type}, {"PnLSign", Int64.Type}, {"NaturalSign", Int64.Type}})
in
    Typed

// ---------- DimCostCenter ----------
let
    Source = fnLoadCsv("DimCostCenter.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"CostCenterKey", Int64.Type}, {"CostCenter", type text}, {"Region", type text},
        {"Division", type text}, {"Owner", type text}})
in
    Typed

// ---------- DimScenario ----------
let
    Source = fnLoadCsv("DimScenario.csv"),
    Typed  = Table.TransformColumnTypes(Source, {{"Scenario", type text}, {"ScenarioSort", Int64.Type}})
in
    Typed

// ---------- DimDate: reuse the Project 01 query (same CSV) ----------

// ---------- PnLLayout (disconnected, defined in M so it is documented & versioned) ----------
let
    Source = #table(
        type table [LineSort = Int64.Type, Line = text, LineType = text, GroupSort = Int64.Type],
        {
            {1, "Revenue", "Group", 1},
            {2, "COGS", "Group", 2},
            {3, "Gross Profit", "Subtotal", 2},
            {4, "Operating Expenses", "Group", 3},
            {5, "EBITDA", "Subtotal", 3},
            {6, "D&A", "Group", 4},
            {7, "EBIT", "Subtotal", 4},
            {8, "Finance Cost", "Group", 5},
            {9, "Profit Before Tax", "Subtotal", 5},
            {10, "Tax", "Group", 6},
            {11, "Net Income", "Subtotal", 6}
        })
in
    Source

// ---------- Budget upload pattern: Excel template from finance team (wide → long) ----------
// Finance usually sends budgets as a wide sheet: Account | CostCenter | Jan | Feb | ... | Dec
let
    Source   = Excel.Workbook(File.Contents(pBudgetFile), null, true),
    Sheet    = Source{[Item = "Budget", Kind = "Sheet"]}[Data],
    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars = true]),
    Unpivot  = Table.UnpivotOtherColumns(Promoted, {"AccountKey", "CostCenterKey"}, "Month", "Amount"),
    WithDate = Table.AddColumn(Unpivot, "DateKey", each
                  Number.From(Text.From(pBudgetYear) &
                  Text.PadStart(Text.From(Date.Month(Date.FromText("1 " & [Month] & " 2000"))), 2, "0") & "01"),
                  Int64.Type),
    Scenario = Table.AddColumn(WithDate, "Scenario", each "Budget", type text),
    Result   = Table.SelectColumns(Scenario, {"DateKey", "AccountKey", "CostCenterKey", "Scenario", "Amount"})
in
    Result

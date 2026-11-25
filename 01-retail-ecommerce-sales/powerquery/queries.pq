// =====================================================================
//  Project 01 · Power Query (M) · Parameterised, foldable-where-possible
//  1) Create a text parameter  pDataFolder  =  "C:\bi-projects\01-retail-ecommerce-sales\data\"
//     (or a SharePoint/OneDrive folder URL; see the SharePoint variant at the end)
//  2) Blank Query > Advanced Editor > paste one query per section.
//  When the source is SQL Server (sql/01_schema.sql), switch to the
//  SQL variants; they fold fully, so incremental refresh works.
// =====================================================================

// ---------- fnLoadCsv (function, reused by every table) ----------
(fileName as text) as table =>
let
    Source   = Csv.Document(File.Contents(pDataFolder & fileName),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
in
    Promoted

// ---------- DimDate ----------
let
    Source = fnLoadCsv("DimDate.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"DateKey", Int64.Type}, {"Date", type date}, {"Year", Int64.Type},
        {"Quarter", type text}, {"MonthNo", Int64.Type}, {"Month", type text},
        {"YearMonth", type text}, {"WeekdayNo", Int64.Type}, {"Weekday", type text},
        {"IsWeekend", type logical}, {"FiscalYear", type text}, {"IsFestiveSeason", type logical}}, "en-US")
in
    Typed

// ---------- DimProduct ----------
let
    Source = fnLoadCsv("DimProduct.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"ProductKey", Int64.Type}, {"SKU", type text}, {"ProductName", type text},
        {"SubCategory", type text}, {"Category", type text}, {"Brand", type text},
        {"ListPrice", Currency.Type}, {"UnitCost", Currency.Type}, {"ABCClass", type text}}, "en-US"),
    Trimmed = Table.TransformColumns(Typed, {{"ProductName", Text.Trim, type text}})
in
    Trimmed

// ---------- DimStore ----------
let
    Source = fnLoadCsv("DimStore.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"StoreKey", Int64.Type}, {"StoreCode", type text}, {"StoreName", type text},
        {"City", type text}, {"Region", type text}, {"Format", type text},
        {"OpenDate", type date}, {"RegionalManagerEmail", type text}}, "en-US")
in
    Typed

// ---------- DimCustomer ----------
let
    Source = fnLoadCsv("DimCustomer.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"CustomerKey", Int64.Type}, {"CustomerCode", type text}, {"Segment", type text},
        {"LoyaltyTier", type text}, {"HomeRegion", type text}, {"SignupDate", type date}}, "en-US")
    // The source already holds an "Unknown" member (CustomerKey = -1) for guest checkouts
in
    Typed

// ---------- FactSales ----------
let
    Source = fnLoadCsv("FactSales.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"SalesOrderLineKey", Int64.Type}, {"OrderNumber", type text}, {"LineNumber", Int64.Type}, {"OrderDateKey", Int64.Type},
        {"ProductKey", Int64.Type}, {"StoreKey", Int64.Type}, {"CustomerKey", Int64.Type},
        {"Channel", type text}, {"Quantity", Int64.Type}, {"UnitPrice", Currency.Type},
        {"DiscountPct", type number}, {"SalesAmount", Currency.Type}, {"CostAmount", Currency.Type},
        {"IsReturned", type logical}}, "en-US"),
    // DQ-1: a source batch (2-3 Mar 2025) was loaded twice -> keep one row per line key
    Deduped = Table.Distinct(Typed, {"SalesOrderLineKey"}),
    // DQ-2: online guest checkouts arrive without a customer -> map to the Unknown member (-1)
    CustomerFixed = Table.ReplaceValue(Deduped, null, -1, Replacer.ReplaceValue, {"CustomerKey"}),
    // The line key is high-cardinality and not needed after de-duplication (smaller VertiPaq model)
    Slim = Table.RemoveColumns(CustomerFixed, {"SalesOrderLineKey"})
in
    Slim

// ---------- FactSalesTarget ----------
let
    Source = fnLoadCsv("FactSalesTarget.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"MonthStartDate", type date}, {"StoreKey", Int64.Type},
        {"Category", type text}, {"TargetAmount", Currency.Type}}, "en-US")
in
    Typed

// ---------- SecurityUserRegion ----------
let
    Source = fnLoadCsv("SecurityUserRegion.csv"),
    Typed  = Table.TransformColumnTypes(Source, {{"UserPrincipalName", type text}, {"Region", type text}}),
    Lower  = Table.TransformColumns(Typed, {{"UserPrincipalName", Text.Lower, type text}})
in
    Lower

// =====================================================================
//  SQL SERVER VARIANT (query folding + incremental refresh)
//  Create DateTime parameters RangeStart / RangeEnd (exact names, type DateTime)
// =====================================================================
// ---------- FactSales (SQL, incremental) ----------
let
    Source = Sql.Database(pServer, pDatabase),
    Fact   = Source{[Schema = "dw", Item = "FactSales"]}[Data],
    // Filter on an integer key so the predicate folds to the source
    Filtered = Table.SelectRows(Fact, each
        [OrderDateKey] >= Number.From(DateTime.ToText(RangeStart, "yyyyMMdd")) and
        [OrderDateKey] <  Number.From(DateTime.ToText(RangeEnd,   "yyyyMMdd")))
in
    Filtered
// Verify folding: right-click the last step > "View Native Query" must be enabled.
// Incremental refresh policy: store 3 years, refresh last 7 days, detect changes off.

// =====================================================================
//  SHAREPOINT / ONEDRIVE VARIANT of fnLoadCsv (no gateway needed)
// =====================================================================
(fileName as text) as table =>
let
    Site   = SharePoint.Files(pSharePointSite, [ApiVersion = 15]),
    File   = Table.SelectRows(Site, each [Name] = fileName and Text.Contains([Folder Path], pFolderName)){0}[Content],
    Csv    = Csv.Document(File, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Csv, [PromoteAllScalars = true])
in
    Promoted

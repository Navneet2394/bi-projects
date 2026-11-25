// =====================================================================
//  Project 03 · Procurement & Supply Chain · Power Query (M)
//  Create the text parameter pDataFolder (path to this project's \data\ folder, ending with "\")
//  and the helper function fnLoadCsv exactly as in Project 01.
// =====================================================================

// ---------- FactPurchaseOrderLine (delivery flags derived here, not in DAX) ----------
let
    Source = fnLoadCsv("FactPurchaseOrderLine.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"POLineKey", Int64.Type}, {"PONumber", type text}, {"OrderDateKey", Int64.Type},
        {"PromisedDate", type date}, {"ReceivedDate", type date}, {"SupplierKey", Int64.Type},
        {"ProductKey", Int64.Type}, {"WarehouseKey", Int64.Type}, {"OrderedQty", Int64.Type},
        {"ReceivedQty", Int64.Type}, {"LineValue", Currency.Type}}, "en-US"),
    OnTime = Table.AddColumn(Typed, "IsOnTime", each [ReceivedDate] <= [PromisedDate], type logical),
    InFull = Table.AddColumn(OnTime, "IsInFull", each [ReceivedQty] >= [OrderedQty], type logical),
    Late   = Table.AddColumn(InFull, "DaysLate", each
                List.Max({0, Duration.Days([ReceivedDate] - [PromisedDate])}), Int64.Type),
    Slim   = Table.RemoveColumns(Late, {"POLineKey"})
in
    Slim

// ---------- FactInventorySnapshot (safety stock is per warehouse x product, so it is merged onto the snapshot) ----------
let
    Source = fnLoadCsv("FactInventorySnapshot.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"SnapshotDateKey", Int64.Type}, {"WarehouseKey", Int64.Type},
        {"ProductKey", Int64.Type}, {"OnHandUnits", Int64.Type}}),
    Safety = Table.TransformColumnTypes(fnLoadCsv("SafetyStock.csv"), {
        {"WarehouseKey", Int64.Type}, {"ProductKey", Int64.Type}, {"SafetyStockUnits", Int64.Type}}),
    Merged = Table.NestedJoin(Typed, {"WarehouseKey", "ProductKey"}, Safety, {"WarehouseKey", "ProductKey"},
                              "SS", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "SS", {"SafetyStockUnits"}),
    BelowFlag = Table.AddColumn(Expanded, "IsBelowSafetyStock",
                each [OnHandUnits] < [SafetyStockUnits], type logical)
in
    BelowFlag

// ---------- DimSupplier ----------
let
    Source = fnLoadCsv("DimSupplier.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"SupplierKey", Int64.Type}, {"SupplierName", type text}, {"Country", type text},
        {"Category", type text}, {"Tier", type text}, {"ContractLeadTimeDays", Int64.Type}}),
    Sourcing = Table.AddColumn(Typed, "Sourcing", each if [Country] = "India" then "Domestic" else "Import", type text)
in
    Sourcing

// ---------- DimProduct (same product master as Project 01) ----------
let
    Source = fnLoadCsv("DimProduct.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"ProductKey", Int64.Type}, {"SKU", type text}, {"ProductName", type text},
        {"SubCategory", type text}, {"Category", type text}, {"Brand", type text},
        {"ListPrice", Currency.Type}, {"UnitCost", Currency.Type}, {"ABCClass", type text}}, "en-US")
in
    Typed

// ---------- DimWarehouse ----------
let
    Source = fnLoadCsv("DimWarehouse.csv"),
    Typed  = Table.TransformColumnTypes(Source, {
        {"WarehouseKey", Int64.Type}, {"Warehouse", type text}, {"Region", type text}, {"CapacityUnits", Int64.Type}})
in
    Typed

// ---------- DimDate: same query as Project 01 ----------

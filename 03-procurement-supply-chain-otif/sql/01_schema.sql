/* =====================================================================
   Project 03 · Procurement & Supply Chain · SQL Server / Azure SQL
   ===================================================================== */
IF SCHEMA_ID('scm') IS NULL EXEC('CREATE SCHEMA scm');
GO
CREATE TABLE scm.DimSupplier (
    SupplierKey INT PRIMARY KEY, SupplierName NVARCHAR(80) NOT NULL, Country NVARCHAR(40) NOT NULL,
    Category NVARCHAR(30) NOT NULL, Tier NVARCHAR(20) NOT NULL, ContractLeadTimeDays INT NOT NULL);
CREATE TABLE scm.DimWarehouse (
    WarehouseKey INT PRIMARY KEY, Warehouse NVARCHAR(40) NOT NULL, Region NVARCHAR(20) NOT NULL, CapacityUnits INT NOT NULL);
CREATE TABLE scm.DimProduct (                    -- same product master as Project 01
    ProductKey INT PRIMARY KEY, SKU VARCHAR(10) NOT NULL, ProductName NVARCHAR(100) NOT NULL,
    SubCategory NVARCHAR(50) NOT NULL, Category NVARCHAR(50) NOT NULL, Brand NVARCHAR(50) NOT NULL,
    ListPrice DECIMAL(12,2) NOT NULL, UnitCost DECIMAL(12,2) NOT NULL, ABCClass CHAR(1) NOT NULL);
CREATE TABLE scm.FactPurchaseOrderLine (
    POLineKey BIGINT PRIMARY KEY NONCLUSTERED, PONumber VARCHAR(12) NOT NULL, OrderDateKey INT NOT NULL,
    PromisedDate DATE NOT NULL, ReceivedDate DATE NULL,
    SupplierKey INT NOT NULL REFERENCES scm.DimSupplier(SupplierKey),
    ProductKey INT NOT NULL REFERENCES scm.DimProduct(ProductKey),
    WarehouseKey INT NOT NULL REFERENCES scm.DimWarehouse(WarehouseKey),
    OrderedQty INT NOT NULL, ReceivedQty INT NOT NULL, LineValue DECIMAL(14,2) NOT NULL);
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactPOL ON scm.FactPurchaseOrderLine;
CREATE TABLE scm.SafetyStock (
    WarehouseKey INT NOT NULL, ProductKey INT NOT NULL, SafetyStockUnits INT NOT NULL,
    CONSTRAINT PK_SafetyStock PRIMARY KEY (WarehouseKey, ProductKey));
CREATE TABLE scm.FactInventorySnapshot (
    SnapshotDateKey INT NOT NULL, WarehouseKey INT NOT NULL, ProductKey INT NOT NULL, OnHandUnits INT NOT NULL,
    CONSTRAINT PK_InvSnap PRIMARY KEY (SnapshotDateKey, WarehouseKey, ProductKey));
GO

/* Reporting view: delivery logic is defined once, upstream of Power BI */
CREATE OR ALTER VIEW scm.vPurchaseOrderLine AS
SELECT  f.*,
        CAST(CASE WHEN f.ReceivedDate <= f.PromisedDate THEN 1 ELSE 0 END AS BIT) AS IsOnTime,
        CAST(CASE WHEN f.ReceivedQty >= f.OrderedQty    THEN 1 ELSE 0 END AS BIT) AS IsInFull,
        CASE WHEN DATEDIFF(DAY, f.PromisedDate, f.ReceivedDate) > 0
             THEN DATEDIFF(DAY, f.PromisedDate, f.ReceivedDate) ELSE 0 END          AS DaysLate
FROM    scm.FactPurchaseOrderLine f;
GO

/* Reconciliation 1: OTIF by order year (README: 80.9% / 80.7% / 80.9%) */
SELECT  OrderDateKey / 10000 AS [Year], COUNT(*) AS Lines,
        AVG(CAST(IsOnTime AS FLOAT)) AS OnTimePct,
        AVG(CAST(IsInFull AS FLOAT)) AS InFullPct,
        AVG(CASE WHEN IsOnTime = 1 AND IsInFull = 1 THEN 1.0 ELSE 0.0 END) AS OTIFPct
FROM    scm.vPurchaseOrderLine
GROUP BY OrderDateKey / 10000
ORDER BY [Year];

/* Reconciliation 2: 2025 OTIF by supplier tier and by sourcing */
SELECT  s.Tier, CASE WHEN s.Country = 'India' THEN 'Domestic' ELSE 'Import' END AS Sourcing,
        COUNT(*) AS Lines,
        AVG(CASE WHEN v.IsOnTime = 1 AND v.IsInFull = 1 THEN 1.0 ELSE 0.0 END) AS OTIFPct
FROM    scm.vPurchaseOrderLine v
JOIN    scm.DimSupplier s ON s.SupplierKey = v.SupplierKey
WHERE   v.OrderDateKey BETWEEN 20250101 AND 20251231
GROUP BY ROLLUP (s.Tier, CASE WHEN s.Country = 'India' THEN 'Domestic' ELSE 'Import' END);

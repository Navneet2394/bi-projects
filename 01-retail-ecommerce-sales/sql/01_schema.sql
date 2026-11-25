/* =====================================================================
   Project 01 · Retail Sales · SQL Server / Azure SQL star schema
   Load the CSVs with BULK INSERT (below), the SSMS Import Flat File wizard,
   or Azure Data Factory. Tested syntax target: SQL Server 2019+ / Azure SQL.
   ===================================================================== */
IF SCHEMA_ID('dw') IS NULL EXEC('CREATE SCHEMA dw');
GO

CREATE TABLE dw.DimDate (
    DateKey      INT          NOT NULL PRIMARY KEY,
    [Date]       DATE         NOT NULL,
    [Year]       SMALLINT     NOT NULL,
    [Quarter]    CHAR(2)      NOT NULL,
    MonthNo      TINYINT      NOT NULL,
    [Month]      CHAR(3)      NOT NULL,
    YearMonth    CHAR(7)      NOT NULL,
    WeekdayNo    TINYINT      NOT NULL,
    [Weekday]    CHAR(3)      NOT NULL,
    IsWeekend    BIT          NOT NULL,
    FiscalYear   CHAR(4)      NOT NULL,
    IsFestiveSeason BIT       NOT NULL
);

CREATE TABLE dw.DimProduct (
    ProductKey   INT           NOT NULL PRIMARY KEY,
    SKU          VARCHAR(20)   NOT NULL,
    ProductName  NVARCHAR(100) NOT NULL,
    SubCategory  NVARCHAR(50)  NOT NULL,
    Category     NVARCHAR(50)  NOT NULL,
    Brand        NVARCHAR(50)  NOT NULL,
    ListPrice    DECIMAL(12,2) NOT NULL,
    UnitCost     DECIMAL(12,2) NOT NULL,
    ABCClass     CHAR(1)       NOT NULL
);

CREATE TABLE dw.DimStore (
    StoreKey     INT           NOT NULL PRIMARY KEY,
    StoreCode    VARCHAR(10)   NOT NULL,
    StoreName    NVARCHAR(100) NOT NULL,
    City         NVARCHAR(50)  NOT NULL,
    Region       NVARCHAR(20)  NOT NULL,
    [Format]     NVARCHAR(20)  NOT NULL,
    OpenDate     DATE          NOT NULL,
    RegionalManagerEmail NVARCHAR(100) NOT NULL
);

CREATE TABLE dw.DimCustomer (
    CustomerKey  INT          NOT NULL PRIMARY KEY,
    CustomerCode VARCHAR(10)  NOT NULL,
    Segment      NVARCHAR(30) NOT NULL,
    LoyaltyTier  NVARCHAR(20) NOT NULL,
    HomeRegion   NVARCHAR(20) NOT NULL,
    SignupDate   DATE         NULL
);

CREATE TABLE dw.FactSales (
    SalesOrderLineKey BIGINT        NOT NULL PRIMARY KEY NONCLUSTERED,
    OrderNumber       VARCHAR(12)   NOT NULL,
    LineNumber        TINYINT       NOT NULL,
    OrderDateKey      INT           NOT NULL REFERENCES dw.DimDate(DateKey),
    ProductKey        INT           NOT NULL REFERENCES dw.DimProduct(ProductKey),
    StoreKey          INT           NOT NULL REFERENCES dw.DimStore(StoreKey),
    CustomerKey       INT           NOT NULL REFERENCES dw.DimCustomer(CustomerKey),
    Channel           VARCHAR(10)   NOT NULL,
    Quantity          INT           NOT NULL,
    UnitPrice         DECIMAL(12,2) NOT NULL,
    DiscountPct       DECIMAL(5,2)  NOT NULL,
    SalesAmount       DECIMAL(14,2) NOT NULL,
    CostAmount        DECIMAL(14,2) NOT NULL,
    IsReturned        BIT           NOT NULL
);
-- Columnstore: best fit for analytic scans and DirectQuery/composite models
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactSales ON dw.FactSales;

CREATE TABLE dw.FactSalesTarget (
    MonthStartDate DATE          NOT NULL,
    StoreKey       INT           NOT NULL REFERENCES dw.DimStore(StoreKey),
    Category       NVARCHAR(50)  NOT NULL,
    TargetAmount   DECIMAL(14,2) NOT NULL,
    CONSTRAINT PK_FactSalesTarget PRIMARY KEY (MonthStartDate, StoreKey, Category)
);

CREATE TABLE dw.SecurityUserRegion (
    UserPrincipalName NVARCHAR(100) NOT NULL,
    Region            NVARCHAR(20)  NOT NULL
);
GO

/* ---------- Load (adjust path; file must be readable by the SQL Server service) ---------- */
-- BULK INSERT dw.DimDate     FROM 'C:\bi-projects\01-retail-ecommerce-sales\data\DimDate.csv'     WITH (FORMAT='CSV', FIRSTROW=2);
-- BULK INSERT dw.DimProduct  FROM 'C:\bi-projects\01-retail-ecommerce-sales\data\DimProduct.csv'  WITH (FORMAT='CSV', FIRSTROW=2);
-- BULK INSERT dw.DimStore    FROM 'C:\bi-projects\01-retail-ecommerce-sales\data\DimStore.csv'    WITH (FORMAT='CSV', FIRSTROW=2);
-- BULK INSERT dw.DimCustomer FROM 'C:\bi-projects\01-retail-ecommerce-sales\data\DimCustomer.csv' WITH (FORMAT='CSV', FIRSTROW=2);
-- BULK INSERT dw.FactSales   FROM 'C:\bi-projects\01-retail-ecommerce-sales\data\FactSales.csv'   WITH (FORMAT='CSV', FIRSTROW=2);
-- BULK INSERT dw.FactSalesTarget FROM '...\FactSalesTarget.csv' WITH (FORMAT='CSV', FIRSTROW=2);
-- BULK INSERT dw.SecurityUserRegion FROM '...\SecurityUserRegion.csv' WITH (FORMAT='CSV', FIRSTROW=2);
-- FactSales.csv is a raw extract: load it into a staging table first, then
--   INSERT dw.FactSales SELECT DISTINCT ... FROM stg.FactSales   (removes the double-loaded batch)
--   and set CustomerKey = -1 where it is NULL (guest checkout).
-- Note: CSV booleans are "True"/"False". If BULK INSERT rejects them into BIT,
-- stage into NVARCHAR columns first and convert with CASE WHEN x='True' THEN 1 ELSE 0 END.

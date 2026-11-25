/* Reconciliation queries: the Power BI numbers must match these.
   (Reference values are also in scripts/kpi_reference.json.) */

-- 1. Net sales, gross margin %, return rate by year
SELECT  d.[Year],
        SUM(f.SalesAmount)                                              AS GrossSales,
        SUM(CASE WHEN f.IsReturned = 0 THEN f.SalesAmount ELSE 0 END)  AS NetSales,
        1 - SUM(CASE WHEN f.IsReturned = 0 THEN f.CostAmount ELSE 0 END)
          / NULLIF(SUM(CASE WHEN f.IsReturned = 0 THEN f.SalesAmount ELSE 0 END), 0) AS GrossMarginPct,
        SUM(CASE WHEN f.IsReturned = 1 THEN f.SalesAmount ELSE 0 END)
          / NULLIF(SUM(f.SalesAmount), 0)                               AS ReturnRatePct,
        COUNT(DISTINCT f.OrderNumber)                                   AS Orders
FROM    dw.FactSales f
JOIN    dw.DimDate d ON d.DateKey = f.OrderDateKey
GROUP BY d.[Year]
ORDER BY d.[Year];

-- 1b. Data-quality checks on the staging extract (expected: 207 duplicate lines, 420 lines without customer)
-- SELECT COUNT(*) - COUNT(DISTINCT SalesOrderLineKey) AS DuplicateLines FROM stg.FactSales;
-- SELECT COUNT(*) AS LinesWithoutCustomer FROM stg.FactSales WHERE CustomerKey IS NULL;

-- 2. Orphan check (should return 0 rows for every dimension)
SELECT 'Product' AS Dim, COUNT(*) AS Orphans FROM dw.FactSales f
LEFT JOIN dw.DimProduct p ON p.ProductKey = f.ProductKey WHERE p.ProductKey IS NULL
UNION ALL
SELECT 'Store', COUNT(*) FROM dw.FactSales f
LEFT JOIN dw.DimStore s ON s.StoreKey = f.StoreKey WHERE s.StoreKey IS NULL
UNION ALL
SELECT 'Customer', COUNT(*) FROM dw.FactSales f
LEFT JOIN dw.DimCustomer c ON c.CustomerKey = f.CustomerKey WHERE c.CustomerKey IS NULL;

-- 3. Target attainment by region, 2025
WITH s AS (
    SELECT st.Region, SUM(CASE WHEN f.IsReturned = 0 THEN f.SalesAmount ELSE 0 END) AS NetSales
    FROM dw.FactSales f
    JOIN dw.DimStore st ON st.StoreKey = f.StoreKey
    WHERE f.OrderDateKey BETWEEN 20250101 AND 20251231
    GROUP BY st.Region),
t AS (
    SELECT st.Region, SUM(t.TargetAmount) AS TargetAmount
    FROM dw.FactSalesTarget t
    JOIN dw.DimStore st ON st.StoreKey = t.StoreKey
    WHERE t.MonthStartDate BETWEEN '2025-01-01' AND '2025-12-31'
    GROUP BY st.Region)
SELECT s.Region, s.NetSales, t.TargetAmount, s.NetSales / NULLIF(t.TargetAmount, 0) AS Attainment
FROM s JOIN t ON t.Region = s.Region
ORDER BY Attainment DESC;

/* Project 02 · Finance star schema (SQL Server / Azure SQL) */
IF SCHEMA_ID('fin') IS NULL EXEC('CREATE SCHEMA fin');
GO
CREATE TABLE fin.DimAccount (
    AccountKey   INT          NOT NULL PRIMARY KEY,
    AccountName  NVARCHAR(60) NOT NULL,
    AccountGroup NVARCHAR(40) NOT NULL,
    GroupSort    TINYINT      NOT NULL,
    PnLSign      SMALLINT     NOT NULL,   -- +1 revenue, -1 cost
    NaturalSign  SMALLINT     NOT NULL    -- -1 for contra accounts (returns)
);
CREATE TABLE fin.DimCostCenter (
    CostCenterKey INT          NOT NULL PRIMARY KEY,
    CostCenter    NVARCHAR(60) NOT NULL,
    Region        NVARCHAR(20) NULL,       -- links retail cost centres to the sales regions
    Division      NVARCHAR(30) NOT NULL,
    [Owner]       NVARCHAR(60) NOT NULL
);
CREATE TABLE fin.DimScenario (
    Scenario     VARCHAR(10) NOT NULL PRIMARY KEY,
    ScenarioSort TINYINT     NOT NULL
);
CREATE TABLE fin.FactFinance (
    DateKey       INT           NOT NULL,   -- first day of month, yyyymmdd
    AccountKey    INT           NOT NULL REFERENCES fin.DimAccount(AccountKey),
    CostCenterKey INT           NOT NULL REFERENCES fin.DimCostCenter(CostCenterKey),
    Scenario      VARCHAR(10)   NOT NULL REFERENCES fin.DimScenario(Scenario),
    Amount        DECIMAL(16,2) NOT NULL
);
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactFinance ON fin.FactFinance;
GO

/* Reconciliation: 2025 P&L by group and scenario (matches the README P&L table) */
SELECT a.GroupSort, a.AccountGroup, f.Scenario,
       SUM(f.Amount * a.PnLSign * a.NaturalSign) AS SignedAmount
FROM   fin.FactFinance f
JOIN   fin.DimAccount  a ON a.AccountKey = f.AccountKey
WHERE  f.DateKey BETWEEN 20250101 AND 20251231
GROUP BY a.GroupSort, a.AccountGroup, f.Scenario
ORDER BY a.GroupSort, f.Scenario;

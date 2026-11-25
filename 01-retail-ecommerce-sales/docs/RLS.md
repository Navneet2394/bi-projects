# Dynamic Row-Level Security

## Role: `Regional Manager`
Modeling › Manage roles › New role › table **DimStore** › DAX filter:
```dax
VAR UserRegions =
    CALCULATETABLE (
        VALUES ( SecurityUserRegion[Region] ),
        SecurityUserRegion[UserPrincipalName] = LOWER ( USERPRINCIPALNAME () )
    )
RETURN
    "ALL" IN UserRegions
        || DimStore[Region] IN UserRegions
```
- One role covers all managers: the mapping table decides what each user sees (no role per region).
- `ALL` gives full access (CFO) without a separate role.
- Because FactSalesTarget also links to DimStore, targets are secured too.

## Test
Modeling › View as › tick *Other user* = `rm.south@northwind.example` + role `Regional Manager`.
Expected: only South stores; Net Sales 2025 = ₹7.51 Cr (`retail_2025_by_region` in `scripts/kpi_reference.json`).

## Service
Dataset › Security › add Entra ID (Azure AD) **security groups** to the role, not individuals.
Workspace Viewers are subject to RLS; Members, Contributors and Admins are **not**, a common audit finding.

## Object-level security (optional, needs Tabular Editor)
Hide `DimProduct[UnitCost]` and `FactSales[CostAmount]` from a `Store Staff` role by setting the
column permission to `None`. Visuals that use them will show an error for that role, so design
separate pages accordingly.

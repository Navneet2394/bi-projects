# Power BI Development Standards (Senior / Lead level)

A reusable standards pack: drop it into any team's repo and adapt it.

## 1. Naming conventions
| Object | Convention | Example |
|---|---|---|
| Fact tables | `Fact` + business process | `FactSales`, `FactPurchaseOrderLine` |
| Dimensions | `Dim` + entity | `DimProduct` |
| Bridge / security | `Bridge…`, `Security…` | `SecurityUserRegion` |
| Measures | Business words, Title Case, units in name | `Net Sales`, `Gross Margin %`, `Net Sales YoY %` |
| Measure folders | Numbered | `1 Base`, `2 Time Intelligence`, `3 Target` |
| Parameters (M) | `p` prefix | `pDataFolder`, `RangeStart` (fixed name) |
| Functions (M) | `fn` prefix | `fnLoadCsv` |
| Workspaces | `<Domain> – <Stage>` | `Sales – DEV`, `Sales – TEST`, `Sales – PROD` |

## 2. Modelling rules
1. Star schema first; snowflake only for very large or shared dimensions.
2. Single-direction relationships; bi-directional only with a written justification.
3. Integer surrogate keys; hide all keys and raw numeric columns that have measures.
4. One marked date table; no auto date/time (*Options › Data load › Auto date/time* **off**).
5. Explicit measures only; set *Discourage implicit measures*.
6. Remove unused and high-cardinality columns (GUIDs, line IDs, timestamps → split date/time).
7. Business logic as far upstream as possible (SQL view → Power Query → DAX).

## 3. DAX rules
- Use `DIVIDE`, variables (`VAR`), and `KEEPFILTERS` / `REMOVEFILTERS` explicitly.
- Avoid `FILTER ( Table, … )` on whole fact tables when a column predicate works.
- No calculated columns on facts > 1M rows unless they are needed for relationships/slicing.
- Format strings on every measure; description on every measure.

## 4. Performance checklist (sign-off before PROD)
- [ ] Performance Analyzer: every visual < 500 ms on a warm cache; page < 2 s
- [ ] DAX Studio › VertiPaq Analyzer: no column > 10% of model size without a reason
- [ ] Query folding verified on every incremental-refresh table
- [ ] ≤ 8 visuals per page with queries; use bookmarks/drill-through rather than crowding
- [ ] Aggregation tables or composite model reviewed for > 100M rows

## 5. ALM / CI-CD
```
Developer (Desktop, .pbip in Git) ──PR──► main
        │                                   │
        ▼                                   ▼
  Feature branch                    Azure DevOps / GitHub Actions
                                      • Best Practice Analyzer (Tabular Editor CLI)
                                      • Deploy to DEV workspace
                                      • Deployment pipeline: DEV → TEST → PROD
                                      • Deployment rules swap data source parameters per stage
```
- Store reports as **Power BI Project (.pbip)** with TMDL + PBIR so they diff in Git.
- Run Tabular Editor's **Best Practice Analyzer** rules in the pipeline and fail the build on errors.
- Use **deployment pipelines** (Premium/Fabric capacity or PPU) with parameter rules per stage.
- Certify production semantic models; use *Endorsement › Certified* plus a data steward contact.

## 6. Security & governance
- RLS through Entra ID security groups; document every role in the repo.
- Sensitivity labels (Microsoft Purview) on datasets and reports with confidential data.
- Tenant settings reviewed quarterly: Publish to web, export, external sharing.
- Usage metrics + Admin monitoring workspace; retire reports with no views in 90 days.

## 7. Code review checklist (PR template)
- [ ] Naming conventions followed
- [ ] New measures have format string, folder and description
- [ ] No bi-directional relationships added without justification
- [ ] Numbers reconciled to source (attach the validation query result)
- [ ] RLS tested with *View as*
- [ ] Accessibility: alt text, tab order, colour contrast ≥ 4.5:1

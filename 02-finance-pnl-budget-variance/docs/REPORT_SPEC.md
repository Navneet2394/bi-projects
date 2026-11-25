# Report specification · Finance P&L

Expected values are for **Jan–Dec 2025, all cost centres**.

## Page 1 · P&L Statement
| Visual | Fields / measures | Expected value |
|---|---|---|
| Matrix | Rows `PnLLayout[Line]` (sorted by LineSort); values PnL Value, PnL Budget, PnL Var % | Net Income ₹1.71 Cr vs ₹1.83 Cr (−6.4%) |
| KPI cards | Revenue, EBITDA Margin %, Net Margin % | ₹35.28 Cr · 8.1% · 4.8% |

## Page 2 · Variance Bridge
| Visual | Fields / measures | Expected value |
|---|---|---|
| Waterfall | Category `DimAccount[AccountName]`, Y `Var vs Budget` | Largest adverse: Returns −₹70.5 L, COGS −₹59.5 L; favourable: Gross sales +₹130.2 L |

## Page 3 · Cost Centre Accountability
| Visual | Fields / measures | Expected value |
|---|---|---|
| Bar chart | Cost centre × Opex Actual vs Budget, `Variance Colour` | Marketing HQ ₹94.4 L vs ₹89.9 L; E-Commerce ₹70.7 L vs ₹67.8 L |
| Table | Cost centre, Owner, Actual, Budget, Var, Variance Flag | |

## Page 4 · Trend & Outlook
| Visual | Fields / measures | Expected value |
|---|---|---|
| Line chart | Month × Net Income actual vs budget (2024–2025) | Festive months show the largest gaps |
| KPI card | Latest Estimate (Net Income) | ₹1.69 Cr |

Use the `Time Calc` calculation group as a slicer (Current / YTD / PY / YoY %) on pages 1 and 3.

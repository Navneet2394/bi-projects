# Calculation Group: Time Intelligence

Calculation groups remove the need for one time-intelligence measure per base measure
(Actual YTD, Budget YTD, Forecast YTD …). Create them in **Power BI Desktop (Model view › Calculation group)**
or in **Tabular Editor**. The model's *Discourage implicit measures* setting must be on.

Table `Time Calc`, column `Period`, items (in this ordinal order):

| Ordinal | Item | Expression |
|---|---|---|
| 0 | Current | `SELECTEDMEASURE ()` |
| 1 | MTD | `CALCULATE ( SELECTEDMEASURE (), DATESMTD ( DimDate[Date] ) )` |
| 2 | QTD | `CALCULATE ( SELECTEDMEASURE (), DATESQTD ( DimDate[Date] ) )` |
| 3 | YTD | `CALCULATE ( SELECTEDMEASURE (), DATESYTD ( DimDate[Date] ) )` |
| 4 | FYTD | `CALCULATE ( SELECTEDMEASURE (), DATESYTD ( DimDate[Date], "3/31" ) )` |
| 5 | PY | `CALCULATE ( SELECTEDMEASURE (), SAMEPERIODLASTYEAR ( DimDate[Date] ) )` |
| 6 | YoY | `SELECTEDMEASURE () - CALCULATE ( SELECTEDMEASURE (), SAMEPERIODLASTYEAR ( DimDate[Date] ) )` |
| 7 | YoY % | see below |

```dax
-- YoY %
VAR Cur = SELECTEDMEASURE ()
VAR PY  = CALCULATE ( SELECTEDMEASURE (), SAMEPERIODLASTYEAR ( DimDate[Date] ) )
RETURN DIVIDE ( Cur - PY, ABS ( PY ) )
```
Format string expression for `YoY %`: `"0.0%"`.

**Design notes and pitfalls**
- Measures that already return a percentage (e.g. `Var vs Budget %`) must not be summed by `YTD`;
  either exclude them with `IF ( ISSELECTEDMEASURE ( [Var vs Budget %] ), SELECTEDMEASURE (), … )`
  or rely on the ratio being re-evaluated (DIVIDE of YTD numerator and YTD denominator happens automatically
  because SELECTEDMEASURE re-evaluates the whole measure in the new filter context).
- Precedence matters when you have two calculation groups (e.g. Time + Currency conversion).
- FactFinance is monthly (DateKey = first day of the month), so MTD equals Current.

# Calculation Group: Scenario Comparison (optional)
Table `Compare`, items: `vs Budget` = `[Actual] - [Budget]`, `vs Forecast` = `[Actual] - [Forecast]`,
`vs PY` = `[Actual] - CALCULATE([Actual], SAMEPERIODLASTYEAR(DimDate[Date]))`.

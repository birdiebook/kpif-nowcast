# J5 Osäkerhet som går att lita på: förregistrering

Skriven 2026-11-22 innan något intervall har utvärderats. Bas: origin/main @ a8cd686.

## Hypotes
Dagens felband (empiriska kvantiler av |fel| på de senaste ~34 månaderna, symmetriska) är för smala i
oroliga perioder och för breda i lugna. Ett lägesberoende intervall (bredare när el- och drivmedelspriset
svänger mycket) ger rätt träffgrad både totalt och i oroliga månader, med smalare band i lugna.

**Min gissning innan:** alla expanderande metoder (U1, U3–U6) ligger inom ±5 pe totalt. U2 (rullande 36 mån)
undertäcker efter lugna perioder (2015–2020) och övertäcker efter 2022. I oroliga månader (översta
tredjedelen av |el_chg|) undertäcker U1–U3 med 10–20 pe, medan U5/U6 ligger nära nominellt. U5 eller U6
får lägst pinball-förlust.

## Upplägg
- **Punktprognos:** `comp_fuel` (komponentmodellen på origin/main, den enda egna modellen med fel 2007–2026).
  Metoderna är modelloberoende och kan läggas på J2 V2 efter merge.
- **Sekventiellt:** intervallet för t byggs bara av fel för månader ≤ t−1 (kända vid deadline) och features
  för t (el_chg, fuel_chg, kända vid deadline). Inkörning: utvärdering från 2015-01, då finns ≥ 36 tidigare fel
  (felen börjar ~2007). U2 har exakt 36.
- **Nivåer:** centrala intervall 50, 80 och 90 % (kvantiler 0,05/0,10/0,25/0,75/0,90/0,95).
- **Mått:** träffgrad per nivå med binomialt 95 %-konfidensintervall (Clopper-Pearson), pinball-förlust
  (snitt över de sex kvantilerna), snittbredd. Också träffgrad i oroliga månader (översta tredjedelen av
  |el_chg| bland utvärderingsmånaderna) och lugna (nedersta tredjedelen). Obs: träffarna är autokorrelerade,
  så det binomiala intervallet är för smalt. Det redovisas ändå enligt briefen.
- **Godkänt (planen):** träffgrad inom ±5 pe från nominell nivå på alla tre nivåerna, 2015-01..2026-10.
  Bland godkända väljs lägst pinball-förlust.

## Varianter (exakt lista, 6 st)
| # | Namn | Metod |
|---|---|---|
| U1 | `j5_abs_all` | Symmetriskt: ±kvantil av |fel|, alla tidigare fel (dagens metod, men sekventiell och expanderande) |
| U2 | `j5_abs_36` | Som U1 men bara de senaste 36 felen (nära dagens 34) |
| U3 | `j5_signed_all` | Asymmetriskt: kvantiler av signerade fel, alla tidigare (split conformal på fel) |
| U4 | `j5_ewma` | Normaliserad conformal: σ_t = √(EWMA av tidigare kvadrerade fel, λ = 0,9); kvantiler av e/σ gånger σ_t |
| U5 | `j5_scaled_energy` | Normaliserad conformal: σ_t = OLS-anpassning av |fel| på [1, |el_chg|, |fuel_chg|] (expanderande, golv 0,05); kvantiler av e/σ gånger σ_t |
| U6 | `j5_qreg_energy` | Linjär kvantilregression av fel på [1, |el_chg|, |fuel_chg|] per kvantil (expanderande, sklearn QuantileRegressor, alpha = 0); kvantiler sorteras för att undvika korsning |

`forecast.py` rörs inte (briefen förbjuder det). Förslaget levereras som en separat funktion och en text om
hur den skulle kopplas in. pytest `tests/test_j5_intervals.py` kräver identiskt intervall för t med och utan
data efter t:s deadline.

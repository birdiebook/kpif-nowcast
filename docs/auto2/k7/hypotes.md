# K7 Tjänstekomponenten: förregistrering

Skriven 2026-11-23 innan något fel för 2015–2026 har beräknats för varianterna nedan.
Bas: main @ 51fa62f (K0–K4, K6 mergade). Varianter före K7: körning 2 13 av 30, projektet 36.
K7:s tak: 5. Efter K7: körning 2 18 av 30, projektet 41.

## Varför och vad jag redan har sett (ärligt om urvalet)
K3: tjänster står för 37 % av kvadratfelet 2015–2026. Innan förregistreringen tittade jag på **baslinjens**
(J2 V2:s tjänstedel: säsong som 5-årsmedel av avvikelsen från 12-månadersmedlet, plus trend) tjänstefel per
månad och år 2013–2026 och på vilka TAB6613-grupper som bär felet. Inga nya prognosserier beräknades.
Det jag såg:

- Paketresor (09.8) står för ~45 % av tjänstefelets varians, persontransporter/flyg (07.3) ~25 %, logi
  (11.2) ~7 %. Hyror, försäkringar och avgifter är små (< 2 % var). Felet är alltså resor.
- Felet sitter i januari, april och juni–augusti. **Augusti 2023–2026** har positiva fel (prognosen för hög)
  varje år: 5-årsfönstret innehåller pandemisomrarna 2021–2022, då säsongsmönstret i resor var platt.
- **April:** sen påsk (2017, 2019, 2025) ger negativt fel, tidig påsk eller påsk i mars (2015, 2016, 2026)
  positivt. J4:s påskdummy (påskdagen i månaden ja/nej) skiljer inte tidig från sen april och gav inget.
- **Januari:** stort negativt fel 2023 (−0,83 pe) när inflationen var hög, alltså större årsskiftesomprissättning
  än femårssnittet.

Specifikationerna nedan är alltså valda efter att ha sett 2013–2026. DM-p på 2015–2026 är därför
optimistiska. **Ren kontroll:** tjänsteserien (TAB6628) finns från 1987, och åren 1995–2009 har jag inte
tittat på. Tjänstedelens fel i m/m 2000-01..2009-12 (n = 120) rapporteras som ett test som inte är påverkat
av urvalet. En variant som vinner 2015–2026 men inte 2000–2009 märks "osäker (vald i efterhand)".

## Hypotes
Tjänstefelet är till stor del förutsägbart kalender- och säsongsbrus i resor, och den nuvarande säsongen
(5-årsmedel) är (a) känslig för avvikande år (pandemin) och (b) blind för påskens läge och för att
januariomprissättningen skalar med inflationstakten. En robust säsong (median) och två kalender-/
nivåregressorer bör minska tjänstefelet i m/m utan ny data.

## Tjänstemodeller (ändrar bara J2 V2:s tjänstedel; energi, varor, livsmedel, kapitalstock oförändrade)
- **A (median):** säsong = median (i stället för medel) av avvikelsen från 12-månadersmedlet samma
  kalendermånad de senaste 5 åren (de som finns). Trend oförändrad (12-månadersmedel t.o.m. t−1).
- **B (median + kalender):** A plus en expanderande OLS-korrektion (utan intercept, `fit_correction`,
  träning från 1995-01, minst 24 månader) av tjänsteresidualen (utfall − A) på två regressorer:
  - `easter_dev`: antal dagar av påskfönstret (fredagen före palmsöndagen t.o.m. annandag påsk, påskdagen −9 till +1, 11 dagar)
    som ligger i månad t, minus snittet för samma kalendermånad de 5 föregående åren. Kalendern är känd i förväg.
  - `jan_dev`: i januari tjänsternas årstakt i december (t−1, publicerad mitten av januari, före deadline
    4 februari) minus snittet av decemberårstakten de 5 föregående åren; 0 övriga månader.
  
  Koefficienten för t skattas bara på månader < t (tjänsteutfallet för t−1 är publicerat före t:s deadline).

Tjänstedelens förändring Δ (pe av KPIF m/m) blir en förändring av KPIF-årstakten k·Δ, k = I[t−1]/I[t−12].
`j2s` = J2 V2 med tjänstemodell A eller B.

## Varianter (exakt lista, 5 st)
| # | Namn | Prognos |
|---|---|---|
| T1 | `k7_med_half` | 0,5·rb_updated + 0,5·j2s(A) = 50/50 + ½(j2s(A) − j2) |
| T2 | `k7_med_full` | 50/50 + (j2s(A) − j2) |
| T3 | `k7_cal_half` | 0,5·rb_updated + 0,5·j2s(B) |
| T4 | `k7_cal_full` | 50/50 + (j2s(B) − j2) |
| T5 | `k7_k2_cal_full` | `k2_avg_ens_s` + (j2s(B) − j2) |

"half" antar att Riksbankens prognos inte har samma tjänstefel som J2 (rättelsen når bara J2-halvan),
"full" att rb_updated har samma säsongsfel (t.ex. samma påsk- och sommarmönster). Jag vet inte vilket, så båda testas.

## Utvärdering och skärm
- Period: 2015-02..2026-10 (n = 141, samma som K2). Använd period 2024–2026 rapporteras bara.
- DM på absolutfel, **ensidigt** (H1: varianten har lägre MAE), alla nästlade: T1–T4 mot 50/50, T5 mot
  `k2_avg_ens_s`. **Holm över de 5.** Även rapporterat: T1–T4 mot `k2_avg_ens_s` och T5 mot 50/50
  (tvåsidigt där ej nästlat), utan Holm.
- **Klarar urvalsskärmen** om Holm-p < 0,10 mot sin bas och MAE 2024–2026 inte högre än basens.
- Rapport: per år (diff mot basen), tjänstedelens MAE i m/m (pe) för A och B mot baslinjens på 2000–2009
  (ren) och 2015–2026, koefficienterna för `easter_dev` och `jan_dev` över tid.
- Revision: TAB6628 och KPIF-index som i J2 V2 (samma antagande som basen); TAB6613 används inte i
  modellerna. Inga nya datahämtningar.
- pytest: prognosen för t identisk med och utan data efter t:s deadline, för alla fem.

## Min gissning innan
- A (median): tjänstedelens MAE i m/m −2 till −5 % 2015–2026 (mest 2023–2026 augusti), ~0 % 2000–2009.
- B: −5 till −10 % 2015–2026, −3 till −8 % 2000–2009 (påsken är den robusta delen; januari osäker med
  ~1 observation per år).
- Totalt: T1 −0,001, T2 −0,003, T3 −0,003, T4 −0,007 mot 50/50 (0,217); T5 −0,005 mot `k2_avg_ens_s` (0,201).
- Ingen klarar urvalsskärmen med Holm (MDE ≈ 0,02); T4 har bäst chans (rå p ~0,05–0,2).

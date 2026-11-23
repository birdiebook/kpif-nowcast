# K13 Skatterensad bas: resultat (urvalsevidens)

## Överst: effekten på den skarpa prognosen för 2026-11 (förslag till `--adjust`)

Med skatterensad bas blir den skarpa modellens (`component_fuel_el_v1`) prognos för 2026-11 **+0,13 pe högre i
årstakt**: 2,05 → 2,18 % (körning 23 nov, elpris för 22 av 30 dagar, samma indata som `forecast.py`). Det ligger
över tröskeln 0,05 pe.

| Modell (2026-11, årstakt) | Orensad | Rensad | Skillnad | varav livsmedel | varav energi |
|---|---|---|---|---|---|
| `component_fuel_el_v1` (skarp) | 2,05 | 2,18 | **+0,13** | +0,064 pe m/m | +0,063 pe m/m |
| J2 V2 | 1,86 | 1,99 | +0,12 | +0,064 | +0,058 |
| `k2_avg_ens_s` | 1,68 | 1,75 | +0,06 | | |
| `rb_updated` | 1,18 | 1,18 | 0 | | |

**Varför:** 12-månaderstrenden för november (nov 2025–okt 2026) innehåller matmomssänkningen (−0,77 pe/12 =
−0,064 per månad) och de tillfälliga energi- och elskatteändringarna 2026-01, -05, -07 och -10 (netto −0,54 pe/12 ≈
−0,045, plus ~0,02 från att energikorrektionens koefficienter skattas om). I november ändras ingen skatt
(koldioxidskattesänkningen gäller hela november), så den orensade modellen räknar in en sänkning som inte sker.

**Utanför modellen, också i november:** halverat pris på månadskort i kollektivtrafiken upphör 3 nov i Skåne, Blekinge,
Jönköping, Kalmar och Kronoberg (~1/4 av befolkningen). Det är en avgift som SCB inte rensar i KS. Grov effekt:
**+0,03 till +0,05 pe** (juli: −0,2 pe för hela landet).

**Förslag till månadsrutinens steg 2:** `--adjust 0.15 --note "K13: skatterensad bas +0.13 (matmoms 2026-04 och
drivmedels-/elskatter 2026 i 12-mån-trenden); månadskort åter fullpris 3 nov i Skåne m.fl. ~+0.03; källa
docs/skattekalender.md"`. Räkna om skillnaden vid den slutliga körningen (1–4 dec) med
`python -m kpif_nowcast.k13_tax current`. Den bör ligga kvar runt +0,13.

**Förbehåll:** backtesten bekräftar inte att den rensade *basen* förbättrar prognoserna i snitt (−0,0005 pe utan
händelsemånaderna, se nedan). Förslaget vilar på att effekten är mekanisk (skattesänkningar är ingen underliggande
prisutveckling) och inte på urvalsevidens. Efter momssänkningen (2026-06, -08, -09, alla utan händelser) blev den
rensade J2 bättre två månader av tre.

**December 2026 (viktigare):** koldioxidskattesänkningen upphör 30 nov, alltså **+0,40 pe** på m/m (ex ante: minus
julis KS-effekt), och månadskortet återgår i resten av landet 2–3 dec, ~**+0,15 pe**. Ingen modell ser detta utan
justering. Totalt ~+0,55 pe utöver den rensade basen (~+0,7 pe mot den orensade skarpa modellen).

---

Förregistrering: [hypotes.md](hypotes.md) (commit 0c8c713, före körning). Kod: `src/kpif_nowcast/k13_tax.py`.
Körning: `experiments/runs/20261123T100622Z_k13_tax.csv` vid f5ab041. Hela tabeller: [results_raw.md](results_raw.md),
2026-11: [current_raw.md](current_raw.md). Kalender och källor: [docs/skattekalender.md](../../skattekalender.md).

**Varianter: 2 av K13:s 2** (`k13_j2_clean`, `k13_ens_clean`), inga tillägg efter resultat. DM på absolutfel,
ensidigt (H1: varianten har lägre MAE än sin orensade referens), Holm över de två.

## Vad som byggdes
- **Händelsekalender** (`EVENTS`, 8 händelser 2022–2026): engångsändringar av skatter med komponent, beslutsdatum
  och källa. Återkommande januari- och julieffekter, avgifter och oklara fall är inte med (motiverat i kalendern).
- **Rensning:** för varje händelsemånad s < t dras SCB:s realiserade KS-effekt (energi- eller icke-energidelen, KPIF
  vs KPIF-KS och KPIF-XE vs KPIF-XE-KS) från komponentens bidrag. Säsong, trend och energikorrektion skattas på de
  rensade bidragen.
- **Tillägg i prognosmånaden** bara om beslutsdatum < deadline(t). Startmånader: SCB:s mekaniska KS-siffra (se
  förbehåll nedan). Slutmånader: minus startmånadens realiserade KS-del (helt ex ante).
- `clean_component_forecast` fungerar för både den skarpa modellen och J2 V2; utan händelser ger den exakt samma
  prognos som originalen (test).

## Resultat, 2015-02..2026-10, n = 141 (förregistrerat kriterium)

| Variant | Referens | MAE | Ref-MAE | Diff | p ensidigt (rå) | Holm p | 2024–26 diff (n = 34) |
|---|---|---|---|---|---|---|---|
| `k13_j2_clean` | J2 V2 | 0,239 | 0,243 | −0,004 | 0,27 | 0,54 | −0,020 |
| `k13_ens_clean` | `k2_avg_ens_s` | 0,203 | 0,201 | +0,002 | 0,73 | 0,73 | −0,000 |

**Ingen variant klarade urvalsskärmen.** Gissningen före körning var för optimistisk för J2-varianten (−0,008 till
−0,015, utfall −0,004) och fel i tecken för ensemblen (−0,003 till −0,008, utfall +0,002).

| Uppdelning (rapport) | `k13_j2_clean` − J2 V2 | `k13_ens_clean` − `k2_avg_ens_s` |
|---|---|---|
| Utan de 7 händelsemånaderna (n = 134) | −0,0005 (p 0,37) | +0,0002 (p 0,61) |
| 2026-04..2026-10 (n = 7) | −0,064 | −0,008 |
| 2022 | +0,005 | +0,022 |
| 2024 / 2025 / 2026 | −0,007 / −0,003 / −0,057 | −0,004 / +0,003 / −0,000 |

**Händelsemånaderna** (fel i årstakt, J2 V2 → rensad): 2026-04 +0,82 → +0,05 (momsen), 2026-01 +0,11 → 0,00,
men 2022-05 0,00 → −0,28, 2026-07 +0,05 → −0,27 och 2026-10 +0,45 → +0,67. Drivmedelssänkningarna slog alltså
inte igenom fullt i KPIF den månad de infördes, eller så tog andra prisrörelser ut dem (SCB: drivmedel −9,4 % i juli
mot ~−15 % mekaniskt). Momsen slog igenom fullt. Känslighet: tillägget ×0,8 ger −0,0038, ×1,2 −0,0023.

## Läckage
- Rensningen av historiken använder KS för s ≤ t−1 (publiceras ~13:e i s+1). Tillägget kräver beslutsdatum < deadline(t).
  Test i `tests/test_k13_tax.py`: identisk prognos för J2, den skarpa modellen och ensemblen när KPIF, komponenter, KS
  och övrig data klipps vid deadline (2016-03, 2022-05, 2022-10, 2026-04, 2026-07, 2026-10). Händelser med beslut på
  eller efter deadline används varken som tillägg eller i rensningen. Framtida händelser påverkar inte t.
- **Kvarvarande risk:** storleken i startmånader är SCB:s KS-siffra, publicerad efter deadline. Den är mekanisk
  (skatteändring × vikt) och våra kontroller ex ante stämmer (moms: −5,36 % × ~14 % vikt; koldioxidskatt: ~−15 % ×
  ~2,7 %), men värdet är inte bevisat ex ante. Det påverkar 5 av 141 månader. Ingen variant klarade skärmen, så
  inget märks "obekräftat".
- Inga Spec med `revised=True` används utöver det som redan finns i K2:s set S (som är oförändrat).

## BLOCKED
Inget. Inga nya datahämtningar (KS-serierna fanns i `data/processed/tax_effects.csv`), inga nya paket. Webbkällor
lästes för kalendern (regeringen, riksdagen, Skatteverket, SCB, TT).

## Vad lärde vi oss
1. **Rensningen hjälper när genomslaget är fullt och stort (momsen), men inte i snitt.** Utan händelsemånaderna är
   skillnaden noll. Säsong + 12-månaderstrend har alltså inte farit så illa av skatteändringarna 2015–2025, eftersom de
   flesta var små eller återkommande.
2. **Drivmedelsskatter slår inte igenom mekaniskt samma månad.** Med fullt genomslag överskattas fallet 2022-05 och
   2026-07 med ~0,3 pe. SCB:s KS antar fullt genomslag; för drivmedel är det fel med den här modellens bränsleproxy.
   En skattad genomslagsgrad (t.ex. 0,5) kunde hjälpa, men det kräver en ny förregistrerad variant.
3. **K2-ensemblen vinner ingenting.** Riksbankens prognos har redan med beslutade skatter, och ML-korrektionen
   anpassar sig till J2-delens fel. Med rensad J2 blir felet i händelsemånaderna mindre men ML-delen tappar lite.
4. **Det viktiga för de närmaste prognoserna är kalendern, inte modellvalet:** november +0,13 (bas) + ~0,03
   (månadskort), december +0,40 (koldioxidskatten) + ~0,15 (månadskort). Matmomsen ligger kvar i trenden till 2027-03.
   Höjningen tillbaka 2028-01 ger ~+0,77 pe.

## Öppna frågor
1. Ska den rensade basen bli huvudmodellens bas? Urvalsevidensen räcker inte. Det rimliga är att behålla den som
   **manuell justering** (månadsrutinens steg 2) och räkna fram siffran med `k13_tax current` varje månad till 2027-03.
2. Genomslagsgrad för drivmedelsskatt (lärdom 2), och om KS-julieffekten 2019–2025 är en metodeffekt hos SCB.
3. Kontrollera budgetpropositionen för 2027 (riksdagen röstar ~9 dec) för skatteändringar 2027-01.

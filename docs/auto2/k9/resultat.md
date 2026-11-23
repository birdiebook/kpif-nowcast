# K9 Längre horisont 3–12 månader: resultat (urvalsevidens)

Förregistrering: [hypotes.md](hypotes.md) (commit b4b5287, före körning). Kod: `src/kpif_nowcast/k9_horizon.py`.
Körning: `experiments/runs/20261123T093232Z_k9_horizon.csv` vid 0ab9fcd ("+dirty" gäller bara radslut i
`data/README.md`). Alla tabeller, parametrar och diff per år: [results_raw.md](results_raw.md).

**Varianter: 4 av 4** (`k9_ridge_h3`, `k9_ridge_h12`, `k9_shrink_h12`, `k9_miss_h6`), inga tillägg efter resultat.
Inga nya hämtningar; alla serier fanns i observationstabellen.

## Vad som byggdes
Prognos av KPIF årstakt h = 3, 6 och 12 månader efter senast publicerade månad, gjord dag 4 i o+2. Bas =
Riksbankens senaste prognos före prognosdagen. Korrektionen använder vad som hänt sedan Riksbankens cutoff:
Riksbankens egen miss på senaste utfallet, prognosens ålder, Brent, KIX, styrränta, 2-årsränta, KI:s
prisplaner (detaljhandel, tjänster), PPI konsumtionsvaror och euroområdets HIKP (de två sista revised=True).
Ridge med nästlad tidsserie-CV (`gap = h`, så att inre valideringsmål inte överlappar träningsmålen),
krympning mot 2 % med skattad vikt, och en enparameters "missen består"-korrektion. DM-test med Newey-West
lagg h − 1, HLN-korrektion, ensidigt mot Riksbanken (nästlat), Holm över de 4.

## Referenser, mål 2015-01..2026-10

| h | n | effektivt n (n/h) | Riksbanken | "2 %" | naiv | 2024–26 (n = 34): RB / 2 % / naiv |
|---|---|---|---|---|---|---|
| 3 | 139 | 46 | **0,489** | 1,368 | 0,668 | **0,391** / 0,621 / 0,603 |
| 6 | 136 | 23 | **0,814** | 1,371 | 1,104 | **0,511** / 0,621 / 1,074 |
| 12 | 130 | 11 | 1,388 | **1,385** | 1,885 | 0,619 / 0,621 / 2,206 |

På h = 12 är Riksbanken och "2 %" lika bra (diff +0,002, p = 0,98), också 2024–26.

## Varianter, mål 2015-01..2026-10 (förregistrerat)

| Variant | h | n | eff. n | aktiva | MAE | RB | diff | p ensidig rå | Holm p | 2024–26 MAE / RB |
|---|---|---|---|---|---|---|---|---|---|---|
| `k9_ridge_h3` | 3 | 139 | 46 | 101 | 0,471 | 0,489 | −0,019 | 0,33 | 1,00 | 0,386 / 0,391 |
| `k9_miss_h6` | 6 | 136 | 23 | 107 | 0,833 | 0,814 | +0,020 | 0,68 | 1,00 | 0,671 / 0,511 |
| `k9_shrink_h12` | 12 | 130 | 11 | 95 | 1,485 | 1,388 | +0,097 | 0,90 | 1,00 | 0,621 / 0,619 |
| `k9_ridge_h12` | 12 | 130 | 11 | 83 | 1,945 | 1,388 | +0,558 | 0,97 | 1,00 | 1,552 / 0,619 |

Mot "2 %" och naiv (tvåsidigt, rå p): `k9_ridge_h3` är bättre än båda (−0,90, p < 0,01; −0,20, p = 0,01),
precis som Riksbanken. `k9_ridge_h12` är sämre än "2 %" (+0,56, p = 0,03). Övriga: se results_raw.md.

**Ingen variant klarade urvalsskärmen** (alla Holm p = 1,00). Revisionsflaggan blir därmed inte aktuell.

### Var vinster och förluster sitter (bara rapport)
- `k9_ridge_h3`: −0,52 pe 2022 (missen på senaste utfallet bar information när inflationen steg), +0,22 2023
  (samma signal fel vid vändningen). Bättre än Riksbanken i 49 % av månaderna från 2018-06. Kraftig krympning
  (alpha ≈ 1000); senaste anpassningen är i praktiken RB + ett intercept på +0,18 (Riksbankens
  genomsnittliga underskattning) och små vikter på missen, PPI, 2-årsränta och Brent.
- `k9_miss_h6`: φ ≈ 1 (missen antas bestå helt sex månader). Hjälper 2020–2022, förlorar 2023, 2024 och
  2026 (+0,47).
- `k9_shrink_h12`: vikten på Riksbanken är instabil: ~0,2 till 2020, ~0,8 under 2021–22, sedan 0 från 2023
  (Riksbankens prognoser 2020 låg under målet medan utfallet 2021–22 låg långt över, vilket gav negativ
  kovarians). Kostade +0,87 pe 2023, när Riksbanken rätt såg att inflationen skulle ligga kvar högt.
- `k9_ridge_h12`: interceptet lär sig 2022 års enorma underskattning (+0,88 vid senaste anpassningen) och
  ger +2,5 pe 2023 och +2,2 2024. Med effektivt ~7 oberoende fönster när den är aktiv går det inte att
  skatta en korrektion på 12 månader.

## Informationsmängd
`tests/test_k9_horizon.py`: för varje variant är prognosen för ett aktivt ursprung identisk när
observationstabellen trunkeras till known_from ≤ prognosdagen och Riksbankens arkiv till omgångar publicerade
före den. Dessutom: startregeln ger RB, träningsrader har publicerade mål, DM/Holm-kontroll. Grönt.

## Gissningen innan
Rätt i riktning för h = 3 (−0,019, strax under gissade −0,02 till −0,05, p = 0,33, inte signifikant) och h = 12 ridge
(sämre, men +0,56 är mer än gissat). Fel för h = 6 (gissat −0,01 till −0,04, utfall +0,02) och krympningen
(gissat ±0,05, utfall +0,10).

## BLOCKED
Inget. Ingen hämtning gjordes.

## Vad lärde vi oss
1. **Riksbanken är ribban och står kvar.** Ingen av fyra rimliga sätt att använda information efter deras
   cutoff, eller att krympa mot målet, ger lägre MAE med någon säkerhet. Det effektiva urvalet är litet:
   ~46 oberoende fönster på 3 månader, ~23 på 6 och ~11 på 12. Bara differenser på flera tiondelar kan
   upptäckas på 12 månader.
2. **h = 3: missen bär något i en uppgång, men vänder vid toppen.** −0,02 i snitt är i nivå med slump. En
   uppdaterad Riksbanksprognos ("rb_updated" för längre horisont) är inget självklart lyft utanför nowcasten.
3. **h = 12: "det blir 2 %" är lika bra som Riksbanken, men att väga ihop dem fungerar inte.** Vikten skattas
   på en handfull regimer (låg inflation, chocken, nedgången) och hamnar fel när regimen byter. Varje
   skattad parameter på 12 månader är i praktiken skattad på 1–2 episoder.
4. **Rekommendation:** frys ingen K9-variant. Behåll Riksbankens prognos som långsiktig referens (och "2 %"
   som jämförelse på 12 månader). Nästa steg för längre horisont, om något: Riksbankens prognos som
   publicerad referens i dashboarden, inte en egen modell.

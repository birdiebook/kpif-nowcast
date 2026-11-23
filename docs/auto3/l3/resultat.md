# L3 Hyror: resultat

Spår L3 i autonom körning 3. Kod: `src/kpif_nowcast/catalog_rents.py`, tester: `tests/test_l3_rents.py`.
Jämförelsen nedan går att köra om med `python -m kpif_nowcast.catalog_rents`.

## Vad som byggdes

| Nyckel | Serie | Frekv. | Från–till | Fördröjning | Rev. |
|---|---|---|---|---|---|
| `rent_negotiated` | Hyresförhandlingarnas utfall, vägt riksgenomsnitt (Hyresgästföreningen) | A (december i hyresåret) | 2016–2026 | −184 d → 30 juni samma år för 2023, 2025, 2026; övriga år källrapportens uppladdningsdatum | ja |
| `kpi_rent_index` | KPIF-post hyror för hyresgäster, COICOP 04.1.1 (SCB TAB6598) | M | 1980-01–2026-10 | 15 d | ja |

`rent_negotiated` är en handkurerad tabell i modulen (`NEGOTIATIONS`), med en rad per år och en källänk per rad.
`negotiated()` (Spec:ens fetch-funktion) läser tabellen i modulen och sparar en daterad kopia i `data/raw/l3/`. KPI-serien hämtas från SCB och cachas där.
Det fanns redan en SCB-serie från hyresundersökningen, `rent_change` (TAB6051, årlig, publiceras i oktober). Den används som kontroll.

**Fördröjning.** Förhandlingarna börjar på hösten och blir klara på våren. Ett daterat riksgenomsnitt från våren är belagt för tre år: 2023 (Hyresgästernas lägesrapport våren 2023, 4,16 %, PDF 2023-04-13, 52 % klart), 2025 (TT 2025-03-21) och 2026 (TT 2026-03-02). För dem gäller known_from 30 juni, minst två månaders marginal. Övriga år (2016–2022, 2024) har inget belagt vårdatum. Där blir värdet känt först när rapporten det hämtas från laddades upp (HTTP `Last-Modified`, 2019-01-21 till 2025-06-24, se publiceringskalendern). Det går in via `publication.LATE_RELEASES`. Varje sparat värde är det som stod i källan på källans datum, så backfill visar ingen siffra innan den var offentlig. Vårens siffra skiljer sig lite från det slutliga snittet (2020: 1,93 → 1,92; 2024: 5,2 → 5,15), därför `revised=True`.

## Tabellen

| År | Utfall % | Omfattning | Källa |
|---|---|---|---|
| 2016 | 0,64 | alla förhandlade, vägt | HGF verksamhetsberättelse 2017 |
| 2017 | 0,71 | alla förhandlade, vägt | HGF verksamhetsberättelse 2017 |
| 2018 | 0,98 | alla förhandlade, vägt | HGF verksamhetsberättelse 2018–2019 |
| 2019 | 1,91 | alla förhandlade, vägt | HGF verksamhetsberättelse 2018–2019 / 2020 |
| 2020 | 1,92 | alla förhandlade, vägt | HGF verksamhetsberättelse 2020 |
| 2021 | 1,32 | alla förhandlade, vägt | HGF verksamhetsberättelse 2021 |
| 2022 | 1,71 | läge 2022-04-20 (83 % klart); privata = allmännyttan | HGF verksamhetsberättelse 2022 |
| 2023 | 4,16 | alla förhandlade, vägt (52 % klart); allmännyttan 4,10, privata 4,27 | HGF lägesrapport våren 2023 |
| 2024 | 5,15 | allmännyttan 5,16, privata 5,13 | HGF verksamhetsberättelse 2024 |
| 2025 | 4,8 | alla förhandlade | HGF verksamhetsberättelse 2025 |
| 2026 | 3,4 | allmännyttan och privata | hyresgastforeningen.se, sidan om hyresförhandling 2027 |

Länkarna finns i `NEGOTIATIONS`.

**Saknas:**
- **2010–2015.** Ingen nationell siffra på de källor som går att nå härifrån. Den äldsta verksamhetsberättelsen på hyresgastforeningen.se är 2017, och gissade URL:er för 2015–2016 ger 404.
- **2027.** Förhandlingarna pågår och det finns inget riksgenomsnitt än. Kända lokala utfall från 1 januari 2027:
  - Stockholms stad, privata (skiljeman): 2,85 % (Fastighetsägarna 2026-10-21).
  - Stockholmsregionen, privata (skiljeman): 2,7–3,2 % per kommun (HGF, 2026-10-02).
  - Ronnebyhus: 2,2 %.
  - Skiljemännens snitt: 2,8 % på cirka 8 600 lägenheter.

  De två sista kommer från HGF-pressmeddelanden som syntes i sökträffar. via.tt.se går inte att nå härifrån.

  Fastighetsägarna publicerar inget eget riksgenomsnitt på sin webb, bara regionala nyheter. Hyresgästföreningens siffra täcker båda parterna, så den används.

## BLOCKED

- **via.tt.se, tv4.se, mynewsdesk, sverigesallmannytta.se, hemhyra.se och web.archive.org** finns inte i miljöns lista. Där finns pressmeddelandena med exakta publiceringsdatum och siffror för åren före 2016. Johannes kan lägga till `via.tt.se` och `www.sverigesallmannytta.se` om 2010–2015 och exakta datum behövs.
- **Ingen drift mot webben behövs.** Tabellen uppdateras för hand en gång om året, i mars–april när riksgenomsnittet är känt.

## Hur väl förutser förhandlingen hyresposten? (deskriptivt, inget test)

Hyresposten i KPI (04.1.1) jämförs med förhandlingsutfallet samma år:

| År | Förhandlat | KPI dec→apr | KPI dec→dec | Andel jan–apr | Skillnad dec→dec | SCB `rent_change` |
|---|---|---|---|---|---|---|
| 2016 | 0,64 | 0,58 | 0,82 | 0,71 | +0,18 | 0,8 |
| 2017 | 0,71 | 0,59 | 0,84 | 0,70 | +0,13 | 0,8 |
| 2018 | 0,98 | 0,76 | 1,10 | 0,70 | +0,12 | 1,1 |
| 2019 | 1,91 | 1,43 | 1,88 | 0,76 | −0,03 | 1,9 |
| 2020 | 1,92 | 1,37 | 1,86 | 0,74 | −0,06 | 1,9 |
| 2021 | 1,32 | 0,94 | 1,38 | 0,68 | +0,06 | 1,4 |
| 2022 | 1,71 | 1,44 | 1,69 | 0,85 | −0,02 | 1,7 |
| 2023 | 4,16 | 2,91 | 3,97 | 0,73 | −0,19 | 4,1 |
| 2024 | 5,15 | 3,73 | 4,92 | 0,76 | −0,23 | 5,0 |
| 2025 | 4,80 | 4,34 | 4,69 | 0,92 | −0,11 | 4,6 |
| 2026 | 3,40 | 3,19 | (dec→okt 3,31) | – | – | 3,3 |

- **Nivån stämmer nästan exakt.** KPI-hyrespostens ökning från december till december skiljer sig från förhandlingsutfallet med i snitt 0,11 procentenheter, som mest 0,23. Korrelationen är 0,999 på tio år, men för få år för mer än en beskrivning. 2016–2018 ligger KPI något över. Det beror troligen på nyproduktion och ombyggnader, som inte ingår i den årliga förhandlingen.
- **Tidsprofilen är det som är svårt att prognostisera.** 68–92 % av årets höjning (snitt 75 %) syns i KPI under januari–april. Resten kommer i maj–augusti, och från september är posten i stort sett platt. Profilen har flyttats tidigare:
  - 2025 kom 2,6 % redan i januari och 2026 1,6 %.
  - Tidigare låg januari på 0,2–0,8 %, och april var ofta lika stor som januari.

  Det stämmer med att skiljemannasystemet (från 2024 års hyror) har gjort fler överenskommelser klara före 1 januari. Retroaktiva uppgörelser syns när de registreras, inte när hyran gällde.
- SCB:s `rent_change` ger samma bild som förhandlingen (±0,2), men den kommer först i oktober. Förhandlingsserien är den tidiga signalen.

## Läget i Sverige nu

Hyreshöjningarna har toppat:

- 2023: 4,16 %
- 2024: 5,15 %
- 2025: 4,8 %
- 2026: 3,4 %
- 2027: troligen 2,8–3 %, att döma av Stockholms skiljemannabeslut och lokala avtal

Hyresposten i KPIF ligger på 3,3 % i årstakt (oktober 2026). Den sjunker mot cirka 3 % när januari–april 2027 ersätter 2026 års höjningar. Hyrorna är en stor och trög del av KPIF. Ett hyresbidrag som minskar med cirka 0,4 procentenheter för posten drar ned tjänsteinflationen under första halvåret 2027.

## Användning i våg 2

1. **Kandidat för hyrespostens bidrag i januari–april.** Förväntad m/m-ökning för posten i månad m ≈ förhandlat utfall × andel för månad m. Andelen skattas på tidigare år, rullande och bara med data före prognosmånaden. Med known_from 30 juni (belagda år) ser modellen årets utfall först från juli, och för obelagda år ännu senare (när verksamhetsberättelsen laddades upp, ofta året efter). För jan–apr-månaderna ger serien då bara förra årets nivå eller äldre. Det är det ärliga informationsläget med nuvarande belägg.
2. **Starkare variant om Johannes vill.** Lägg ett per år belagt datum för när siffran blev offentlig (mars–april), till exempel med en tidig release-mekanism i `publication.py`. Då kan serien användas i jan–apr samma år. Det kräver pressmeddelanden med datum, alltså att via.tt.se öppnas. Hyresgästernas lägesrapport på hyresgastforeningen.se är en nåbar källa med datum, men bara våren 2023 hittades.
3. **Nära horisont, mest relevant för januari–mars.** De lokala utfallen för nästa år (Stockholm) är kända redan i oktober–december. En "delutfall"-serie skulle kunna byggas om källorna öppnas, men inte på 2027-data enbart.
4. Ingen effekt är testad här. Inget p-värde.

**KPI-hyresposten före 2026.** `kpi_rent_index` före 2026 är SCB:s omräkning till COICOP 2018 (TAB6598, uppdaterad 2026-11-12). Backfill gör varje värde känt vid periodens slut + 15 d, men serien fanns inte i realtid. Backtest före 2026 använder alltså rekonstruerade värden. `revised=True` flaggar det. Behövs riktiga realtidsvärden kan COICOP 1999-hyresindexet läggas in som egen serie.

## Granskning

En oberoende granskare hade fem fynd. Alla bedömdes mot källan.

| Fynd | Dom | Åtgärd |
|---|---|---|
| 1. 2023 sparat som 4,0, HGF:s egen siffra är 4,2 (wrong) | **Stämmer.** "Fyra procent" i verksamhetsberättelsen 2023 är avrundat. Hyresgästernas lägesrapport våren 2023 (hyresgastforeningen.se, PDF 2023-04-13) ger 4,16 % (allmännyttan 4,10, privata 4,27), och TT-tabellen 4,2. | Rättat till **4,16** med lägesrapporten som källa. Det är mer precist än TT:s 4,2 och har ett eget datum. 2023-avvikelsen blir −0,19 och snittet 0,11 (var 0,10). Tabellerna ovan är uppdaterade. |
| 2. Belägg för 2020 och 2022 är statusdatum i senare rapporter, inte publiceringsdatum (wrong) | **Stämmer.** Rapporten med "mitten av mars 2020" laddades upp 2020-12-17, och rapporten med "20 april 2022" är verksamhetsberättelsen 2022 (2023). | 30 juni gäller nu bara år med belagd vårpublicering: 2023, 2025, 2026. Övriga år får known_from = källrapportens uppladdningsdatum (`Last-Modified`) via `catalog_rents.RELEASES` → `publication.LATE_RELEASES`. Releasetabell med belägg i publiceringskalendern. Testet låser att varje år har exakt en sorts datum. |
| 3. Backfill ger slutligt värde från 30 juni, fast vårens siffra var preliminär (minor) | **Löst genom fynd 2.** För obelagda år är värdet nu känt först när källan med just det värdet publicerades. För 2023, 2025 och 2026 är det sparade värdet vårens siffra (4,16, 4,8, 3,4). Inga separata vintages byggs. Den tidigare vårsiffran för 2020 (1,93) och 2024 (5,2) används inte, vilket kostar information men inte läcker. | Ingen extra vintage-mekanism. Det hade krävt skrivning förbi `upsert`. |
| 4. `kpi_rent_index` före 2026 är omräknade värden som inte fanns i realtid (minor) | **Stämmer.** | Not i publiceringskalendern och ovan. Ingen ny realtidsserie byggd. Det är en egen hämtning som får göras i våg 2 vid behov. |
| 5. resultat.md säger att `fetch` läser tabellen, men det finns ingen `fetch()` (minor) | **Stämmer.** | Texten är rättad: `negotiated()` är Spec:ens fetch-funktion. |

Inget fynd avvisades.

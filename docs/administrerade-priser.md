# Administrerade priser: kalender och förslag till manuell justering (L1)

Uppdaterad 2026-11-23 (körning 3, spår L1, rättad efter granskning samma dag; primärkällkontroll i spår L1b, se nedan). Kod: `src/kpif_nowcast/admin_calendar.py` (`ADMIN_EVENTS`).
Kalendern bygger på K13:s skattekalender ([skattekalender.md](skattekalender.md), `k13_tax.EVENTS`): K13:s åtta
skattehändelser läses in därifrån och dupliceras inte. `k13_tax.EVENTS` är oförändrad, så K13:s registrerade
varianter går att reproducera. L1 lägger till avgifter, subventioner, reglering, äldre skatter och 2027–2028.

## Användning i månadsrutinen (steg 2)

```
python -m kpif_nowcast.admin_calendar 2026-12
```

Kommandot skriver ut händelserna i prognosmånaden, summan i pe på KPIF m/m, omräkningen till årstakt och en
färdig rad `python -m kpif_nowcast.forecast --adjust <pe> --note "<händelser, källor>"`. Det är ett förslag.
Användningen beslutar Johannes. `python -m kpif_nowcast.admin_calendar --table` skriver tabellen nedan.

## Metod

- **En rad per händelse:** ikraftträdandemånad (första månaden SCB mäter det nya priset), SCB:s COICOP-post
  (COICOP 2018, som i tabellen KPIF2020COICOPM), typ, effekt i pe på KPIF m/m, metod, om SCB rensar den i KPIF-KS,
  beslutsdatum ("senast") och källa.
- **Effekten** räknas på ett av fyra sätt:
  - `scb_ks`: SCB:s mekaniska KS-beräkning (KPIF m/m − KPIF-KS m/m, energi- och icke-energidel som i K13);
  - `weight_x_change`: postens KPIF-vikt (promille, SCB [KPIF2020COICOPM](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__PR__PR0101__PR0101G/KPIF2020COICOPM/))
    × antagen prisändring på posten;
  - `observed`: vikt × SCB:s uppmätta m/m för posten i händelsemånaden (bara historik);
  - `assumption`: antagande som står i raden.
  Vikterna är årets KPIF-vikter från SCB (hämtade 2026-11-23, cache `data/raw/l1/`). Vikt × prisändring ger
  bidraget till KPIF m/m så länge postens index ligger nära decembernivån. Efter stora steg (månadskortet efter
  −26 %) skalar den effektiva vikten med postens indexkvot. Därför är återgången lika stor som sänkningen, inte
  större.
- **Typer:** `one_off` (ny nivå, även permanenta ändringar: modellen ser inte steget), `end` (en tillfällig ändring
  upphör) och `recurring` (årlig ändring, t.ex. januaritaxor och indexering). Huvudmodellens säsong är ett
  femårssnitt, så den har redan ett normalt år. För `recurring` räknas bara `pe − normal` in, och bara när båda
  är kända. Normalen är snittet av postens januaribidrag de fem senaste åren. Den är ungefärlig: modellen
  (`seasonal_trend_additive`) avtrendar med 12-månaderssnittet, vilket ger en skillnad på ungefär ±0,005 pe.
- **Läckageregeln (som K13):** en händelse föreslås för månad t bara om beslutet är fattat före deadline(t) = dag 4
  i t+1. Händelser utan beslut står med i kalendern men föreslås aldrig. Testerna låser regeln.
- **Årstakt:** `forecast.py --adjust` gäller årstakten. Summan i m/m multipliceras med index(t−1)/index(t−12),
  ungefär 1,01. Innan t−1 är publicerad används senaste 11-månaderskvot.
- **Ekot visas men ingår inte.** Kommandot visar också vad tidigare engångshändelser bidrar med i huvudmodellens
  12-månaderstrend och femårssäsong (exakt, eftersom `seasonal_trend_additive` är linjär). För 2026-12 är ekot
  −0,12 pe m/m. Det är samma mekanism som K13:s skatterensning. Johannes beslutade 2026-11-23 att inte använda den
  justeringen (beslutsloggen), och K13 fick ingen urvalsevidens för den. Därför står ekot som information.
- **Genomslag:** effekterna förutsätter fullt genomslag. K13 visade att drivmedelsskatterna inte slog igenom fullt
  samma månad (juli 2026: drivmedel −9,4 % mot cirka −15 % mekaniskt), medan matmomsen slog igenom fullt.
- **Regionala kort** fördelas efter befolkningsandel (SCB BE0101N1, 2024): söder (Skåne, Blekinge, Jönköping,
  Kalmar, Kronoberg) 22,7 %, Halland 3,3 %, övriga 74,0 % (varav Västra Götaland 16,7 %). Hur SCB viktar regionerna
  inom 07.3.5 är okänt. Viktas de efter biljettintäkter väger SL mer, och då hamnar mer av effekten i december.
- **Källäget (L1b, 2026-11-23):** varje händelse har ett fält `verified` (kolumnen Verifierad): datum och hur
  den kontrollerades mot primärkälla (proposition, betänkande med riksdagens beslutsdatum ur `dokumentstatus`,
  SFS i riksdagens databas, Skatteverkets skattesatser, regeringens pressmeddelanden), `delvis` eller
  `ej verifierad` med orsak. Beslutsdatum är riksdagens beslut (eller utfärdande av SFS/förordning när det är
  senare och avgör), som "senast"-datum. Regionernas, TV4/TT:s och kommunernas webbplatser är inte nåbara från
  körmiljön, så månadskortens regionala datum är fortfarande overifierade.

## Närmaste månadsrutiner

**2026-12 (rutinen 1–4 jan 2027):** förslag **`--adjust 0.52`** (oförändrat efter L1b):
- **+0,398 pe:** koldioxidskattesänkningen på bensin och diesel upphör 30 nov 2026. Det är minus julis realiserade
  KS-energidel (K13). Verifierat mot primärkällor 2026-11-23: Skatteverkets skattesatser för 1–31 dec 2026 är
  4,79 kr/l på bensin (miljöklass 1) mot 2,39 kr/l okt–nov, alltså +2,40 kr/l (+3,00 kr inkl. moms).
  Övergångsregeringens budgetproposition (prop. 2026/27:1, 12 nov) och höständringsbudgeten (prop. 2026/27:2)
  förlänger inte sänkningen. Prop. 2026/27:1 skriver att skatteintäkterna 2027 ökar när de tillfälliga
  skattesänkningarna "främst på drivmedel" upphör. Riksdagens dokumentlista för 2026/27 har ingen proposition
  eller betänkande om förlängning (sökt på koldioxidskatt, drivmedel, bensin och diesel). Det enda
  förlängningsförslaget gäller jordbrukets diesel (FiU-protokoll 5 nov), som inte påverkar pumppriset för hushåll.
- **+0,115 pe:** månadskorten får fullpris igen från 3 dec i övriga regioner. SL och Västtrafik har sista köpdag
  för halvpris 2 dec. Statsbidraget gäller kort som börjar gälla senast 2 dec.
- Risker: genomslaget i drivmedelspriset (se ovan), och att Västtrafik förlänger halvpriset till 29 dec
  (återremitterat 6 okt 2026). Då flyttas +0,026 till januari. Ändra i så fall raden och kör om.
- Tidpunktsrisk för månadskorten: SL-abonnemang dras med halvpris för december 26 nov, och 30-dagarskort som
  aktiveras 2 dec gäller till ungefär 1 jan. Prissätter SCB kortet efter giltighetsperiod hamnar en del av
  +0,115 i januari. Kontrollera SCB:s KPI-nyhet för december innan januarirutinen.

**2027-01 (rutinen 1–4 feb 2027):** förslag cirka **`--adjust -0.03`**, alltså nära noll:
- +0,005: Halland går tillbaka till fullpris.
- −0,031: prisbasbeloppet höjs bara 0,7 %, och omsorgstaxorna följer det. Normalen i säsongen är +0,041.
  Posten 13.3.0 innehåller också barnomsorg (13.3.0.1), vars maxtaxa inte följer prisbasbeloppet, men hela vikten
  skalas med +1,0 %. Siffran är alltså grov, inom ungefär ±0,01 pe.
- Beslutade men normala, och därför ute: elskatten 36,0 → 36,2 öre/kWh (vanlig indexering, förslaget att låsa
  den genomfördes inte) och indexeringen av drivmedelsskatten.
- Tobaksskatten +3,5 % utöver indexeringen genomförs inte: prop. 2026/27:1 (tabell 1.5) listar den bland
  tidigare aviserade förslag som inte genomförs. Raden står nu som beslutad med effekt 0.
- Elskatten: remissen i maj 2026 (låst på 36,0 öre/kWh) kom inte med i prop. 2026/27:1, så den vanliga
  KPI-indexeringen gäller. Nivån ~36,2 öre/kWh är inte bekräftad av Skatteverket ännu (sidan visar bara 2026).
  Drivmedelsindexeringen är bekräftad av Skatteverket: bensin +10 öre/l, diesel +8,5 öre/l från 1 jan 2027.
- Prisbasbeloppet 59 600 kr (+0,7 %) är bekräftat (SFS 2026:1779, 24 sep 2026).
- Okänt eller inte beslutat: elnätsavgifterna (inga besked 23 nov, se L5) och VA- och avfallstaxorna.
  Kontrollera före rutinen.
- Ekot i januari är −0,155 pe, varav tandvårdsstödet för 67+ i januari 2026 ger 1/5 av −0,19 i säsongen. Det är
  information och ingår inte i förslaget.
- Matmomsen ligger på 6 % hela 2027. Återgången till 12 % (+0,77 pe) kommer i januari 2028.

## Kalender

| Månad | COICOP | Post | Typ | Effekt (pe m/m) | Metod | I KS | Beslut senast | Händelse | Källa | Verifierad |
|---|---|---|---|---|---|---|---|---|---|---|
| 2016-01 | 07.2.2 | Bränslen och smörjmedel | one_off | +0,140 | weight_x_change | ja | 2015-11-25 | Höjd energiskatt på bensin (+48 öre/l) och diesel (+53 öre/l), BP 2016. 0,48 kr × 1,25 moms på ~13,5 kr/l ≈ +4,4 %; SCB KS 2016-01 totalt +0,30 inkl. januarihöjningar. | [1](https://data.riksdagen.se/dokument/H3031) [2](https://data.riksdagen.se/dokumentstatus/H301FiU1) [3](https://www.regeringen.se/rattsliga-dokument/departementsserien-och-promemorior/2015/08/ytterligare-skattehojningar-pa-vissa-drivmedel/) | 2026-11-23: prop. 2015/16:1 (+48/+53 öre/l från 1 jan 2016) läst; beslut bet. 2015/16:FiU1 25 nov 2015. L1:s länk bet. 2015/16:SkU18 var fel (motionsbetänkande, beslut 9 mar 2016) |
| 2016-01 | 07.2.4 | Andra tjänster för personliga transportmedel | one_off | +0,050 | assumption | nej | 2015-12-31 | Höjd trängselskatt i Stockholm (max 60 → 105 kr/dag) och ny avgift på Essingeleden. posten +3,1 % mot normalt −2 % i januari: (3,1+2,0) × 8,98 ‰ ≈ +0,05. | [1](https://www.transportstyrelsen.se/globalassets/global/vag/trangselskatt/infofolder-forandringar-trangselskatt-stockholm-.pdf) | ej verifierad: transportstyrelsen.se inte nåbar från miljön och riksdagsbeslutet inte hittat; L1:s länk bet. 2015/16:SkU18 var fel (beslut 9 mar 2016) och är borttagen |
| 2017-07 | 05.3.1 | Elektronik och vitvaror (flera poster) | one_off | +0,116 | scb_ks | ja | 2016-11-24 | Ny kemikalieskatt på viss elektronik (lag 2016:1067), från 1 juli 2017. SCB KS 2017-07 (+0,116) tillskrivs hela skatten; inga andra kända skatteändringar. | [1](https://data.riksdagen.se/dokument/sfs-2016-1067) [2](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/kemikalieskatt/nyareglerforattdeklarerakemikalierivisselektronik.4.7361717f187e3364e41101b.html) | 2026-11-23: SFS 2016:1067 utfärdad 24 nov 2016 (riksdagens SFS-databas); storleken är SCB:s KS |
| 2018-04 | 07.3.3 | Persontransport med flyg | one_off | +0,041 | scb_ks | ja | 2017-11-30 | Ny flygskatt (lag 2017:1200), från 1 april 2018. SCB KS 2018-04. | [1](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/lag-20171200-om-skatt-pa-flygresor_sfs-2017-1200/) | 2026-11-23: SFS 2017:1200 utfärdad 30 nov 2017 (riksdagens SFS-databas) |
| 2019-01 | 08.3.9 | Andra informations- och kommunikationstjänster | one_off | +0,000 | assumption | nej | 2018-11-14 | Radio- och tv-avgiften ersätts av public service-avgift via skatten; SCB länkar ut avgiften utan priseffekt. SCB: utanför KPI:s målpopulation, utlänkad utan prispåverkan (vikten 11,2 → 6,0 ‰). | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-januari-2019/) [2](https://www.scb.se/contentassets/d1f974c3e55d4ff39fa6314fc211980c/andringar_i_kpi_fran_2019_v002.pdf) | 2026-11-23: prop. 2017/18:261, riksdagsbeslut bet. 2018/19:KrU2 14 nov 2018 (dokumentstatus) |
| 2019-07 | 06.2.2 | Öppen tandvård | one_off | −0,187 | observed | ja | 2019-08-14 | Ny metod för allmänt tandvårdsbidrag (ATB) i KPI: tandvård faller varje juli (återkommande från 2020). metodbyte hos SCB, inte ett politiskt beslut; beslut = SCB:s publicering 14 aug 2019 (efter deadline för 2019-07, så aldrig föreslagen). Juli −12 till −20 % varje år sedan dess. | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-juli-2019/) | 2026-11-23: SCB:s KPI-nyhet juli 2019 (länken fungerar) |
| 2022-05 | 07.2.2 | Bränslen och smörjmedel | one_off | −0,258 | scb_ks | ja | 2022-04-30 | Tillfälligt sänkt energiskatt på bensin och diesel 1,05 kr/l, maj–sep 2022. (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/H903221) [2](https://data.riksdagen.se/dokumentstatus/H901FiU39) | 2026-11-23: prop. 2021/22:221 läst; riksdagsbeslut bet. 2021/22:FiU39 27 apr 2022 (dokumentstatus) |
| 2022-10 | 07.2.2 | Bränslen och smörjmedel | end | +0,258 | scb_ks | ja | 2022-04-30 | Sänkningen från maj 2022 upphör 30 sep. (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/H903221) [2](https://data.riksdagen.se/dokumentstatus/H901FiU39) | 2026-11-23: solnedgång 30 sep 2022 i prop. 2021/22:221 (beslut 27 apr 2022); K13:s källa Företagarna (sekundär, inte nåbar) ersatt |
| 2024-01 | 07.2.2 | Bränslen och smörjmedel | one_off | −0,280 | observed | nej | 2023-11-30 | Reduktionsplikten sänks till 6 % (prop. 2023/24:28) och sänkt drivmedelsskatt; ingen skatt för reduktionsplikten, så den rensas inte i KS. hela drivmedelsposten −10,8 % i jan 2024 (övre gräns: inkluderar marknadspris); huvudmodellen ser bara Brent i SEK. | [1](https://data.riksdagen.se/dokument/HB01MJU5) [2](https://www.konj.se/media/1dojjkax/specialstudie-104-sankning-av-reduktionsplikt.pdf) | 2026-11-23: bet. 2023/24:MJU5 beslut 30 nov 2023 (dokumentstatus); Skatteverket: bensin 6,31 → 5,71 kr/l skatt 2023 → 2024. konj.se-länken inte nåbar |
| 2025-05 | 04.3 | Underhåll, reparation och säkerhet avseende bostaden (ROT) | one_off | −0,176 | scb_ks | ja | 2025-05-07 | ROT-avdraget 30 → 50 % 12 maj–31 dec 2025 (finns i K13:s kalender, inte i EVENTS). SCB KS icke-energidel 2025-05 (k13_tax.ks_parts; −0,189 i tax_effects är tax_xe_own, KPIF-XE-skala). Reparationstjänsterna (04.3.2) publiceras inte; publicerade 04.3 är bara material (= 04.3.1, +0,8 % i maj). | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-maj-2025/) [2](https://data.riksdagen.se/dokument/HC03156) [3](https://data.riksdagen.se/dokumentstatus/HC01FiU32) | 2026-11-23: L1:s datum 2025-04-30 var för tidigt. Prop. 2024/25:156 (10 apr 2025), riksdagsbeslut bet. 2024/25:FiU32 7 maj 2025 (dokumentstatus); före deadline för 2025-05 |
| 2025-07 | 06.1.1 | Läkemedel | one_off | +0,011 | observed | nej | 2025-05-22 | Höjt högkostnadsskydd för läkemedel (prop. 2024/25:144). | [1](https://data.riksdagen.se/dokument/HC03144) [2](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-juli-2025/) | 2026-11-23: riksdagsbeslut bet. 2024/25:SoU27 22 maj 2025 (dokumentstatus) |
| 2025-07 | 07.2.2 | Bränslen och smörjmedel | one_off | +0,000 | assumption | ja | 2025-05-22 | Energiskatten på bensin och diesel −32 öre/l samtidigt som reduktionsplikten höjs (+32 öre/l), 1 jul 2025; nettoeffekt på pumppriset ≈ 0. prop. 2024/25:131: skattesänkningen väger upp reduktionspliktens prishöjning. SCB:s KS energidel 2025-07 −0,05 ser bara skatten, så KS-baserade justeringar överskattar effekten. | [1](https://data.riksdagen.se/dokument/HC03131) [2](https://data.riksdagen.se/dokumentstatus/HC01MJU17) [3](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/energiskatter/skattpabransle.4.15532c7b1442f256bae5e56.html) | 2026-11-23: L1b-tillägg. Skatteverket: bensin 5,11 → 4,79 kr/l skatt 1 jul 2025; prop. 2024/25:131 läst; beslut bet. 2024/25:MJU17 22 maj 2025 |
| 2026-01 | 04.3 | Underhåll, reparation och säkerhet avseende bostaden (ROT) | end | +0,037 | scb_ks | ja | 2025-05-07 | ROT 50 % upphör 31 dec 2025 (solnedgång i lagen). hela icke-energidelen av SCB KS 2026-01 (alla januariändringar), så övre gräns för ROT-slutet om övriga ändringar var ≥ 0. Återgången blev mycket mindre än startens −0,176; orsaken är inte verifierad (osäker). | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-januari-2026/) [2](https://data.riksdagen.se/dokumentstatus/HC01FiU32) | 2026-11-23: solnedgång i prop. 2024/25:156, beslut bet. 2024/25:FiU32 7 maj 2025 |
| 2026-01 | 04.5.1 | Elektricitet | one_off | −0,132 | scb_ks | ja | 2025-11-30 | Sänkt energiskatt på el (BP 2026). (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/HD031d2) [2](https://data.riksdagen.se/dokumentstatus/HD01FiU1) | 2026-11-23: prop. 2025/26:1 avsnitt 13.12.2 (36,0 öre/kWh 2026) läst; beslut bet. 2025/26:FiU1 26 nov 2025 |
| 2026-01 | 06.2.2 | Öppen tandvård | one_off | −0,186 | observed | nej | 2025-12-08 | Tandvårdsstöd för 67+ (betalar 10 % av referenspriset), från 1 jan 2026. normal januari +2 till +4 %, så effekten är snarast −0,2 till −0,22. | [1](https://www.regeringen.se/pressmeddelanden/2025/12/tandvarden-for-aldre-blir-billigare-den-1-januari-2026/) [2](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-januari-2026/) | 2026-11-23: regeringen 8 dec 2025: riksdagen röstade 3 dec, förordningarna beslutade 8 dec |
| 2026-04 | 01 | Livsmedel och alkoholfria drycker | one_off | −0,773 | scb_ks | ja | 2026-02-25 | Matmomsen 12 → 6 % 1 apr 2026–31 dec 2027. (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/HD0355) [2](https://data.riksdagen.se/dokumentstatus/HD01SkU9) | 2026-11-23: K13:s beslutsdatum 2025-11-30 är fel. BP 2026 bara aviserade; prop. 2025/26:55 (25 nov 2025), riksdagsbeslut bet. 2025/26:SkU9 25 feb 2026, t.o.m. 31 dec 2027. Före deadline för 2026-04 (4 maj), så K13:s variant påverkas inte |
| 2026-05 | 07.2.2 | Bränslen och smörjmedel | one_off | −0,115 | scb_ks | ja | 2026-04-30 | Tillfälligt sänkt energiskatt på bensin och diesel till EU:s miniminivå, maj–sep 2026. (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/HD03236) [2](https://data.riksdagen.se/dokumentstatus/HD01FiU48) [3](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/energiskatter/skattpabransle.4.15532c7b1442f256bae5e56.html) | 2026-11-23: beslut bet. 2025/26:FiU48 22 apr 2026; Skatteverket: bensin energiskatt 1,52 → 0,70 kr/l 1 maj–30 sep 2026 |
| 2026-07 | 07.2.2 | Bränslen och smörjmedel | one_off | −0,398 | scb_ks | ja | 2026-06-30 | Tillfälligt sänkt koldioxidskatt på bensin och diesel 2,40 kr/l (3,00 inkl. moms), jul–nov 2026. (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/HD03275) [2](https://data.riksdagen.se/dokumentstatus/HD01FiU47) [3](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/energiskatter/skattpabransle.4.15532c7b1442f256bae5e56.html) | 2026-11-23: beslut bet. 2025/26:FiU47 17 jun 2026; Skatteverket: koldioxidskatt bensin −2,40 kr/l 1 jul–30 nov 2026 |
| 2026-07 | 07.3.5 | Kombinerad persontransport | one_off | −0,156 | observed | nej | 2026-06-25 | Halverat pris på månadskort i kollektivtrafiken (statsbidrag) 1 jul–dec 2026. mekaniskt 44 % × −50 % = −22 % (−0,130); uppmätt −26,4 %. Indirekt subvention, rensas inte i KS. | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/produktrelaterat/aktuellt/hantering-i-kpi-och-relaterade-matt-av-reformer-som-infors-i-juli-2026/) [2](https://www.regeringen.se/pressmeddelanden/2026/06/halverade-priser-i-kollektivtrafiken--nu-har-regeringen-beslutat-om-reglerna/) [3](https://data.riksdagen.se/dokument/sfs-2026-1391) | 2026-11-23: anslag bet. 2025/26:FiU47 17 jun 2026; SFS 2026:1391 utfärdad 25 jun 2026 (bidrag för kort aktiverade senast 2 dec eller giltiga t.o.m. 31 dec 2026) |
| 2026-07 | 09.4.6 | Rekreations- och sporttjänster | one_off | ? | assumption | ja | 2026-05-20 | Dansbandsmoms 25 → 6 % (rensas i KS, försumbar). | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/produktrelaterat/aktuellt/hantering-i-kpi-och-relaterade-matt-av-reformer-som-infors-i-juli-2026/) [2](https://data.riksdagen.se/dokumentstatus/HD01SkU25) | 2026-11-23: prop. 2025/26:109, beslut bet. 2025/26:SkU25 20 maj 2026 (dokumentstatus) |
| 2026-07 | 10.1.0 | Förskola | one_off | −0,056 | observed | nej | 2026-06-30 | Fribelopp i maxtaxan för förskola (permanent). taxeändringar rensas inte i KS. | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/produktrelaterat/aktuellt/hantering-i-kpi-och-relaterade-matt-av-reformer-som-infors-i-juli-2026/) [2](https://data.riksdagen.se/dokument/HD031d18) | delvis: BP 2026 utgiftsområde 16 aviserar fribeloppet, anslaget beslutat 16 dec 2025 (bet. 2025/26:UbU1); förordningen inte hittad. Storleken är SCB:s uppmätta juli 2026 |
| 2026-07 | 13.3.0 | Socialt skydd (fritidshem) | one_off | −0,036 | observed | nej | 2026-06-30 | Fribelopp i maxtaxan för fritidshem (permanent). | [1](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/produktrelaterat/aktuellt/hantering-i-kpi-och-relaterade-matt-av-reformer-som-infors-i-juli-2026/) [2](https://data.riksdagen.se/dokument/HD031d18) | delvis: som förskolan (BP 2026 UO16, bet. 2025/26:UbU1 16 dec 2025) |
| 2026-10 | 07.2.2 | Bränslen och smörjmedel | end | +0,115 | scb_ks | ja | 2026-04-30 | Energiskattesänkningen från maj 2026 upphör 30 sep. (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/HD03236) [2](https://data.riksdagen.se/dokumentstatus/HD01FiU48) [3](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/energiskatter/skattpabransle.4.15532c7b1442f256bae5e56.html) | 2026-11-23: Skatteverket: bensin 1,57 → 2,39 kr/l skatt från 1 okt 2026 |
| 2026-11 | 07.3.5 | Kombinerad persontransport | end | +0,035 | assumption | nej | 2026-10-28 | Månadskort åter fullpris från 3 nov i Skåne, Blekinge, Jönköping, Kalmar och Kronoberg. +0,156 (juli omvänt) × befolkningsandel 22,7 %. | [1](https://www.tv4.se/artikel/35OZ9s7vhA6u63p2WPj0ph/da-blir-manadskortet-dubbelt-sa-dyrt-i-ditt-laen) | ej verifierad: TV4/TT och regionernas webbplatser inte nåbara från miljön; SFS 2026:1391 tillåter halvpris till 2 dec, så regionerna får sluta tidigare |
| 2026-12 | 07.2.2 | Bränslen och smörjmedel | end | +0,398 | scb_ks | ja | 2026-06-30 | Koldioxidskattesänkningen upphör 30 nov 2026 (ingen förlängning i BP 2027). (K13) | [skattekalender](skattekalender.md) [1](https://data.riksdagen.se/dokument/HD03275) [2](https://data.riksdagen.se/dokumentstatus/HD01FiU47) [3](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/energiskatter/skattpabransle.4.15532c7b1442f256bae5e56.html) [4](https://data.riksdagen.se/dokument/HE031d2) | 2026-11-23: Skatteverket: bensin miljöklass 1 2,39 → 4,79 kr/l skatt, diesel 3 961 kr/m³ från 1 dec 2026; inget förlängningsförslag i prop. 2026/27:1 (12 nov) eller höständringsbudgeten (prop. 2026/27:2), inga sådana propositioner eller betänkanden i riksdagens dokumentlista |
| 2026-12 | 07.3.5 | Kombinerad persontransport | end | +0,115 | assumption | nej | 2026-10-28 | Månadskort åter fullpris från 3 dec i övriga regioner (SL och Västtrafik: sista köpdag 2 dec). +0,156 × 74,0 % (alla utom söder och Halland). Förlänger Västtrafik till 29 dec flyttas +0,026 till 2027-01. Risk: SL-abonnemang dras med halvpris för december 26 nov och 30-dagarskort aktiverade 2 dec gäller till ~1 jan; prisar SCB efter giltighetstid hamnar en del i januari. | [1](https://www.tv4.se/artikel/35OZ9s7vhA6u63p2WPj0ph/da-blir-manadskortet-dubbelt-sa-dyrt-i-ditt-laen) [2](https://www.dagensps.se/privatekonomi/manadskortet-dubbelt-sa-dyrt-2027-men-har-kan-du-behalla-rabatten-i-januari/) | delvis: sista dag 2 dec stämmer med SFS 2026:1391 4 § (kort aktiverade senast 2 dec 2026); regionernas egna besked (SL, Västtrafik) inte nåbara från miljön |
| 2027-01 | 02.3 | Tobak | one_off | +0,000 | assumption | ja | 2026-11-12 | Aviserad tobaksskatt +3,5 % utöver indexering genomförs inte (prop. 2026/27:1 tabell 1.5); bara ordinarie indexering. indexeringen är normal och ligger i säsongen. | [1](https://www.regeringen.se/rattsliga-dokument/departementsserien-och-promemorior/2025/11/hojd-skatt-pa-viss-tobak/) [2](https://data.riksdagen.se/dokument/HE031d2) | 2026-11-23: prop. 2026/27:1 tabell 1.5 och avsnitt 12: 'Höjd skatt på vissa tobaksprodukter' bland tidigare aviserade förslag som inte genomförs (−0,32 mdkr). PM 27 nov 2025 läst |
| 2027-01 | 04.4 | Vattenförsörjning (04.4.1), sophämtning (04.4.2) och avlopp (04.4.3) | recurring | ? | assumption | nej | ej beslutad | Kommunala VA- och avfallstaxor i januari (2024: VA +13,9 %, 2025 +9,8 %, 2026 +6,5 %). | [1](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__PR__PR0101__PR0101G/KPIF2020COICOPM/) | ej verifierad: 290 kommunala taxebeslut, ingen samlad källa |
| 2027-01 | 04.5.1 | Elektricitet | recurring | +0,004 | assumption | ja | 2026-11-12 | Energiskatt på el 36,0 → ~36,2 öre/kWh (ordinarie KPI-indexering; förslaget att låsa på 36,0 lades inte i BP 2027). 0,25 öre inkl. moms på ~180 öre/kWh ≈ +0,14 % × 31,8 ‰; normal indexering, säsongen har den. | [1](https://www.regeringen.se/regeringens-politik/skatt-och-tull/skatteforslag-som-remitterats-infor-hostbudgeten-2027/) [2](https://data.riksdagen.se/dokument/HE031d2) [3](https://toreenergi.se/energiskatt-2027/) | delvis: remissen (18 maj 2026) föreslog 36,0 öre/kWh 2027 men prop. 2026/27:1 (12 nov) lägger bara inkomstskatteförslag, så indexeringen i 11 kap. 3 § LSE gäller (regeringen fastställer före november månads utgång). Nivån 36,2 och SFS 2026:1859 kommer från toreenergi.se (inte nåbar); Skatteverket visar ännu bara 2026 |
| 2027-01 | 04.5.1 | Elektricitet (elnät) | recurring | ? | assumption | nej | ej beslutad | Elnätsavgifter i januari (Ellevio, Vattenfall, E.ON): inga 2027-besked hittade 23 nov 2026; se L5. | [1](https://www.svt.se/nyheter/inrikes/elnatsjattarna-hojer-avgiften-kraftigt) | ej verifierad: ingen samlad primärkälla (se L5); svt.se inte nåbar |
| 2027-01 | 07.2.2 | Bränslen och smörjmedel | recurring | +0,016 | assumption | ja | 2026-11-23 | Ordinarie indexering av skatt på bensin (+10 öre/l) och diesel (+8,5 öre/l). 12,5 öre inkl. moms på ~20 kr/l ≈ +0,6 % × 26,4 ‰; normal indexering. | [1](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/energiskatter/skattpabransle.4.15532c7b1442f256bae5e56.html) | 2026-11-23: Skatteverket: bensin miljöklass 1 4,79 → 4,89 kr/l, diesel miljöklass 1 3 961 → 4 046 kr/m³ från 1 jan 2027. Beslutsdatum = dag för kontrollen (övre gräns); hurbra.se (sekundär) ersatt |
| 2027-01 | 07.3.5 | Kombinerad persontransport | end | +0,005 | assumption | nej | 2026-10-28 | Halland: rabatterat kort kan aktiveras till 1 jan, fullpris i januari. +0,156 × 3,3 %. | [1](https://www.tv4.se/artikel/35OZ9s7vhA6u63p2WPj0ph/da-blir-manadskortet-dubbelt-sa-dyrt-i-ditt-laen) | ej verifierad: hallandstrafiken.se och TV4 inte nåbara. Obs: SFS 2026:1391 ger bara bidrag för kort aktiverade senast 2 dec eller giltiga t.o.m. 31 dec, så aktivering till 1 jan är regionens egen kostnad |
| 2027-01 | 07.3.5 | Kombinerad persontransport | end | +0,026 | assumption | nej | ej beslutad | Västtrafik: förlängning av halva priset till 29 dec (återremitterad 6 okt 2026, ej beslutad). om beslutad: flytta +0,026 från 2026-12 hit. | [1](https://via.tt.se/pressmeddelande/4582212/regionfullmaktige-6-oktober-2026?lang=sv) | ej verifierad: via.tt.se och vgregion.se inte nåbara från miljön |
| 2027-01 | 13.3.0 | Socialt skydd (äldreomsorg, maxtaxor) | recurring | +0,010 (normal +0,041) | weight_x_change | nej | 2026-09-24 | Prisbasbeloppet 2027 +0,7 % (59 600 kr); maxtaxor i omsorgen följer det. posten följer prisbasbeloppet i januari (pbb +0,6/+8,7/+9,1/+0,7 % gav 2021 +0,6, 2023 +4,7, 2024 +11,2, 2026 +1,2 %), antag +1,0 %; normal = snitt av januaribidragen 2022–2026 (ungefärlig: modellen avtrendar med 12-månaderssnittet, skillnad ≈ ±0,005 pe). Posten innehåller barnomsorg (13.3.0.1), vars maxtaxa inte följer prisbasbeloppet, men hela vikten skalas med +1,0 %. | [1](https://www.regeringen.se/pressmeddelanden/2026/09/prisbasbeloppfor-2027-faststallt/) [2](https://data.riksdagen.se/dokument/sfs-2026-1779) | 2026-11-23: SFS 2026:1779 utfärdad 24 sep 2026 (59 600 kr, förhöjt 60 900 kr); regeringen: +0,7 % mot 2026 |
| 2028-01 | 01 | Livsmedel och alkoholfria drycker | end | +0,773 | assumption | ja | 2026-02-25 | Matmomsen 6 → 12 % igen (sänkningen gäller t.o.m. 31 dec 2027). minus K13:s KS-effekt 2026-04. | [1](https://data.riksdagen.se/dokument/HD0355) [2](https://data.riksdagen.se/dokumentstatus/HD01SkU9) | 2026-11-23: prop. 2025/26:55 (t.o.m. 31 dec 2027), beslut bet. 2025/26:SkU9 25 feb 2026; L1:s datum 2025-11-30 (från K13) var för tidigt |

Typ `recurring` med "normal" visar normalen i säsongen. "ej beslutad" betyder att händelsen aldrig föreslås.
Siffrorna för K13:s slutmånader (2022-10, 2026-10, 2026-12) är minus startmånadens realiserade KS-del, som i
`k13_tax.addback`. Utan lokal data används minus startmånadens `pe`.

## Primärkällkontroll (L1b, 2026-11-23)

Alla 35 händelser (L1:s 26, en ny och K13:s åtta) är kontrollerade mot primärkälla där det gick. Före/efter för
de närmaste rutinerna: **2026-12 +0,52 → +0,52**, **2027-01 −0,03 → −0,03**. Inga förslag ändrades, men källorna
och flera beslutsdatum gjorde det.

Rättelser:
- **2016-01 drivmedel:** länken till bet. 2015/16:SkU18 var fel (motionsbetänkande, beslut 9 mars 2016, efter
  händelsen). Rätt är prop. 2015/16:1 (+48/+53 öre/l), beslut bet. 2015/16:FiU1 25 nov 2015. Samma felaktiga länk
  är borttagen från trängselskatten 2016, vars beslut inte gick att hitta (overifierad).
- **2025-05 ROT** (och ROT-slutet 2026-01): beslutet var 7 maj 2025 (bet. 2024/25:FiU32), inte "senast 30 april".
  Det angivna datumet låg alltså före det verkliga beslutet. Det påverkar inte förslaget (deadline 4 juni 2025).
- **2026-04 matmomsen** (K13) och **2028-01 återgången**: BP 2026 bara aviserade sänkningen. Lagen kom i
  prop. 2025/26:55 (25 nov 2025) och riksdagen beslutade 25 feb 2026 (bet. 2025/26:SkU9), inte "senast 30 nov
  2025". Det ligger före deadline för 2026-04 (4 maj 2026), så K13:s variant påverkas inte. Kalendern använder
  det verifierade datumet (`K13_DECIDED_FIX`), `k13_tax.EVENTS` är oförändrad.
- **2027-01 tobak:** "ej beslutad" → beslutad att inte genomföras (effekt 0), prop. 2026/27:1.
- **2027-01 drivmedelsindexering:** sekundärkällan (hurbra.se) ersatt med Skatteverket; nivåerna stämde.
- **Ny rad 2025-07 drivmedel (effekt 0):** energiskatten sänktes 32 öre/l 1 juli 2025 samtidigt som
  reduktionsplikten höjdes med motsvarande prispåverkan (prop. 2024/25:131, bet. MJU17 22 maj 2025). SCB:s KS-mått
  ser bara skatten (energidel −0,05 i juli 2025), så KS-baserade justeringar för den månaden vore fel.
- Skärpta "senast"-datum utan påverkan på förslag: kemikalieskatten (SFS 24 nov 2016), flygskatten (SFS 30 nov
  2017), public service-avgiften (bet. 2018/19:KrU2 14 nov 2018), läkemedel (bet. SoU27 22 maj 2025),
  tandvård 67+ (förordning 8 dec 2025), månadskorten (SFS 2026:1391 25 juni 2026), dansbandsmomsen (bet. SkU25
  20 maj 2026), prisbasbeloppet (SFS 2026:1779 24 sep 2026).

Inte verifierat (BLOCKED i miljön): regionernas besked om månadskort (Skånetrafiken, SL, Västtrafik,
Hallandstrafiken, TV4/TT, via.tt.se), trängselskatten 2016 (Transportstyrelsen), elnätsavgifterna 2027, VA- och
avfallstaxorna, elskattens exakta nivå 2027 (toreenergi.se; Skatteverket har inte publicerat 2027 ännu).
Förordningen om fribeloppet i maxtaxan hittades inte (anslaget är beslutat, storleken är SCB:s mätning).

## Inte med, och varför
- **Återkommande januariändringar** av hyror, VA, sophämtning, elnät, kollektivtrafik och punktskatter (indexering)
  syns i SCB:s data varje år och ligger i säsongen. De tas med bara när storleken avviker på ett känt sätt
  (prisbasbeloppet 2027). Kända januarier med stora avvikelser: VA +8 % 2023, +13,9 % 2024 och +9,8 % 2025;
  sophämtning +10,2 % 2023; omsorgstaxor +11,2 % 2024 (prisbasbeloppet +9,1 %).
- **Tandvård i juli** (ATB fylls på, −12 till −20 % varje juli sedan SCB:s metodbyte 2019) är återkommande. Bara
  metodbytet 2019 står som händelse.
- **Läkarvård:** avgiftsfri öppenvård för 85+ (2017) syns inte i data (annan öppenvård +2,5 % i jan 2017) och
  saknar belagd storlek. Den står inte med.
- **Plastpåseskatten** (maj 2020) och **momsen på e-böcker** (juli 2019) är försumbara (KS ≤ 0,03).
- **Elprisstödet** och högkostnadsskyddet för el gäller elpriset, inte en administrerad avgift. El modelleras i J2.

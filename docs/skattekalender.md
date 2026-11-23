# Skattekalender för KPIF 2005–2027

Uppdaterad 2026-11-23 (K13). Kalendern används av `src/kpif_nowcast/k13_tax.py` (`EVENTS`) och av månadsrutinens
steg 2 (manuell justering för beslutade engångshändelser).

## Hur effekten mäts
- **SCB:s mekaniska effekt:** `tax_total = KPIF m/m − KPIF-KS m/m` (KPIF med konstant skatt, TAB6592). KS-måtten
  rensar *direkta* effekter av skatter och subventioner med antagande om fullt och omedelbart genomslag. Avgifter
  (kollektivtrafik, förskola) och indirekta subventioner rensas inte (SCB, se nedan).
- **Uppdelning energi/övrigt (från 2020):** icke-energidel `ne = (KPIF-XE m/m − KPIF-XE-KS m/m)·(1 − w_energi)`,
  energidel `en = tax_total − ne` (TAB6593, TAB6746).
- Siffrorna nedan är pe på KPIF:s månadsförändring. I årstakt blir effekten ungefär lika stor i tolv månader
  (den ligger kvar tills den faller ur jämförelsen eller skatten ändras tillbaka).
- **Beslutsdatum** anges som "senast"-datum (riksdagsbeslutet låg före). Läckageregeln i modellen: en händelse
  får användas för prognosmånad t bara om beslutsdatum < deadline(t) = dag 4 i t+1.

## Händelser som rensas i K13 (`EVENTS`)

| Månad | Komp. | KS-del (pe) | Händelse | Beslut senast | Källa |
|---|---|---|---|---|---|
| 2022-05 | energi | −0,258 | Tillfälligt sänkt energiskatt på bensin och diesel, 1,05 kr/l (1,31 kr inkl. moms), 1 maj–30 sep 2022 | 2022-04-30 | [prop. 2021/22:221](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/proposition/extra-andringsbudget-for-2022-tillfalligt-sankt_h903221/html/) |
| 2022-10 | energi | +0,148 (tillägg ex ante: +0,258) | Sänkningen upphör 30 sep 2022 | 2022-04-30 (solnedgång i lagen) | [Företagarna](https://www.foretagarna.se/nyheter/riks/2022/oktober/slut-for-tillfalligt-sankta-drivmedelspriser) |
| 2026-01 | energi | −0,132 | Sänkt energiskatt på el (budgetpropositionen för 2026) | 2025-11-30 | KS-uppdelningen; [skatteförslag inför BP 2027](https://regeringen.se/regeringens-politik/skatt-och-tull/skatteforslag-som-remitterats-infor-hostbudgeten-2027/) (elskatten låses på 36,0 öre/kWh 2027) |
| 2026-04 | livsmedel | −0,773 | Matmomsen halveras 12 → 6 %, 1 apr 2026–31 dec 2027 | 2025-11-30 | Beslutsloggen fas 4b (regeringen); [SCB KPI april 2026](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-april-2026/) (livsmedel −5,5 % m/m) |
| 2026-05 | energi | −0,115 | Tillfälligt sänkt energiskatt på bensin och diesel till EU:s miniminivå (bensin −0,82 kr/l, diesel −319 kr/m³), 1 maj–30 sep 2026 | 2026-04-30 | [prop. 2025/26:236, bet. 2025/26:FiU48](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/betankande/extra-andringsbudget-for-2026-sankt-skatt-pa_hd01fiu48/html/) (utskottet 21 april); [Skatteverket](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/nyheterinompunktskatter/2026/nyheterinompunktskatter/tillfalligtsanktskattpabensinochdieselfranden1maj2026.5.350d33b019d68128e861b4f.html) (publ. 23 april) |
| 2026-07 | energi | −0,398 | Tillfälligt sänkt koldioxidskatt på bensin och diesel, 2,40 kr/l (3,00 kr inkl. moms), 1 jul–30 nov 2026 | 2026-06-30 | [prop. 2025/26:275](https://data.riksdagen.se/dokument/HD03275.html) (28 maj); [Skatteverket](https://www.skatteverket.se/foretag/skatterochavdrag/punktskatter/nyheterinompunktskatter/2026/nyheterinompunktskatter/tillfalligtsanktkoldioxidskattpabensinochdiesel.5.3129d65419ef1497c06893.html); [SCB:s hantering juli 2026](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/produktrelaterat/aktuellt/hantering-i-kpi-och-relaterade-matt-av-reformer-som-infors-i-juli-2026/) |
| 2026-10 | energi | +0,105 (tillägg ex ante: +0,115) | Energiskattesänkningen från maj upphör 30 sep 2026 | 2026-04-30 | som 2026-05 |
| **2026-12** | energi | (tillägg ex ante: **+0,398**) | **Koldioxidskattesänkningen upphör 30 nov 2026** | 2026-06-30 | som 2026-07; inget beslut om förlängning hittat 2026-11-23 |

**Storleken i startmånader** (`pe` i koden) är SCB:s KS-siffra. Den är en mekanisk beräkning (skatteändring ×
vikt, fullt genomslag) som går att göra före deadline, men själva siffran publiceras efter. Egna kontroller ex ante:
- Matmomsen: 1,06/1,12 − 1 = −5,36 % på varor med 12 % moms; KS-effekten −0,77 motsvarar en vikt på ~14,4 % (livsmedel
  och alkoholfria drycker), rimligt. SCB uppmätte −5,5 % för livsmedel i april.
- Koldioxidskatten: 3,00 kr/l inkl. moms på ett pumppris kring 19–21 kr ≈ −14 till −16 %; KS −0,40 motsvarar en
  drivmedelsvikt på ~2,7 %, rimligt.
- Slutmånader använder minus startmånadens realiserade KS-del (helt ex ante). 2022-10 visar att det kan slå fel:
  +0,258 ex ante mot +0,148 realiserat.

## Med i KS men inte rensat (motivering)
| Månad | KS (pe) | Vad | Varför inte |
|---|---|---|---|
| varje januari | +0,1 till +0,3 | Indexering och höjning av punktskatter (tobak, alkohol, energi) | Återkommande, fångas av säsongen (fas 4b: att rensa dem gjorde det sämre) |
| varje juli 2019–2025 | −0,17 till −0,26 | Återkommande julieffekt i KS (icke-energi) | Återkommande, fångas av säsongen |
| 2012-01 | −0,22 (inkl. januarihöjningar) | Restaurangmomsen 25 → 12 % | Ingen energi/icke-energi-uppdelning före 2020. Tjänstebidraget visar inget synligt genomslag (residual −0,01 pe), så att rensa med fullt genomslag hade lagt in ett fel. Valet gjordes efter att ha sett residualen, före variantkörningen |
| 2025-05 | −0,19 (icke-energi) | ROT-avdraget 30 → 50 %, 12 maj–31 dec 2025 ([SCB KPI maj 2025](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-maj-2025/), avskrivningar egnahem −0,2 pe) | Utgången 2026-01 sammanfaller med tandvårdsstödet för 67+ (−) och januarihöjningarna; de tar ungefär ut varandra (KS icke-energi 2026-01 = +0,04). Påverkar inte prognosen för 2026-11 |
| 2006-10, 2009-05, 2019-07 | −0,19, −0,38, −0,26 | Ej identifierade (2019-07 är början på julimönstret) | Påverkar inte säsongen för 2015 och framåt (2006, 2009) eller är återkommande |

## Inte i KS: avgifter och subventioner som SCB inte rensar
| Månad | Effekt | Vad | Källa |
|---|---|---|---|
| 2026-01 | tandvård −22 % år/år, ~−0,2 pe på KPI | Tandvårdsstöd för 67+ | SCB KPI april och oktober 2026 |
| 2026-07 | lokaltrafik −26 % m/m, −0,2 pe | Halverat pris på månadskort i kollektivtrafiken 1 jul–31 dec 2026 (statsbidrag till regionerna). Indirekt subvention, rensas inte i KS | [SCB:s hantering juli 2026](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/produktrelaterat/aktuellt/hantering-i-kpi-och-relaterade-matt-av-reformer-som-infors-i-juli-2026/), [SCB KPI juli 2026](https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-juli-2026/) |
| **2026-11** | **~+0,03 till +0,05 pe** (grov) | Ordinarie pris på månadskort igen från 3 nov i Skåne, Blekinge, Jönköping, Kalmar och Kronoberg (~1/4 av befolkningen) | [TV4/TT 28 okt 2026](https://www.tv4.se/artikel/35OZ9s7vhA6u63p2WPj0ph/da-blir-manadskortet-dubbelt-sa-dyrt-i-ditt-laen) |
| **2026-12** | **~+0,15 pe** (grov) | Ordinarie pris från 2–3 dec i övriga län (SL, Västtrafik m.fl.; Halland förlängt) | samma |
| 2026-07 | liten | Sänkt förskole-/fritidshemstaxa (fribelopp), sänkt dansbandsmoms (rensas i KS, försumbar) | SCB:s hantering juli 2026 |

Månadskortet räknas grovt så här: −0,2 pe i juli fördelat efter befolkningsandel för de regioner som återgår. SCB:s
urval per region och hur biljetter som köpts före bytet räknas är okänt, så osäkerheten är stor.

## Framåt (2027)
- Matmomsen 6 % till och med 2027-12-31: höjningen tillbaka ger ~+0,77 pe i januari 2028 (utanför 2027).
- Elskatten: förslag att slopa indexeringen och låsa den på 36,0 öre/kWh 2027 (remiss inför BP 2027). Det ger en något
  lägre januarieffekt än vanligt 2027, inte en engångshändelse. Inget beslutat i K13:s källor.
- Budgetpropositionen för 2027 (läggs senast 12 nov, riksdagen röstar ~9 dec 2026) kan innehålla nya skatteändringar
  från 2027-01. Kontrollera före januariprognosen.

## Not: primärkällkontroll (L1b, 2026-11-23)
`k13_tax.EVENTS` och tabellerna ovan är oförändrade så att K13:s varianter går att reproducera. Kontrollen mot
primärkällor (riksdagens `dokumentstatus`, propositioner, Skatteverkets skattesatser) gav:
- **2026-04 matmomsen: beslutsdatumet är fel.** BP 2026 aviserade bara sänkningen. Lagen kom i prop. 2025/26:55
  (25 nov 2025) och riksdagen beslutade 25 feb 2026 (bet. 2025/26:SkU9), inte "senast 2025-11-30". Beslutet låg
  före deadline för 2026-04 (2026-05-04), så rensningen och K13:s varianter påverkas inte. `admin_calendar` använder
  det verifierade datumet.
- **2022-10:** källan (Företagarna) är sekundär. Primärkälla: solnedgången 30 sep 2022 i prop. 2021/22:221, beslut
  bet. 2021/22:FiU39 27 apr 2022 (före K13:s "senast"-datum 2022-04-30, alltså korrekt).
- **2026-01 elskatten:** länken om att låsa elskatten på 36,0 öre/kWh 2027 gäller en remiss (maj 2026) som inte
  kom med i övergångsregeringens prop. 2026/27:1. Den ordinarie indexeringen gäller 2027. Själva händelsen
  (36,0 öre/kWh 2026, prop. 2025/26:1 avsnitt 13.12.2, beslut bet. 2025/26:FiU1 26 nov 2025) stämmer.
- **2022-05, 2026-05, 2026-07:** riksdagens beslut 27 apr 2022 (FiU39), 22 apr 2026 (FiU48) och 17 jun 2026
  (FiU47), alla före K13:s "senast"-datum. Storlekarna stämmer med Skatteverket (bensin: energiskatt 1,52 → 0,70
  kr/l maj–sep 2026, koldioxidskatt −2,40 kr/l jul–nov 2026).
- **2026-12:** bekräftat. Skatteverkets skattesatser för 1–31 dec 2026 är 4,79 kr/l på bensin (miljöklass 1) mot
  2,39 kr/l i okt–nov. Ingen förlängning i prop. 2026/27:1 eller prop. 2026/27:2, och inget förslag i riksdagens
  dokumentlista 2026/27.
- **Framåt (2027):** prop. 2026/27:1 är lämnad (12 nov 2026). Den innehåller bara ett inkomstskatteförslag, och den
  aviserade tobaksskattehöjningen (+3,5 %) genomförs inte (tabell 1.5). Drivmedelsindexeringen från 1 jan 2027:
  bensin +10 öre/l, diesel +8,5 öre/l (Skatteverket).
- **Saknas i kalendern, men utan nettoeffekt:** 1 jul 2025 sänktes energiskatten på bensin och diesel 32 öre/l
  samtidigt som reduktionsplikten höjdes (prop. 2024/25:131). KS-energidelen −0,05 i juli 2025 är alltså inte en
  pumpprisändring. Står som rad med effekt 0 i `admin_calendar`.


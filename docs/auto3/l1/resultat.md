# L1 Administrerade priser: resultat

Spår L1 i körning 3, 2026-11-23. Ingen statistisk test (enligt briefen): kalendern är mekanisk och ger ett förslag.
Användningen beslutar Johannes.

## Vad som byggdes
- **`src/kpif_nowcast/admin_calendar.py`:** en handkurerad kalender (`ADMIN_EVENTS`, 26 händelser 2016–2028) plus
  K13:s 8 skattehändelser, som läses in från `k13_tax.EVENTS`. De dupliceras inte, och `EVENTS` är oförändrad.
  Totalt 34 rader. Varje rad har ikraftträdandemånad, SCB:s COICOP 2018-post, typ (`one_off`/`end`/`recurring`),
  effekt i pe på KPIF m/m, metod (`scb_ks`, `weight_x_change`, `observed`, `assumption`), om SCB rensar den i KS,
  beslutsdatum ("senast") och källa.
- **Vikter:** SCB:s KPIF-vikter per COICOP-post och månadsförändringar (KPIF2020COICOPM via api.scb.se), cachade i
  `data/raw/l1/`. Befolkning per län (BE0101N1, 2024) används för de regionala månadskorten.
- **Kommandot `python -m kpif_nowcast.admin_calendar <YYYY-MM>`** skriver händelserna, summan i pe och en färdig
  `--adjust <pe> --note "..."`-rad till `forecast.py`. `--table` skriver kalendertabellen.
- **Läckageregeln är som K13:s:** en händelse föreslås för t bara om beslutet är före dag 4 i t+1. Händelser utan
  beslut föreslås aldrig.
- **Återkommande ändringar** räknas bara med sin avvikelse från säsongens normal.
- **Ekot av tidigare engångshändelser** i huvudmodellens trend och säsong visas som information men ingår inte i
  förslaget, i linje med Johannes beslut om K13 2026-11-23.
- **Dokumentation:** [docs/administrerade-priser.md](../../administrerade-priser.md) med metod, tabell och de
  närmaste rutinerna.
- **Tester:** `tests/test_l1_admin_calendar.py`, 10 tester, körs utan nät. De täcker struktur, att vikt × ändring
  stämmer med pe, att K13 återanvänds utan dubbletter och att `EVENTS` är oförändrad, läckageregeln, normal för
  återkommande ändringar, ekot, kommandot och att dokumentet listar varje händelse.

## Serier
Ingen katalogserie lades till. Det krävdes inte för L1, så publiceringskalendern och datakatalogen är orörda.

## Förslag för de närmaste rutinerna
| Månad | Förslag | Innehåll |
|---|---|---|
| 2026-12 | `--adjust 0.52` | Koldioxidskattesänkningen upphör +0,398 (K13, ingen förlängning i övergångsbudgeten 12 nov); månadskort åter fullpris 3 dec i övriga regioner +0,115 |
| 2027-01 | `--adjust -0.03` | Halland fullpris +0,005; prisbasbeloppet bara +0,7 % → omsorgstaxor −0,031 mot normalt januari. Elnät, VA, avfall okända; tobaksskattehöjningen inte beslutad |
| 2026-11 | `--adjust 0.04` | Månadskort åter fullpris 3 nov i södra Sverige (slutprognosen körs 2 dec utan justering enligt Johannes beslut 2026-11-23) |

Osäkerheter:
- Genomslaget i drivmedelspriset: K13 såg −9,4 % i juli mot cirka −15 % mekaniskt.
- Månadskorten fördelas på regioner efter befolkning, men SCB:s regionvikter är okända.
- Västtrafik kan förlänga halvpriset till 29 dec. Då flyttas +0,026 till januari.
- Tidpunkt för månadskorten: SL-abonnemang dras med halvpris för december 26 nov, och 30-dagarskort som aktiveras
  2 dec gäller till ungefär 1 jan. Prissätter SCB kortet efter giltighetsperiod hamnar en del av +0,115 i januari.
- Omsorgstaxorna i januari är grova (±0,01 pe): posten 13.3.0 innehåller barnomsorg, som inte följer
  prisbasbeloppet, och normalen är ungefärlig (±0,005 pe).

## BLOCKED och begränsningar
- **Primärkällor:** regeringen.se, riksdagen.se och skatteverket.se går inte att nå från miljön (proxyn svarar
  inte). Därför bygger länkarna dit på webbsökning och är inte lästa i sin helhet. SCB:s sidor är lästa direkt.
  För drift behövs inga av dem, eftersom kalendern är handkurerad. Johannes kan lägga till `www.regeringen.se`,
  `www.riksdagen.se`, `data.riksdagen.se` och `www.skatteverket.se` om kalendern ska kunna verifieras automatiskt.
- **Elnätsavgifter 2027:** inga besked från Ellevio, Vattenfall eller E.ON i sökresultaten 23 nov. Raden står kvar
  utan storlek (L5 bygger serien).
- **SL:s taxa 2027:** inget besked hittades. UL (Uppsala) höjer 30-dagarsbiljetten +45 kr från 7 jan 2027. Det är
  för litet för att ta med utan SL.
- **Historik 2015–2025** innehåller identifierade engångshändelser, inte varje kommuns och regions årliga taxa. De
  återkommande januariändringarna syns i SCB:s data och ligger i säsongen.

## Vad kalendern säger om läget i Sverige
De administrativa besluten styr inflationen ovanligt mycket 2026. Siffrorna nedan är den rullande 12-månaderssummen
av engångs- och slut-händelserna (`one_off`/`end`) i kalendern, med fullt genomslag. K13 såg ungefär 60 %
genomslag för drivmedelsskatten i juli, så drivmedelsdelen kan vara överskattad.
- **Okt 2026:** under de senaste tolv månaderna har engångshändelserna sänkt KPIF med cirka **1,7 pe** i årstakt.
  Bidragen är matmomsen −0,77, koldioxidskatten −0,40, tandvård 67+ −0,19, månadskort −0,16, elskatten −0,13 och
  förskola/fritidshem −0,09. Energiskattesänkningen i maj och återgången i oktober tar ut varandra, och ROT-slutet
  (högst +0,04) drar åt andra hållet. Med KPIF på 1,1 % ligger den underliggande takten utan dessa beslut nära 2,8 %.
- **December 2026:** drivmedelsskatten och månadskorten går tillbaka, och då lyfts KPIF m/m med cirka +0,5 pe. I
  årstakt krymper engångseffekten till cirka −1,15 pe.
- **April–juni 2027:** matmomsen faller ur jämförelsen i april. Effekten är då nära noll (−0,07 till +0,05), alltså
  stiger KPIF:s årstakt mekaniskt med drygt 1 pe från december till juni utan att det underliggande trycket ändras.
- **Juli–september 2027:** juli 2026-sänkningarna (koldioxidskatt, månadskort, förskola, fritidshem) faller ur
  jämförelsen, men återgångarna i november och december 2026 ligger kvar. Effekten blir då **+0,7 pe**: KPIF:s
  årstakt ligger över den underliggande takten. Den sjunker till +0,55 i oktober–november och är nära noll i
  december 2027.
- **Januari 2028:** matmomsen går tillbaka till 12 % och ger cirka +0,77 pe, som ligger kvar i årstakten hela 2028.

## Användning i våg 2
- **Som korrektion:** `suggest(t).mm_pe` per månad, eller `pe` per händelse, är en kalendervariabel som är känd
  vid deadline. Den kan prövas som korrektion på bästa skuggmodell och 50/50, eller som händelseindikator för att
  vikta ned händelsemånader i utvärderingen. Det kräver förregistrering. Inga p-värden här.
- **Som rensning:** `echo(t)` ger exakt vad tidigare engångshändelser bidrar med i huvudmodellens trend och säsong.
  Det är samma mekanism som K13:s rensning, men inklusive avgifter (månadskort, förskola, tandvård), som K13
  saknade.
- **I dashboarden:** tabellen och "engångseffekt i årstakt" (−1,7 okt 2026 → −1,15 dec → 0 apr–jun 2027 → +0,7 jul–sep → 0 dec 2027 → +0,8 jan 2028) passar Sverigeläget.

## Granskning
En oberoende granskare lämnade sex fynd. Alla kontrollerades mot källan (kalendern med verklig data, SCB:s
KPIF2020COICOPM-metadata och data via api.scb.se, `k13_tax.ks_parts`, `forecasts/2026-11.json`).

| # | Fynd | Bedömning | Åtgärd |
|---|---|---|---|
| 1 | Läget: effekten är inte "borta efter juli 2027" | Stämmer. Rullande 12-månaderssumma: +0,69 jul–sep 2027, +0,58/+0,54 okt–nov, +0,03 dec 2027. | Avsnittet om läget och dashboardbanan omskrivna. |
| 2 | ROT: −0,19 var `tax_xe_own` (KPIF-XE-skala), +0,19 för slutet saknar stöd | Stämmer. `ks_parts` ger 2025-05 ne −0,176 och 2026-01 ne +0,037 (hela icke-energidelen). | 2025-05 satt till −0,176. 2026-01 satt till +0,037 (`scb_ks`, övre gräns, markerad osäker). Summan för tolv månader till okt 2026 blir −1,70 i stället för −1,55, och den underliggande takten 2,8 % i stället för 2,5 %. Förslagen för 2026-12 och 2027-01 påverkas inte. |
| 3 | Fel COICOP-poster för ROT och VA/avfall | Stämmer. 04.3.1 är material (varor). Tjänsteposten 04.3.2 finns inte i tabellen. Publicerade 04.3 är identisk med 04.3.1 (+0,8 % i maj 2025), så ROT syns inte i någon publicerad post. 04.4.1 är bara vattenförsörjning. | ROT står på `04.3` med not om att 04.3.2 inte publiceras. VA/avfall står på `04.4` med 04.4.1–04.4.3 namngivna. |
| 4 | 2026-11 kallades "redan körd rutin" | Stämmer. `forecasts/2026-11.json` är PRELIMINARY, och slutprognosen körs 2 dec. | Texten rättad. |
| 5 | Kollektivtrafikkällorna är bara delvis verifierbara, och det finns en tidpunktsrisk | Stämmer. Värdarna går inte att nå härifrån (redan BLOCKED). Beslutsdatumen är övre gränser långt före deadline, så det finns ingen läckagerisk. | Tidpunktsrisken (SL-abonnemang 26 nov, 30-dagarskort till ~1 jan) är tillagd i raden, dokumentet och osäkerheterna. |
| 6 | Normalen för `recurring` är ungefärlig; 13.3.0 innehåller barnomsorg | Stämmer, liten effekt. Normalen räknades inte om. | Noten finns i metoden, i raden och i osäkerheterna (±0,005 och ±0,01 pe). −0,031 står kvar inom osäkerheten. |

Inget fynd avvisades. Förslagen till månadsrutinerna är oförändrade: `--adjust 0.52` för 2026-12 och
`--adjust -0.03` för 2027-01.

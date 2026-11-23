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
| 2026-11 | `--adjust 0.04` | Månadskort åter fullpris 3 nov i södra Sverige (redan körd rutin; Johannes valde ingen justering) |

Osäkerheter:
- Genomslaget i drivmedelspriset: K13 såg −9,4 % i juli mot cirka −15 % mekaniskt.
- Månadskorten fördelas på regioner efter befolkning, men SCB:s regionvikter är okända.
- Västtrafik kan förlänga halvpriset till 29 dec. Då flyttas +0,026 till januari.

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
De administrativa besluten styr inflationen ovanligt mycket 2026:
- **Okt 2026:** under de senaste tolv månaderna har engångshändelserna sänkt KPIF med cirka **1,5 pe** i årstakt,
  med fullt genomslag. Det är matmomsen −0,77, koldioxidskatten −0,40, elskatten −0,13, tandvård 67+ −0,19,
  månadskort −0,16 och förskola/fritidshem −0,09, mot ROT-slutet och energiskatteåtergången. Med KPIF på 1,1 %
  ligger den underliggande takten utan dessa beslut nära 2,5 %.
- **December 2026:** drivmedelsskatten och månadskorten går tillbaka, och då lyfts KPIF m/m med cirka +0,5 pe. I
  årstakt krymper engångseffekten till cirka −1,0 pe.
- **Våren 2027:** matmomsen faller ur jämförelsen i april och juli-händelserna i juli. Då försvinner nästan hela
  effekten, och KPIF:s årstakt stiger mekaniskt med ungefär 1 pe under första halvåret 2027 utan att det
  underliggande trycket ändras.
- **Januari 2028:** matmomsen går tillbaka till 12 % och ger cirka +0,77 pe.

## Användning i våg 2
- **Som korrektion:** `suggest(t).mm_pe` per månad, eller `pe` per händelse, är en kalendervariabel som är känd
  vid deadline. Den kan prövas som korrektion på bästa skuggmodell och 50/50, eller som händelseindikator för att
  vikta ned händelsemånader i utvärderingen. Det kräver förregistrering. Inga p-värden här.
- **Som rensning:** `echo(t)` ger exakt vad tidigare engångshändelser bidrar med i huvudmodellens trend och säsong.
  Det är samma mekanism som K13:s rensning, men inklusive avgifter (månadskort, förskola, tandvård), som K13
  saknade.
- **I dashboarden:** tabellen och "engångseffekt i årstakt" (−1,5 → −1,0 → ~0 pe) passar Sverigeläget.

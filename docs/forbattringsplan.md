# Förbättringsplan: autonoma jobb

Skriven 2026-11-22. Planen gäller nästa steg innan drift (fas 6). Varje jobb är tillräckligt
avgränsat för att köras av en agent utan sällskap, och tillräckligt viktigt för att vara
värt det. Inga tidsramar: jobben körs så snabbt det går, parallellt där inget beroende hindrar.

## Utgångsläge

| | MAE 2015–26 (n=141) | Kommentar |
|---|---|---|
| **rb_updated** (Riksbanken + senaste miss) | **0,256** | Ribban att slå |
| Riksbanken | 0,320 | Oftast 2–3 månader gammal vid vår deadline |
| Komponentmodell (drivmedel) | 0,316 | Bästa egna modell på lång historik |
| Naiv | 0,376 | |

Ingen egen modell är i närheten av ribban. För att slå den måste vi tillföra information som
Riksbanken inte hade när prognosen gjordes. Det mesta av den informationen kommer
**mellan prognosomgångens cutoff och vår deadline**: energipriser, euroområdets snabbestimat och
Snabb-KPI för tidigare månader. Den insikten styr ordningen nedan.

Minsta förbättring som går att upptäcka statistiskt på 2015–26 är ca 0,06–0,08 pe.

## Regler för autonoma jobb

1. *(Ändrad 2026-11-23: agenten mergar nu själv till main när pytest är grönt, se CLAUDE.md
   "Agentiskt arbete".)* **Egen worktree och gren** (`auto/<jobb>`) under arbetet. Leveransen var en
   pull request. Lärdom 22 nov: parallella sessioner i samma mapp ger konflikter.
2. **Förregistrera:** hypotes, förväntat tecken och storlek skrivs i `docs/beslutslogg.md`
   ("Min gissning innan") och committas **innan** första körningen.
3. **Modellval på 2015–2026** (eller längre). 2024–2026 är *använd* och rapporteras bara.
4. **Högst 10 varianter per jobb.** Alla loggas i `experiments/runs/`, även de som misslyckas.
5. **Godkänt = slår `rb_updated`**, eller jobbets egen jämförelsemodell, med DM-test p < 0,10
   på 2015–26, utan att bli sämre 2024–26. Annars redovisas resultatet som negativt. Det är ett
   giltigt resultat.
6. **Rör aldrig den skarpa prognosen** (`forecast.py`, `MODEL_NAME`, `forecasts/`). Ett byte av
   huvudmodell beslutar Johannes efter att ha läst PR:en.
7. **Informationsmängd:** allt som används för månad t ska finnas före deadline (dag 4 i t+1),
   via `observations.as_of()` eller med dokumenterad publiceringsfördröjning.
   `tests/test_information_set.py` ska vara grönt.
8. **Hygien:** ingen data i git, inga hemligheter, filer med å/ä/ö redigeras aldrig med
   PowerShell Get/Set-Content.
9. **Slutrapport** i PR-beskrivningen och beslutsloggen: vad som testades, resultat mot ribban,
   vad som inte gick och rekommendation.

## Jobben

Ordnade efter förväntad nytta. Beroenden anges. Varje jobb har en färdig instruktion som kan
ges till en agent rakt av.

### J1. Hybridmodell: Riksbanken + det som hänt sedan (störst förväntad vinst)
**Hypotes:** `rb_updated` saknar bara information efter Riksbankens cutoff. En korrigering för
energiprisrörelser, euroområdets snabbestimat och komponenternas senaste missar slår ribban.
**Uppgift:**
- Bygg `hybrid = rb_updated + korrigering`. Korrigeringen skattas med expanderande fönster på
  nyheter sedan prognosomgångens cutoff: förändring i el- och drivmedelspris jämfört med
  cutoff-månaden, euroområdets snabbestimat minus föregående månad, och avvikelsen i senast
  kända KPIF-komponent mot vår säsongsbaslinje.
- Testa också en enkel kombination: ett viktat snitt av `rb_updated` och komponentmodellen, med
  vikter från tidigare fel.
**Godkänt:** slår `rb_updated` enligt regel 5. Rapportera MAE efter prognosomgångens ålder (1/2/3 mån).
**Beroende:** inget.

### J2. Elmodellen på lång historik
**Hypotes:** med elpriser från 2011 kan elkorrigeringen skattas och utvärderas på 2015–26. Den
förbättrar komponentmodellen (drivmedel) även där, inte bara 2024–26.
**Uppgift:**
- Träna `ENERGY` från 2012 i stället för 2021-12.
- Åtgärda dubbelräkningen av el, där säsongsfaktorn redan innehåller elprisets säsong och
  `el_chg` lägger till den igen. Testa el som avvikelse från säsongsmönstret.
- Testa elpriset gånger andelen rörliga avtal (SCB TAB3571, med hänsyn till revideringar), och
  viktning av elområden efter förbrukning i stället för antagandet 70/30.
- Januari: elnätsavgifter (TAB3950) publiceras först i maj och kan därför bara användas för
  *nästa* januari via en enkel regel. Dokumentera det.
**Godkänt:** `comp_fuel_el` slår `comp_fuel` på 2015–26 enligt regel 5. Rapportera också mot `rb_updated`.
**Beroende:** inget, men resultatet matar J1.

### J3. Systematiskt prognostest av datakatalogen
**Hypotes:** några av de 64 serierna tillför information utöver den bästa basmodellen. De flesta gör det inte.
**Uppgift:**
- För varje månadsserie i `catalog.py`: lägg till serien (point-in-time via `as_of`, rätt
  fördröjning) som korrigering på basmodellen (bästa från J1, annars `rb_updated`) och
  utvärdera på 2015–26.
- Kontrollera för multipla test (Benjamini-Hochberg) och rapportera en rangordnad tabell.
- Föreslå högst tre serier att behålla och testa dem tillsammans en gång.
- Gör samma screening för horisonterna 3 och 12 månader (`horizon.py`).
**Godkänt:** tabellen finns och rekommendationen är förankrad i resultat efter kontrollen för
multipla test. Ett "inget håller" är ett giltigt utfall.
**Beroende:** helst efter J1.

### J4. KPIF underifrån på detaljnivå
**Hypotes:** de stora överraskningarna sitter i några få delindex: el, drivmedel, utrikes resor
och paketresor, hyror och livsmedel. De går att förutse bättre var för sig än som de fem grupperna.
**Uppgift:**
- Med TAB6613 (alla COICOP-nivåer): identifiera de 10–15 delindex som bidrar mest till felet
  2015–26.
- Bygg egna enkla modeller för dem. Hyror är kända i förväg via årliga förhandlingar. Resor har
  stark säsong och påverkas av påskens placering. El och drivmedel finns redan.
- Väg ihop med SCB:s vikter och jämför med femgruppsmodellen.
**Godkänt:** bättre än komponentmodellen på 2015–26 enligt regel 5. **Beroende:** inget.

### J5. Osäkerhet som går att lita på
**Hypotes:** dagens felband (empiriska kvantiler på 34 månader) är för smala i oroliga perioder.
**Uppgift:**
- Bygg prognosintervall med kvantilregression eller konform prediktion på 2015–26 och utvärdera
  träffgrad (50/80/90 %), pinball-förlust och intervallbredd.
- Gör intervallet beroende av läget, till exempel bredare när elpriset svänger mycket.
- Föreslå ändring i `forecast.py` som PR, men aktivera den inte.

**Godkänt:** träffgraden ligger inom ±5 procentenheter från nominell nivå.

### J6. Arbetsförmedlingens data
**Uppgift:**
- Bygg en hämtare för inskrivna arbetslösa och varsel, som Excel-filer från "tidigare statistik"
  med länkar som byts varje månad. Hantera brott i åldersgrupper (2023, 2026) och byte av SNI.
- Lägg till serierna i `catalog.py` med rätt fördröjning (cirka 12 dagar).
- Kör `observations` och `sverige_dashboard`.

**Godkänt:** serierna finns i katalogen med historik från 1992/1996 och klarar kvalitetskontrollen.

### J7. Svensk AI-indikator
**Hypotes:** AI-spridningen syns tidigast i kompetensefterfrågan och investeringar, senare i produktivitet per bransch.
**Uppgift:**
- Validera söktermer i JobTech (AI, maskininlärning, generativ AI, LLM och andra) genom att
  läsa ett stickprov av annonser. Bygg en normerad annonsserie per bransch eller yrke.
- Bygg produktivitet per bransch från SCB:s nationalräkenskaper (förädlingsvärde per timme).
- Sätt ihop en indikator med tydlig metod och jämför Sverige med EU.
- Skriv en kort analys i `docs/ai-indikator.md` och lägg till en sektion i dashboarden.

**Godkänt:** en reproducerbar indikator med dokumenterad metod. Inga orsaksslutsatser utan stöd.

### Återkommande jobb (billiga, schemalagda)
| Jobb | När | Vad |
|---|---|---|
| **Veckohämtning** | Söndagar | `observations` (sparar riktiga vintages), `features`, export av `sverige_dashboard`, kvalitetskontroll. Rapportera nya siffror och avvikelser |
| **Skarp prognos** | 1–4 varje månad | Månadsrutinen i CLAUDE.md. Den första är schemalagd till 2 december |
| **Utvärdering** | ~15:e varje månad | `data`, `scorecard`, uppdatera båda dashboardarna |
| **Månadsbrev** (förslag) | Efter utvärderingen | En kort text om läget i Sverige och prognosen, i `docs/manadsbrev/ÅÅÅÅ-MM.md` |

Veckohämtningen är den viktigaste: varje vecka den körs blir datan mer ärlig, eftersom riktiga vintages sparas.

## Körordning

Styrs bara av beroenden. Allt som kan köras parallellt startas samtidigt, och nästa våg
startar så fort det den behöver är mergat.

```
Våg 1 (oberoende, parallellt):  J2 Elmodellen · J4 Detaljnivå · J5 Osäkerhet · J6 Arbetsförmedlingen · J7 AI-indikator
Våg 2 (efter J2):               J1 Hybridmodell
Våg 3 (efter J1):               J3 Prognostest av katalogen
Löpande:                        veckohämtning, månadsrutin
```

Johannes roll: läsa varje PR:s slutrapport och besluta om merge och om huvudmodellen ska bytas.

## Vad som avgör om planen lyckats

- Minst en modell slår `rb_updated` på 2015–26 med p < 0,10, **eller** vi vet med god grund
  varför det inte går och vilken information som saknas.
- Katalogen och dashboarden uppdateras automatiskt varje vecka.
- Alla jobb har en ärlig slutrapport, även de negativa.

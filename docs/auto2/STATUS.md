# STOP

**Körning 2 är klar (2026-11-23, ca 3,5 h väggtid).** Omstartsuppgiften avslutar direkt när den ser STOP.
Alla spår är **mergade till main** (agentic first, beslut 2026-11-23), slutligt main **129bbb0**, pytest 150 passed / 1 skipped.
Varianter: körning 2 **28/30**, projektet **51**. Alla p-värden är urvalsevidens på 2015–26; inget här betyder att en
modell "slår" rb_updated. Det riktiga testet är skuggprognoserna från 2026-12.

## Slutrapport

### Huvudresultat
1. **ML på residualen klarade urvalsskärmen och håller globalt.** `k2_avg_ridge_l` (ridge på residualen mot 50/50-snittet,
   43 katalogserier) har MAE **0,200** mot 50/50 0,217 och rb_updated 0,256, efter att två läckor rättats (flash-datum, K2b;
   publiceringskalender, K11). Holm 0,018 inom K2, globalt SPA p 0,035 mot rb_updated och 0,025 mot 50/50 över 35 varianter (K12).
   Urvalsbias ≈ 0,022 pe, så vinsten mot 50/50 ligger inom brusbandet i rå MAE men är stabil studentiserat. `k2_avg_ens_s`
   (0,202, Holm 0,082) och `k2_avg_ridge_l` går nu som **skuggprognoser** (2026-11: 1,66 / 1,62 %).
2. **Två verkliga läckor hittades och rättades av granskningsspår:** Eurostats decemberflash publiceras efter dag 4
   (K2b, K11), `gdp_ind_yy` och `hh_consumption_yy` hade för kort fördröjning, och fraktindexet påverkades av USA:s
   shutdown 2025 (K11). `known_from` rättas nu vid inläsning och låses av `tests/test_publication_calendar.py`.
3. **Riktade komponentmodeller hjälpte inte:** tjänster (K7), livsmedel (K8), längre horisont (K9), prisleden (K0),
   nordisk el (K6) och skatterensad bas (K13) klarade inte skärmen. Ärligt negativt: säsong + trend + el + K2 är svåra att slå med fri data.
4. **Skatterna (K13):** rensat för skatter vore skarp 2026-11 cirka +0,13 pe högre. Johannes beslut: **ingen justering** av
   novemberprognosen. December: CO2-skattesänkningen upphör, +0,40 pe enligt K13. Bedöms i nästa månadsrutin.
5. **Sverigebilden:** 29 prisledsserier, 241 länsserier, AF, AI-indikatorn, förklaringar per komponent, Sverigeläget v2 i
   Claude Data (uppladdad), samma sida på GitHub Pages (byggs i Actions) och ett skriptgenererat månadsbrev.

### Per spår
| Spår | Resultat | Varianter | Detaljer |
|---|---|---|---|
| K0 Prisleden | 29 serier; screening 0/29 över BH; K0-C2 obekräftad, inte fryst | 2 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k0/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k0/resultat.md) |
| K1 Drift | pipeline, skuggor, workflows, DuckDB-tester, champion/challenger | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k1/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k1/resultat.md) |
| K2 ML | ridge/ens på residualen klarade skärmen | 9 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k2/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k2/resultat.md) |
| K2b Granskning | håller med förbehåll; flashläcka rättad; onlinerepro grön | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k2b/granskning.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k2b/granskning.md) |
| K3 Förklaring | bidrag per komponent; tjänster 37 % av felet | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k3/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k3/resultat.md) |
| K4 Regionalt | 241 länsserier, kvalitet grön | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k4/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k4/resultat.md) |
| K5 Sverigeläget v2 | 9 nya dataset, månadsbrev, uppladdad | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k5/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k5/resultat.md) |
| K6 Om lätt | J4 D2 ingen revisionseffekt; nordisk el håller inte | 2 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k6/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k6/resultat.md) |
| K7 Tjänster | negativt (77 % av tjänstefelet är resor) | 5 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k7/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k7/resultat.md) |
| K8 Livsmedel | negativt i totalen; livsmedelsfel −10 % | 4 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k8/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k8/resultat.md) |
| K9 Horisont 3–12 | negativt; Riksbanken kvar som ribba | 4 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k9/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k9/resultat.md) |
| K10 Pages | shim + workflow, lokalt verifierad | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k10/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k10/resultat.md) |
| K11 Publiceringskalender | 4 läckor rättade; K2 rör sig ≤0,001 | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k11/granskning.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k11/granskning.md) |
| K12 Globalt test | bästa håller globalt (SPA/StepM) | 0 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k12/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k12/resultat.md) |
| K13 Skatterensad bas | negativt i backtest; skattekalender | 2 | [https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k13/resultat.md](https://github.com/birdiebook/kpif-nowcast/blob/main/docs/auto2/k13/resultat.md) |

### BLOCKED
Medlingsinstitutet (bara PDF), Swedavia (403), hotellnätter (SCB slutar 2021), varsel per län efter 2026-03 (AF slutade med fil),
länskarta GeoJSON (konto/GIS), vintages för TAB6613 (finns inte), grannländers egna spotpriser, J7:s råcache.

### Att göra själv (Johannes)
- **GitHub Pages:** Settings → Pages → Source: GitHub Actions, sedan Actions → "Pages (Sverigeläget)" → Run workflow.
- **Workflows är aktiva på main:** veckohämtning söndagar, skuggprognoser dag 1–4. Första körningen söndag 2026-11-29.
- **kpif-auto2-restart:** stäng av eller ta bort i appen (den hängde på behörighetsfrågor och behövs inte längre).
- Byte av huvudmodell är ditt beslut, efter live-utfall för skuggorna.

### Öppna frågor
`observations.upsert` daterar sena releaser för tidigt framöver (K2b), `jobads_*` och utlåning kanske ska vara revised (K11),
dashboarden klipps inte på known_from (K5), licenser för publik Pages-sida per källa (K10).

---

# Status: autonom körning 2 (Sverige på djupet)

**Lås:** orkestrerare 2026-11-23T10:26Z · heartbeat 2026-11-23T10:26Z
**Start:** 2026-11-23 · **Bas:** main @ 42b717b
**Varianter i körningen:** 28/30 (projektet totalt 23 + 28 = 51) · **main:** 5f91077 · **parallellt:** 6 (höjt från 3)
**Merge:** klara spår mergas till main av orkestreraren (ändrat 2026-11-23) · **Brief:** [BRIEF.md](BRIEF.md) · regler: `docs/autonom-korning-2.md` på main

## Spår

| Spår | Gren | Worktree | Steg | Varianter | Senaste SHA | Resultat / BLOCKED |
|---|---|---|---|---|---|---|
| K0 Prisleden | auto2/k0 | k0 | **KLAR, mergad** (25a6a6e) | 2/2 | d1a2a2f | 29 serier (PPI, KPIF-XE, varor/tjänster, KI prisplaner, FRED-råvaror, räntor/SWESTR). Screening: 0/29 överlever BH. K0-C2 på 50/50: 0,226 mot 0,232, Holm 0,097, obekräftad (revisionsläckage möjligt) → inte fryst. **Inget håller.** BLOCKED: Medlingsinstitutet (PDF/sessionsproxy), Swedavia (403), hotellnätter (slutar 2021). |
| K1 Drift | auto2/k1 | k1 | **KLAR, mergad** (a6fe532) | – | 3d376c1 | pipeline.py, shadow.py, 2 workflows (schedule/dispatch, nu aktiva på main), DuckDB + 12 datatester, champion/challenger i SCORECARD. Offline-repro identisk. Onlinerepro → K2b. |
| K2 ML | auto2/k2 | k2 | **KLAR, mergad** (806e943) | 9/10 | 4ef395e | Urvalsevidens (34 varianter totalt): k2_avg_ridge_l 0,199 (Holm 0,014), k2_avg_ens_s 0,201 (0,055), k2_avg_ridge_s 0,206 (0,083) mot 50/50 0,217 → **klarade urvalsskärmen**. Granskas oberoende i K2b innan skugga. |
| K2b Granskning + K2-skugga + onlinerepro | auto2/k2b | k2b | **KLAR, mergad** (75b6ac3) | 0 | 1190e04 | **Håller med förbehåll.** Verkligt läckage hittat och rättat: Eurostats flash publiceras efter dag 4 för alla december (+ 2018-03, 2026-01). Efter rättelse: k2_avg_ridge_l 0,200 (Holm 0,025), k2_avg_ens_s 0,202 (0,083) klarar skärmen; k2_avg_ridge_s 0,207 (0,19) klarar inte. Båda registrerade som skuggor (2026-11: 1,63 / 1,66). Onlinerepro från tom data GRÖN, skuggor identiska. |
| K3 Förklaring | auto2/k3 | k3 | **KLAR, mergad** (52191e2) | 0 | 4f7a154 | explain.py: bidrag per komponent, nyhetsdekomposition, felet per komponent, EWMA-band. 2026-11: 2,05 % (el +0,91, drivmedel −0,32). Fel 2015–26: tjänster 37 % av kvadratfelet, energi 21, varor 20, livsmedel 20. Inkopplat i pipeline monthly. |
| K4 Regionalt | auto2/k4 | k4 | **KLAR, mergad** (f74d2bb) | 0 | d60864c | 241 länsserier (AF andel/antal/varsel, SCB BAS/AKU/småhuspris/FPI/folkmängd, Tillväxtanalys konkurser), kvalitet grön (AF-länssumma = riket alla 370 mån). Skåne 8,2 % / Norrbotten 3,4 %, lägre än i fjol i alla län. BLOCKED: varsel per län efter 2026-03 (AF slutade med fil), GeoJSON (konto/GIS), FPI per kvartal. |
| K5 Sverigeläget v2 | auto2/k5 | k5 | **KLAR, mergad** (657d712), **uppladdad** | 0 | 9f39131 | 9 nya dataset (region, af, ai_indicator, prisled, forecast, champion, explain×3) + ny sida. Månadsbrev `docs/manadsbrev/2026-11.md` av skript. Sidans check i Claude Data ej körd ännu (ingen har sidan öppen). |
| K6 Om lätt | auto2/k6 | k6 | **KLAR, mergad**  | 2/4 | 0734d09 | Vintages TAB6613 BLOCKED (finns inte); ersatt med kontroll gammal/ny HIKP: el och drivmedel identiska (r 1,000) → J4 D2:s vinst är ingen revisionseffekt. Nordisk el: FI −0,011 (Holm 0,58), DK +0,002 (0,86), klarade inte skärmen; el-HIKP i FI/DK följer spot med en månads lagg, metoden är SCB-specifik. |
| K7 Tjänster | auto2/k7 | k7 | **KLAR, mergad** (11e0c8f) | 5/5 | 89a6db2 | Ingen klarade skärmen (bäst −0,001 mot 50/50). 77 % av tjänstefelet är resor (paketresor, flyg, logi); säsong+trend går knappt att slå med fri data. |
| K8 Livsmedel | auto2/k8 | k8 | **KLAR, mergad** (bf36a1c) | 4/4 | d366a3c | Ingen klarade skärmen (bäst 0,214 mot 0,217, Holm 0,41). Livsmedelsbidragets eget fel −10 % (2022–23 −35 %), men drunknar i totalen. Fynd: momssänkningen 2026-04 ligger kvar i trend/säsong → K13. |
| K13 Skatterensad bas | auto2/k13 | k13 | **KLAR, mergad** (5f91077) | 2/2 | d3cbf9e | Ingen klarade skärmen. Men: skarp 2026-11 blir +0,13 pe med rensad bas (2,05 → 2,18); förslag `--adjust 0.15` (inkl. månadskort i 5 län). **December: CO2-skattesänkningen upphör → +0,40 pe**, månadskort +0,15. Johannes beslutar. |
| K9 Horisont 3–12 | auto2/k9 | k9 | **KLAR, mergad** (7bbd5f3) | 4/4 | eecfbd4 | Ingen klarade skärmen. Riksbanken kvar som ribba på 3–12 mån; "2 %" lika bra på 12 mån. Effektivt n 46/23/11 för litet för korrektioner. |
| K10 Pages-dashboard (fas 6) | – | – | väntar (K5) | – | – | – |
| K12 Globalt test (SPA/MCS) | auto2/k12 | k12 | **KLAR, mergad** (05a9abc); omkörning pågår | 0 | 2a3dc6e | **Bästa håller globalt** över 31 varianter: k2_avg_ridge_l SPA p 0,035 mot rb_updated, 0,018 mot 50/50 (blocklängd 12: 0,12/0,076). Urvalsbias ~0,022 pe. Omkörs med K2b-rättelse och K8. |
| K11 Granskning publiceringsdatum | auto2/k11 | k11 | pågår | 0 | 51fa62f | – |

## Källlås
- SCB (regional), Arbetsförmedlingen: K4
- Riksbanken, KI, Eurostat: K6 (K2b får göra en liten onlinerepro mot SCB)

## Logg
- 2026-11-23T10:26Z: K2b, K12, K13, K5 mergade (137 passed på main). Huvudcheckoutens data uppdaterad från k5 (backup observations.20261123.bak.parquet). Sverigeläget v2 uppladdad (14 dokument). K12 omkörs.
- 2026-11-23T09:52Z: K8 klar (negativ), mergad; test_k8_food skippar nu utan K0-data (80bc02f, 108 passed). K13 skatterensad bas startad (2 av 4 reservvarianter).
- 2026-11-23T09:41Z: K9 och K7 klara (negativa), mergade (107 passed). K12 globalt test startat.
- 2026-11-23T09:25Z: Johannes: K0–K6 använde ~20 % av ett 5-timmarsfönster. Parallellitet höjd till 6 och backloggen utökad med K7 tjänster (37 % av felet), K8 livsmedel, K9 horisont 3–12, K10 Pages (efter K5) och K11 granskning av publiceringsfördröjningar. Variantbudget: K7 5, K8 4, K9 4 → max 26/30.
- 2026-11-23T09:22Z: K6 och K4 klara, mergade (96 passed på main f74d2bb). K5 startad. Kalibrering uppdaterad.
- 2026-11-23T09:05Z: K3 klar, mergad (87 passed på main). K6 startad. CLAUDE.md fick "Storleksbedömning" och docs/agentkalibrering.md (564c508).
- 2026-11-23T08:49Z: K2, K1, K0 klara; pytest grönt på sammanslaget main (74 passed); mergade och pushade. K3, K4, K2b startade från 25a6a6e.
- 2026-11-23 10:05: Johannes: agentic first. Orkestreraren mergar klara spår till main när pytest är grönt (CLAUDE.md "Agentiskt arbete", main 63a07c6). Syftesändringen ligger nu på main; grenen auto2/syfte är ersatt.
- 2026-11-23 09:50: Johannes: nytt syfte (inte lärprojekt; bästa möjliga lösning och bild av Sverige via KPIF). CLAUDE.md, vision.md, beslutslogg och K2-texten uppdaterade på grenen auto2/syfte (d77c022), merge beslutar Johannes. Spåragenterna informerade.
- 2026-11-23 09:35: K0, K1, K2 startade (agenter). Variantbudget: K2 10, K0 2, K6 ≤4, reserv 14.
- 2026-11-23: kpif-auto2-restart skapad (varje timme :19). Sparades utan auto-läge; Johannes har slagit på Auto i appen.
- 2026-11-23: ministeg: worktrees k0–k2 från origin/main, data kopierad, PYTHONPATH pekar på worktree, pytest 39 passed / 4 skipped.

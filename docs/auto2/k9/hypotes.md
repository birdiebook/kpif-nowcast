# K9 Längre horisont 3–12 månader: förregistrering

Skriven 2026-11-23 innan något fel för varianterna nedan har beräknats. Bas: main @ 51fa62f.
K9:s tak: **4 varianter totalt över alla horisonter**. Kända referenssiffror (fas 5, MAE 2015–2026):
Riksbanken 0,49 / 0,81 / 1,39 och "2 %" 1,37 / 1,37 / 1,39 på h = 3 / 6 / 12.

## Fråga och hypotes
Kan en korrektion av Riksbankens prognos med det som hänt sedan deras cutoff, eller en krympning av
Riksbankens prognos mot 2 %, ge lägre MAE än Riksbankens prognos på h = 3, 6 och 12?

**Hypotes:** den enda signalen med tydlig mekanism är Riksbankens egen miss på senast publicerade månad
(inflationen är persistent och Riksbankens prognos är 0–4 månader gammal vid vår prognosdag), plus
energi- och prisledsnyheter sedan cutoff. Signalen avtar med horisonten: något på h = 3, lite på h = 6,
inget på h = 12. På h = 12 är frågan i stället om Riksbankens prognos ska krympas mot 2 %; fas 5 visar
att båda är lika bra över perioden, vilket talar för en vikt mellan 0 och 1, men med effektivt ~10
oberoende observationer blir vikten osäker.

**Gissning innan (MAE 2015–2026, diff mot Riksbanken):**
- V1 `k9_ridge_h3`: −0,02 till −0,05, rå ensidig p 0,05–0,3. Klarar urvalsskärmen med ~30 % sannolikhet.
- V2 `k9_ridge_h12`: sämre än Riksbanken, +0,05 till +0,20 (interceptet lär sig 2022–23 års underskattning).
- V3 `k9_shrink_h12`: vikt w ≈ 0,3–0,7; diff −0,05 till +0,05, klarar inte skärmen.
- V4 `k9_miss_h6`: −0,01 till −0,04, φ ≈ 0,5–1; klarar inte skärmen.

## Uppställning (gemensam)
- **Ursprung o** = senast publicerade KPIF-månad; prognosdag = dag 4 i o+2 (`horizon.origin_date`).
  Mål = KPIF årstakt (pe) i o+h.
- **Riksbankens prognos** `RB` = `horizon.riksbank_for`: senaste prognosomgång publicerad före prognosdagen
  med cutoff c < o+h. Arkivet börjar 2015-02, så ursprung från 2014-12.
- **Utvärdering:** målmånader 2015-01..2026-10 där Riksbankens prognos och utfall finns. 2024–26 (använd)
  rapporteras separat, bara rapport. Före start (för få träningsrader) är varianten = Riksbankens prognos;
  delurvalet där varianten är aktiv rapporteras också.
- **Träningsrader vid ursprung o:** rader o' med o'+h ≤ o (utfallet publicerat före prognosdagen). Varje rads
  features är beräknade med `observations.as_of(origin_date(o'))`.
- **Features vid ursprung o** (alla as-of prognosdagen; "sedan c" = senaste värde minus värdet för period c):
  1. `rb_miss` = KPIF årstakt för o − Riksbankens prognos för o i samma omgång (0 om o ≤ c)
  2. `age` = o − c (månader)
  3. `rb_gap` = RB(o+h) − 2
  4. `gap0` = KPIF årstakt för o − 2
  5. `brent_since` = log-förändring i Brent (SEK) sedan c, %
  6. `kix_since` = log-förändring i KIX sedan c, %
  7. `rate_since` = styrräntan nu − vid c
  8. `gvb2_since` = 2-årig statsobligationsränta nu − vid c
  9. `ki_retail_since` = KI prisplaner detaljhandel (snitt senaste 3 mån) − värdet vid c
  10. `ki_services_since` = samma för KI prisplaner tjänster
  11. `ppi_since` = PPI hemmamarknad konsumtionsvaror, årstakt nu − vid c (revised=True)
  12. `ea_since` = euroområdets HIKP årstakt nu − vid c (revised=True)
- **Inga nya hämtningar.** Alla serier finns i observationstabellen (K0 och katalogen).

## Varianter (exakt lista, 4)
1. **`k9_ridge_h3`** (h = 3): mål = utfall − RB, ridge med intercept på de 12 featurena, prognos = RB +
   predikterad residual. Median-imputering och standardisering anpassas bara på träningsraderna. Alpha väljs
   med nästlad tidsserie-CV inom varje expanderande fönster: `TimeSeriesSplit(n_splits=4, gap=h,
   test_size=(n−h)//5)` (gap = h så att inre valideringsmål inte överlappar träningsmålen), kriterium MAE,
   grid 0,1–3000 som K2 (`k2_ml.RIDGE_GRID`), sedan refit på hela fönstret. Start: minst 36 träningsrader.
2. **`k9_ridge_h12`** (h = 12): identisk med 1 men h = 12.
3. **`k9_shrink_h12`** (h = 12): prognos = 2 + w·(RB − 2), w = Σ(y−2)(RB−2)/Σ(RB−2)² på träningsraderna
   (OLS utan intercept), klipps till [0, 1]. Start: minst 24 träningsrader.
4. **`k9_miss_h6`** (h = 6): prognos = RB + φ·`rb_miss`, φ = OLS utan intercept av (y − RB) på `rb_miss` över
   träningsraderna, inte klippt. Start: minst 24 träningsrader. *Motivering:* den enklaste formen av "det
   som hänt sedan cutoff" med tydlig mekanism (persistens i Riksbankens miss); en parameter är det som går
   att skatta med effektivt ~20 oberoende observationer på h = 6, och ger täckning av den tredje horisonten.

## Test och urvalsregel
- **DM-test** på absolutfel mot Riksbankens prognos, **ensidigt** (H1: varianten har lägre MAE; alla fyra
  nästlar Riksbanken: koefficienter 0 respektive w = 1, φ = 0 ger RB). Långsiktig varians med Newey-West
  (Bartlett) med **lagg h − 1** (överlappande fel), HLN-korrektion med h, Student-t med n−1 frihetsgrader.
- **Holm** över de 4 varianterna (mot Riksbanken).
- Mot "2 %" och naiv (årstakten oförändrad): samma DM, **tvåsidigt** (inte nästlade), rå p.
- **Effektivt n** rapporteras som n/h (antal icke-överlappande fönster), bredvid n.
- **Klarade urvalsskärmen:** Holm-p < 0,10 mot Riksbanken och MAE 2024–26 inte högre än Riksbankens.
  En ridge-variant som klarar skärmen märks "obekräftad (revisionsläckage möjligt)" eftersom PPI och HIKP
  har revised=True (inget utrymme under taket för en kontrollvariant utan dem).
- **Informationsmängdstest:** pytest per variant att prognosen för ett ursprung är identisk när
  observationstabellen, Riksbankens arkiv och KPIF trunkeras till det som var känt på prognosdagen.
- Körningen loggas med `evaluation.log_run`.

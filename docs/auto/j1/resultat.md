# J1 resultat (urvalsevidens)

Körning: `experiments/runs/20261122T221013Z_j1_hybrid.csv`. Full tabell: [results_raw.md](results_raw.md).
Globalt varianttotal vid körningen: **13/50**. Alla p-värden är urvalsevidens från samma urval.
DM-test ensidigt (H1: lägre MAE än rb_updated), Holm över 8 varianter.

## 2015-01..2026-10, n = 141 (förregistrerat kriterium)

| Variant | MAE | Diff mot rb_updated | p ensidigt (rå) | Holm p |
|---|---|---|---|---|
| C2 j1_comb_invmse | 0,216 | −0,039 | 0,020 | 0,139 |
| C1 j1_comb_equal | 0,217 | −0,039 | 0,015 | 0,117 |
| C3 j1_comb_ols | 0,217 | −0,038 | 0,023 | 0,139 |
| H4 j1_hyb_energy_ea | 0,222 | −0,033 | 0,080 | 0,261 |
| C4 j1_comb_ols_age | 0,222 | −0,033 | 0,034 | 0,172 |
| H2 j1_hyb_energy | 0,226 | −0,030 | 0,065 | 0,261 |
| H3 j1_hyb_energy_core | 0,228 | −0,027 | 0,089 | 0,261 |
| H1 j1_hyb_energy_fixed | 0,238 | −0,017 | 0,216 | 0,261 |
| j2 (J2 V2, referens) | 0,243 | −0,013 | 0,282 | – |
| rb_updated | 0,256 | – | – | – |

**Ingen variant klarade urvalsskärmen** (Holm p < 0,10). Bästa Holm p = 0,117 (C1). Resultatet är
negativt enligt förregistreringen, men nära gränsen.

## Delurval och använd period (bara rapport)
- 2017-02..2026-10 (n = 117, alla skattningar har ≥24 obs): C1 0,232 mot rb_updated 0,281, Holm p = 0,079.
  Det är ett sekundärt delurval och avgör inget.
- 2024–2026 (n = 34, använd): alla varianter lägre MAE än rb_updated (0,220–0,248 mot 0,267), inget signifikant.
  Ingen variant blir sämre.

## MAE efter prognosomgångens ålder, 2015–2026
| Ålder | rb_updated | j2 | C1 equal | H2 energy | n |
|---|---|---|---|---|---|
| 1 mån | 0,188 | 0,213 | 0,173 | 0,199 | 45 |
| 2 mån | 0,246 | 0,249 | 0,217 | 0,230 | 60 |
| 3+ mån | 0,355 | 0,270 | 0,270 | 0,252 | 36 |

## Tolkning
- Kombinationen vinner i alla åldrar, även vid 1 månad där rb_updated = Riksbanken. Det tyder på att
  de två prognoserna har olika fel (diversifiering), inte bara att j2 har nyare energidata.
- Skattade vikter (C2, C3) ger inget utöver 50/50 (C1). Klassiskt resultat: enkla snitt är svåra att slå.
- Energinyheten ensam (H1, fast β = 1) hjälper lite. Skattat β (H2) mer: β < 1 behövs, troligen för att
  rb_updated:s miss för t−1 redan bär en del av energichocken.
- Gissningen innan (0,215–0,225, p före Holm 0,02–0,10, Holm strax över 0,10) stämde.

## Frysning
Ingen variant klarade skärmen, så ingen frysning. **Förslag till Johannes:** C1 `j1_comb_equal`
(0,5·rb_updated + 0,5·j2, ingen parameter) är en naturlig kandidat att följa live bredvid J2:s V2,
om han vill. Den kräver ingen skattning, så risken för överanpassning är låg.

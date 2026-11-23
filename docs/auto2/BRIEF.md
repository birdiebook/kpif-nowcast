# Brief: autonom körning 2 (ordagrant, 2026-11-23)

Detaljerna för spåren och reglerna står i `docs/autonom-korning-2.md` och `docs/autonom-korning.md`
på `origin/main` (läs med `git -C C:\dev\kpif-nowcast show origin/main:docs/autonom-korning-2.md`).
Allt under linjen är uppdraget ordagrant som det gavs till orkestreraren.

---

Background (from the session that started this one):
Johannes (BI/data engineering) bygger ett lärprojekt: nowcast av svensk KPIF-inflation, med agenten som kodare och honom som styrande. Körning 1 (J1–J7) blev klar på 30 minuter. Den gav en elmodell (J2, MAE 0,243) och ett 50/50-snitt med rb_updated (0,217) som skuggprognoser från 2026-12. Ribban rb_updated ligger på 0,256. Inget slår ribban säkert. Johannes vill nu ha en mer ambitiös körning med fokus på Sverige: prisleden (K0), drift i GitHub Actions (K1), ML med nästlad validering (K2), förklarade prognoser (K3), regional data (K4), dashboard v2 och månadsbrev (K5), och K6 bara om det är lätt. Commits ska använda repots lokala git-identitet (GitHub noreply). Repot är publikt: inga personuppgifter, ingen data i git, inga hemligheter.

Task:
ultracode.

Kör autonom körning 2 i `C:\dev\kpif-nowcast` (GitHub `birdiebook/kpif-nowcast`) enligt `docs/autonom-korning-2.md`. Den briefen bygger på `docs/autonom-korning.md`, vars regler gäller utom där körning 2 säger annat. Läs båda först, plus `CLAUDE.md`, `docs/vision.md`, `docs/forbattringsplan.md` och de sista posterna i `docs/beslutslogg.md`.

Utgångsläge: main @ `42b717b`. J1–J7 är mergade (J2 `j2_el.py`, J1 `j1_hybrid.py`, J5 EWMA-band, J6 `catalog_af.py`, J7 AI-indikator). Grenen `auto/status` finns kvar från körning 1. Använd den, men skriv körning 2:s status i `docs/auto2/STATUS.md` och spara briefen ordagrant som `docs/auto2/BRIEF.md` där. Worktrees ska ligga under `C:\dev\kpif-auto2\<spår>`, med grenar `auto2/<spår>`. 23 av projektets modellvarianter är förbrukade, och körning 2 får använda 30 nya.

Förberedelser medan Johannes är vaken:
1. Ministeget enligt briefen: worktree, robocopy av data, PYTHONPATH-kontroll, pytest och push till `auto/status`. Ingen behörighetsprompt får dyka upp.
2. Föreslå den schemalagda uppgiften `kpif-auto2-restart` med auto-läge. Skapa den bara efter Johannes ja, och testa en riktig väckning. Körning 1:s uppgift sparades utan auto-läge och fastnade på varje start. Om det händer igen: be Johannes slå på auto-läge för uppgiften i appen, eller kör utan omstart.
3. Ge Johannes statuslänken `https://github.com/birdiebook/kpif-nowcast/blob/auto/status/docs/auto2/STATUS.md`.

Kör sedan backloggen (K0, K1 och K2 först, högst 3 samtidigt) tills den är tom. Skriv då slutrapport och STOP. Ingenting mergas till main, och `forecast.py`, `forecasts/` och den schemalagda uppgiften `kpif-final-forecast-2026-11` rörs inte. Hoppa över datakällor som blir omständliga (konto, betalning, skrapning mot villkoren) och markera dem BLOCKED.

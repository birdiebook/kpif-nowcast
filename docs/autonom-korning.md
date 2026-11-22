# Autonom körning av förbättringsplanen

Körinstruktion för en ny session. Kopiera allt under linjen och klistra in som första meddelande.
Den är granskad av tre oberoende granskare (drift och gränser, statistik, repo och samordning)
innan den skrevs. Se `docs/forbattringsplan.md` för jobben.

**Innan du lägger dig (gör själv):**
- Slå på keep-awake i appen och behåll nätströmmen.
- `powercfg /change standby-timeout-ac 0` och `powercfg /change hibernate-timeout-ac 0`
- Pausa Windows Update en vecka.
- Starta sessionen i auto-läge. Svara ja på allow-reglerna och på omstartsuppgiften när den frågar,
  och vänta tills den har gjort ett helt ministeg utan att fråga om lov.
- Starta inga andra sessioner i `C:\dev\kpif-nowcast` förrän körningen är klar.

Status under körningen: https://github.com/birdiebook/kpif-nowcast/blob/auto/status/docs/auto/STATUS.md

---

ultracode.

## Mål
Kör jobben J1–J7 i docs/forbattringsplan.md autonomt i C:\dev\kpif-nowcast (GitHub birdiebook/kpif-nowcast) från söndag 2026-11-22 kväll till senast måndag 2026-11-23 22:00. Leverans: pushade grenar auto/<jobb> med rapport, ingenting mergat. Johannes följer körningen från mobilen.

## Läs först
CLAUDE.md, docs/vision.md, docs/forbattringsplan.md (dess regler gäller utöver denna brief) och de sista posterna i docs/beslutslogg.md. Spara den här briefen ordagrant som docs/auto/BRIEF.md på grenen auto/status. Varje omstart läser den därifrån.

## Miljö och förberedelser
Gör detta medan Johannes är vaken.
1. Statusgren och worktrees ska ligga utanför appens .claude\worktrees:
```
git -C C:\dev\kpif-nowcast fetch origin
git -C C:\dev\kpif-nowcast worktree add -b auto/status C:\dev\kpif-auto\status origin/main
```
Jobb skapas med `git -C C:\dev\kpif-nowcast worktree add -b auto/jN-<namn> C:\dev\kpif-auto\jN <bas>`.
2. Data: data/ är gitignorerad, så en ny worktree saknar data. Säkerhetskopiera först data\observations.parquet till data\observations.20261122.bak.parquet. Kontrollera storleken på data/ och kopiera sedan en gång per worktree: `robocopy C:\dev\kpif-nowcast\data C:\dev\kpif-auto\jN\data /E`.
3. Kod: den redigerbara installationen pekar på huvudcheckoutens src. Kör detta före varje Python-körning i en worktree:
```
$env:PYTHONPATH = "C:\dev\kpif-auto\jN\src"
C:\dev\kpif-nowcast\.venv\Scripts\python.exe -c "import kpif_nowcast;print(kpif_nowcast.__file__)"
```
Avbryt om sökvägen inte ligger under worktreen. Kör testerna som `python -m pytest` med samma PYTHONPATH. Kör aldrig `pip install -e .`.
4. Behörigheter: be Johannes bekräfta auto-läge och allow-regler för git fetch, git push origin auto/*, git worktree add, venv-python, robocopy och skrivning under C:\dev\kpif-auto. Kör sedan ett helt ministeg medan han tittar: worktree, pytest, commit och push till auto/status. Bekräfta att ingen prompt dyker upp.
5. Omstart: /loop överlever inte ett stopp vid 5-timmarsgränsen. Föreslå en schemalagd uppgift, kpif-auto-restart, som körs varje timme från 00:30 till måndag 22:00 med prompten "Läs docs/auto/BRIEF.md och STATUS.md från origin/auto/status och fortsätt enligt avsnittet om 5-timmarsfönstret." Skapa den först efter Johannes ja. Testa en riktig väckning innan han lägger sig.
6. Det här gör Johannes själv: slår på keep-awake i appen, behåller nätströmmen, stänger av viloläge (`powercfg /change standby-timeout-ac 0` och `powercfg /change hibernate-timeout-ac 0`) och pausar Windows Update.

## Körordning
Högst 2 jobb samtidigt. Prioritet: J2, J1, J3, J6, J4, J5, J7.
- Börja med J2 och J6.
- J1 startar när J2 är KLAR, det vill säga när en variant klarat skärmen eller alla varianter är förbrukade (MISSLYCKAD räknas också som klar). Om J2 klarade skärmen: tagga `auto/j2-done` och förgrena J1 från taggen. Annars förgrenas J1 från origin/main och använder J2:s elserier enbart som data. Skriv bas-SHA i rapporten.
- J3 startar när J1 är klar. Basen är alltid rb_updated från origin/main.
- J4, J5 och J7 tar lediga platser när inget jobb med högre prioritet kan köras.
- Använd flera agenter bara för variantutvärdering, inte för läsning, datahämtning eller statusuppdateringar.

## Regler per jobb
- Förregistrera hypotes och exakt variantlista i docs/auto/<jobb>/hypotes.md och lägg en länkrad i docs/beslutslogg.md. Committa innan något körs. En variant som läggs till senare märks "tillagd efter resultat".
- En variant är varje distinkt prognosserie vars fel för 2015–2026 har beräknats. Val av fönster, startår och lagg räknas som egna varianter. Högst 10 per jobb. En variant räknas som förbrukad när förregistreringen är committad. Logga allt via evaluation.log_run och i docs/auto/VARIANTS.md på auto/status med löpande total. Globalt tak är 50 varianter, J3:s screening oräknad.
- Modellval görs på 2015–2026. Perioden 2024–2026 är redan använd. Varje DM-resultat är urvalsevidens från samma urval. Skriv aldrig att en modell slår rb_updated, skriv "klarade urvalsskärmen". Frys en sådan modell (SHA och parametrar) i rapporten som skuggprognos från 2026-12. Johannes utvärderar den live.
- Allt som skattas (säsongsfaktorer, vikter, skalning, kvantiler) skattas om inom det expanderande fönstret, med enbart data vars known_from ligger före deadline (dag 4 i t+1). Varje jobb ska ha ett pytest som visar att prognosen för t blir identisk med och utan data efter t:s deadline.
- Features från en Spec med revised=True flaggas. En modell som klarar skärmen tack vare sådana features märks "obekräftad (revisionsläckage möjligt)".
- Nya Spec eller laggar ska ange källan i publiceringskalendern. Avrunda mot senare publicering. SCB:s detaljindex för t får aldrig användas för t.
- J5: mät täckning bara på sekventiella intervall, efter minst 36 månaders inkörning, och redovisa ett binomialt konfidensintervall.
- Redovisa Holm-justerat p bredvid råa p. För nästlade jämförelser (J1, J3): ensidigt test med angiven riktning.
- Hämta inget som redan finns i parquet-filen eller i råcachen. Bara ett jobb åt gången får hämta från en viss källa (låsrad i STATUS). Högst 3 försök med exponentiell backoff, sedan BLOCKED för källan. Nya hämtningar sparas i data/raw/<jobb>/. JobTech cachas per svar och hämtas i batchar som går att återuppta.
- Filer skrivs bara med Edit/Write eller med Python och encoding='utf-8', aldrig med PowerShell Set-Content, Out-File eller omdirigering. Kör `git diff --stat` före varje commit och avbryt om en fil är ändrad på alla rader.
- Nya katalogserier läggs i en egen modul per jobb, inte i den befintliga listan i catalog.py.
- Ett jobb är klart när pytest är grönt och grenen är pushad. Under docs/auto/<jobb>/ ska det då finnas en resultatsammanfattning (MAE, DM-p, n). docs/auto/<jobb>.md ska innehålla kpif_nowcast.__file__ och SHA överst, PR-text, "beror på: <gren>@<sha>" och länken https://github.com/birdiebook/kpif-nowcast/compare/main...auto/<jobb>?expand=1.

## 5-timmarsfönstret och återupptagning
- Arbeta i små steg som avslutas helt. Committa och pusha efter varje steg.
- Vid varje start: kör `git -C C:\dev\kpif-nowcast fetch origin` och läs `git show origin/auto/status:docs/auto/STATUS.md`. Avsluta om där står STOP. Avsluta om låsraden är yngre än 20 minuter, för då kör en annan instans. Annars: skriv ett eget lås med tidsstämpel.
- Kör `git status` i varje worktree. Ocommittade ändringar commitas som "WIP (avbruten)" eller stashas, aldrig reset --hard. Fortsätt med nästa variantnummer.
- /loop utan intervall används bara som komplement.
- Högst 2 försök per steg, sedan BLOCKED. Om STATUS är oförändrad två väckningar i rad: skriv STALLED och stoppa.
- Om ett verktyg nekas: markera BLOCKED och byt jobb. Vänta aldrig.
- Hård deadline: måndag 2026-11-23 22:00.

## Status och rapportering
Bara orkestreraren skriver docs/auto/STATUS.md, och bara på auto/status (C:\dev\kpif-auto\status). Jobben skriver bara sina egna filer på sina egna grenar. Överst i STATUS: lås, starttid, senaste heartbeat och global varianttotal. Per jobb: gren, worktree, steg, varianter x/10, senaste SHA, resultat och eventuell BLOCKED-orsak. Om en push nekas: `git pull --rebase` och pusha igen. Ge Johannes länken github.com/birdiebook/kpif-nowcast/blob/auto/status/docs/auto/STATUS.md vid start.

## Förbjudet
- Committa, pusha eller merga till main. Köra checkout eller pull i C:\dev\kpif-nowcast. Där får bara fetch, worktree add och git show köras.
- Röra forecast.py, forecasts/, CLAUDE.md eller docs/vision.md.
- Force-push, radera grenar eller taggar, git clean, git worktree remove --force. Röra worktrees eller grenar som inte börjar med auto/.
- Skriva i huvudcheckoutens data/, outputs/ eller experiments/. Den ospårade filen experiments/runs/20261122T212103Z_backtest.csv ska lämnas orörd.
- Lägga data i git.
- Ändra schemalagda uppgifter, inställningar eller systeminställningar. Enda undantaget är att skapa kpif-auto-restart efter Johannes ja.

## När allt är klart
Skriv en slutrapport överst i STATUS: resultat per jobb märkt som urvalsevidens, global varianttotal bredvid varje p-värde, och länkar. Skriv sedan STOP i STATUS, så att omstartsuppgiften avslutar direkt, och stoppa loopen.

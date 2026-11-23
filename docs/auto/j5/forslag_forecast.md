# Förslag: lägesberoende felband i den skarpa prognosen (inte aktiverat)

`forecast.py` är inte ändrad. Så här skulle bytet se ut om Johannes väljer det.

I dag: `error_bands()` tar kvantil 50 och 80 % av |fel| för samma modell sedan `EVAL_START` och lägger
dem symmetriskt runt prognosen (`range_50`, `range_80`).

Förslag (U4, EWMA-normaliserad conformal):
```python
from kpif_nowcast.j5_intervals import interval_for

# err: utfall - prognos för alla tidigare månader (äldst först), samma modell som den skarpa
q = interval_for("j5_ewma", err.to_numpy(), None, None)   # dict kvantil -> felkvantil
range_50 = [final_yy + q[0.25], final_yy + q[0.75]]
range_80 = [final_yy + q[0.10], final_yy + q[0.90]]
range_90 = [final_yy + q[0.05], final_yy + q[0.95]]
```
- Felen ska vara sekventiella (varje månads prognos gjord med data fram till dess deadline). Backtestens
  `component_forecast` uppfyller det.
- Banden blir asymmetriska och följer felnivån. Efter en orolig period blir de bredare, efter en lugn smalare.
- Med dagens modell (comp_fuel_el, fel bara från 2024) finns för få fel; använd J2 V2 eller comp_fuel för historiken.

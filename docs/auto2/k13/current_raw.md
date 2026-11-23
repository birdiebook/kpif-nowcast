# K13: 2026-11 with and without tax cleaning (made 2026-11-23, live-style features, partial electricity month as in forecast.py)

|                                        |   raw_yy |   clean_yy |   diff_yy |   raw_mm |   clean_mm |   addback_mm |   d_capital_stock |   d_energy |   d_food |   d_goods |   d_services |
|:---------------------------------------|---------:|-----------:|----------:|---------:|-----------:|-------------:|------------------:|-----------:|---------:|----------:|-------------:|
| component_fuel_el_v1 (live main model) |    2.054 |      2.183 |     0.129 |    0.669 |      0.797 |            0 |                 0 |      0.063 |    0.064 |         0 |            0 |
| J2 V2                                  |    1.861 |      1.985 |     0.124 |    0.479 |      0.601 |            0 |                 0 |      0.058 |    0.064 |         0 |            0 |
| k2_avg_ens_s                           |    1.683 |      1.745 |     0.062 |  nan     |    nan     |          nan |               nan |    nan     |  nan     |       nan |          nan |
| rb_updated                             |    1.18  |      1.18  |     0     |  nan     |    nan     |          nan |               nan |    nan     |  nan     |       nan |          nan |

2026-12: known tax add-back +0.398 pp m/m (energy), about +0.40 pp y/y relative to a forecast without it; on top of the cleaned base.

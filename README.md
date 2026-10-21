# glacier-change

Glacier area change from Sentinel-2, checked against GLIMS inventory outlines. One config file per region
(`regions/<id>.json`). Generalized from the Mount Baker method behind whatcom.land
(`whatcom-land/methods/glacier-outlines.md`), which has the validation history and pitfalls.

    uv run python -m glacier_change glims hood                        # reference outlines → data/hood/
    uv run python -m glacier_change scenes hood 2025-08-01/2025-10-15 # list scenes
    uv run python -m glacier_change read hood 2025-09-23              # download windows → cache/hood/ (gitignored)
    uv run python -m glacier_change measure hood 2025-09-23           # per-glacier areas → data/hood/areas-*.csv
    uv run python -m glacier_change qc hood sheet.png 2016-09-25 2025-09-23   # check every scene by eye

Method: ice = red / SWIR (B04 / B11) > 2, patches ≥ 0.01 km², counted within 100 m of a reference outline.
Debris-covered and dirty ice read as rock, so this measures **visible** snow and clean ice, not glacier extent.

Data: GLIMS Glacier Database (NSIDC, doi:10.7265/N5V98602), outlines by Portland State University (CC0,
doi:10.15760/geology-data.03). Sentinel-2 L2A via Microsoft Planetary Computer (Copernicus data).

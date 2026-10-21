"""How much field-mapped ice reads as bright? Sentinel-2 bright mask (T=2) against the 2023 Mt. Hood glacier margins of
Bakken-French et al. (2024, The Cryosphere 18:4517), mapped from 0.3 m imagery of 8 Sep 2023 and walked in the field,
debris-covered and stagnant ice included. Zenodo doi:10.5281/zenodo.13356244 (CC BY 4.0), saved as
data/hood/external/ogi_2023_margins.geojson.

    PYTHONPATH=. uv run python methods/hood_ogi_2023_check.py   → data/hood/ogi-2023-check.csv
"""
import geopandas as gpd
import pandas as pd
from rasterio import features

from glacier_change import measure, region, s2

DATES = ["2016-09-25", "2022-09-19", "2023-09-14", "2025-09-23", "2026-10-03"]

r = region.load("hood")
ogi = gpd.read_file(r.data / "external" / "ogi_2023_margins.geojson").to_crs(r.crs)
rows = []
for d in DATES:
    b, tr = s2.load(r, d, 0)  # Hood has one window
    ice = measure.ice(b, 2.0)
    for name, g in [*ogi.groupby("Name"), ("All", ogi)]:
        m = features.rasterize([(x, 1) for x in g.geometry], out_shape=ice.shape, transform=tr).astype(bool)
        rows.append({"date": d, "glacier": name, "ogi_2023_km2": round(m.sum() * measure.PX_KM2, 3),
                     "bright_km2": round((ice & m).sum() * measure.PX_KM2, 3),
                     "bright_share": round((ice & m).sum() / m.sum(), 3)})
df = pd.DataFrame(rows)
df.to_csv(r.data / "ogi-2023-check.csv", index=False)
print(df.pivot(index="glacier", columns="date", values="bright_share").to_string())

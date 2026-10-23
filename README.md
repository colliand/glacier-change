# glacier-change

Glacier area change from Sentinel-2, checked against GLIMS inventory outlines. One config file per region
(`regions/<id>.json`). Generalized from the Mount Baker method behind
[whatcom.land](https://whatcom.land/glaciers). Regions so far:

- `baker`: Mount Baker, Washington ([methods/baker.md](methods/baker.md); note:
  [notes.colliand.com](https://notes.colliand.com/glaciers/mount-baker)). The validation case: within 1% of the
  Portland State 2015 outlines.
- `hood`: Mount Hood, Oregon ([methods/hood.md](methods/hood.md); note:
  [notes.colliand.com](https://notes.colliand.com/glaciers/mount-hood)). Debris-covered ice: bright ice is not glacier
  area here.

    uv run python -m glacier_change glims hood                        # reference outlines → data/hood/
    uv run python -m glacier_change scenes hood 2025-08-01/2025-10-15 # list scenes
    uv run python -m glacier_change read hood 2025-09-23              # download windows → cache/hood/ (gitignored)
    uv run python -m glacier_change measure hood 2025-09-23           # per-glacier areas → data/hood/areas-*.csv
    uv run python -m glacier_change qc hood sheet.png 2016-09-25 2025-09-23   # check every scene by eye
    uv run python -m glacier_change landsat hood 2013 2026            # Landsat 8/9, one value per year → data/hood/landsat-*.csv
    uv run python -m glacier_change landsat-qc hood methods/hood-landsat-series.jpg

Method: ice = red / SWIR (B04 / B11) > 2, patches ≥ 0.01 km², counted within 100 m of a reference outline.
Debris-covered and dirty ice read as rock, so this measures **visible** snow and clean ice, not glacier extent.

Data: GLIMS Glacier Database (NSIDC, doi:10.7265/N5V98602), outlines by Portland State University (CC0,
doi:10.15760/geology-data.03). Sentinel-2 L2A (Copernicus data) and Landsat 8/9 Collection 2 Level-2 (USGS) via Microsoft Planetary Computer.

## Licence

Open and permissively shared:

- **Code** (`glacier_change/`, `methods/*.py`): [MIT](LICENSE).
- **Data, figures and text** made here (`data/`, `methods/` notes and images, this README):
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reuse freely with credit.
- Third-party files keep their own licences: GLIMS / Portland State University outlines (CC0); the Oregon Glaciers
  Institute 2023 outlines under `data/hood/external/` (Bakken-French et al. 2024, Zenodo 13356244, CC BY 4.0, cite the
  original); Sentinel-2 data under the Copernicus terms ("contains modified Copernicus Sentinel data"); Landsat data
  from USGS (public domain).

Cite as: Colliander, J. (2026). *glacier-change: glacier area change from Sentinel-2, checked against inventory
outlines.* https://github.com/colliand/glacier-change

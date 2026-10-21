# Mount Hood: first results (2026-10-21)

Reference: Portland State University outlines via GLIMS: 1956 USGS maps (101 polygons) and Sept 2015 / Sept 2016
imagery (37 polygons, 7.03 km² within 8 km of the summit). Named glaciers: 15.6 km² (1956) → 5.8 km² (2015–16).

## Validation, Sentinel-2 25 Sep 2016 vs PSU
Ours 6.7 km² vs 7.0 (−5%), IoU 0.73 (Baker: 0.93). Disagreements, by eye (`hood-sentinel2-2016-2026.jpg`):
debris-covered tongues missed (Eliot, Coe, part of Sandy); seasonal snow on the south flank counted; the scene's
cloud classes flagged bright snow as cloud on a clear day (so SCL is now reported only, never used as a mask).

## Scenes (checked by eye)
Usable: 2016-09-25, 2022-09-19, 2023-09-14, 2025-09-13, 2025-09-23, 2026-10-03 (long October shadows).
Rejected: 2016-09-05 cloud; 2026-09-08 fresh snow over the whole mountain; 2024-08-29, 2025-08-21 leftover snow.

## Bright snow and clean ice (red/SWIR > 2)

Within 100 m of the PSU outlines, Sentinel-2 (10 m):

| | 2016-09-25 | 2022-09-19 | 2023-09-14 | 2025-09-13 | 2025-09-23 | 2026-10-03 |
|---|---|---|---|---|---|---|
| km² | 6.72 | 5.67 | 3.34 | 3.83 | 3.51 | 3.31 |

Share of the PSU outline area that is bright, Landsat 8/9 (30 m, C2 L2 scale and offset applied;
`hood_landsat_check.py`, images `hood-landsat-2015-2016-2023-2025.jpg`):

| 2015-09-27 | 2016-09-13 | 2023-09-09 | 2025-09-22 |
|---|---|---|---|
| 74% | 84% | 52% | 53% |

Sentinel-2: 82% (2016) → 48% (2025). Two sensors agree: a step down in 2023, flat since. Against the 2015 baseline
(a record-low snow year, so the cautious one) bright area inside the outlines fell 29% by 2025 (Landsat).

## Where the loss is (Sentinel-2 2016 → 2025, inside PSU outlines; Copernicus DEM 30 m)
Lost 2.42 of 5.79 km² bright. 92% on named glaciers. By elevation: below 2,300 m 82% lost; 2,300–2,600 m 44%;
2,600–2,900 m 23%; above 2,900 m about half (steep summit slopes). By distance inside the outline: 0–30 m 66%;
30–100 m 41%; 100–200 m 27%; over 200 m 20%. Lost pixels read ratio ~1.2 in 2025 (rock-like; dust alone does not do
this, as ice absorbs SWIR through thin dust).

## What this does and does not show
Shows: Hood's glaciers lost roughly 30–40% of their bright snow-and-ice surface between 2015–16 and 2023, mostly at
margins and low tongues, with no recovery through 2026.
Does not show: glacier area loss. Ice buried under thick debris reads the same as bare rock, and Hood's low tongues
carry heavy debris. NAIP (latest 2022-08, 30 cm) predates the 2023 drop, so it can't settle this.

## Next
- Glacier-area check: compare with a published field or lidar study of Eliot/Coe/Sandy (Jackson & Fountain 2007
  for the 2004 baseline; any post-2020 work), or DEM differencing (thinning) where repeat lidar exists.
- Per-glacier table and a year series (Landsat 2013–2026, one late-season scene a year).

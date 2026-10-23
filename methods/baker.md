# Mount Baker (2026-10-23)

The method in this repo was first built for Mount Baker, for [whatcom.land](https://whatcom.land/glaciers) (Glaciers
tab, 2026-10-10), then generalized here and tried on Mount Hood. This note moves Baker into the repo as a region
(`regions/baker.json`) and reruns it with the repo's code. Numbers agree with the whatcom.land build within 1% on every
shared date; small differences come from the 100 m zone and nearest-glacier assignment used here.

Reference: Portland State University outlines via GLIMS, within 10 km of the summit: 1974–75 USGS maps (70 polygons,
48.0 km²) and 2015 imagery (66 polygons, 40.2 km²). The two inventories divide the ice between glaciers differently
(Boulder 6.3 → 3.4 km² while Roosevelt, Park and Easton grow), so compare **totals** across them, and per-glacier numbers
only within one inventory or within our own method.

## Validation, Sentinel-2 4 Oct 2015 vs PSU 2015

The only clear 2015 scene (Sentinel-2A began that summer; 2015 was a record-low snow year, no fresh snow).

| | km² |
|---|---|
| PSU 2015 outlines | 40.16 |
| Ours, ratio > 2 | 39.70 (−1%) |
| Ours, 2.5 / 1.5 | 38.98 / 40.91 |

Overlap (IoU) 0.93, against 0.73 on Hood. Baker's glaciers carry much less rock, so bright ice is nearly all the ice.
Misses: debris-covered snouts (Deming, Easton, Coleman, Boulder). Extras: snow on rock ribs PSU excluded.

## Scenes (checked by eye, `baker-sentinel2-2015-2026.jpg`)

| Date | > 2 | 1.5 | 2.5 | vs 2015 (ours) | |
|---|---|---|---|---|---|
| 2015-10-04 | 39.70 | 40.91 | 38.98 | | reference |
| 2022-09-27 | 37.75 | 39.45 | 36.81 | −5% | big 2022 snowpack still lying at the edges |
| 2023-09-14 | 34.83 | 36.44 | 33.95 | −12% | |
| 2025-09-03 | 35.27 | 36.98 | 34.23 | −11% | |
| 2025-09-23 | 34.34 | 35.90 | 33.48 | −14% | best scene: end of melt, no fresh snow |
| 2026-09-16 | 33.86 | 35.19 | 33.07 | −15% | usable; see below |

Rejected: 2026-09-06 (cloud over the south and west flanks), 2026-10-03 (fresh snow), 2026-08-24 (no data over the
mountain in the window).

**Fresh-snow check.** Median red reflectance (×10⁴) of pixels that are ice on every date: 2015-10-04 4992, 2022-09-27
5128, 2023-09-14 4292, 2025-09-03 5124, 2025-09-23 4424, 2026-09-16 5342, 2026-10-03 5679. Earlier dates have higher sun,
so brightness alone is not proof; but 3 October 2026 is brighter than any September scene with lower sun, so it carries
fresh snow. 16 September 2026 is somewhat bright, perhaps a light dusting, yet only 0.7% of the pixels that were rock on
23 Sep 2025 read as ice. So 2026's area is if anything an overestimate, and it is no larger than 2025.

## Where the loss is (2015-10-04 → 2025-09-23, `baker_change.py`, `baker-change-2015-2025.jpg`)

Lost 5.72 km² of bright ice, gained 0.36 km² (mostly shade differences on north faces). Lost pixels lie a median 30 m
inside the 2015 edge; 90% within 94 m. The glaciers are pulling back all round their margins, most at the low snouts.
The lost pixels read ratio ~1.2 in 2025 (rock), so the threshold choice barely matters.

Per glacier, ours 2015 → 2025-09-23 (ratio > 2): Coleman −9%, Deming −10%, Roosevelt −10%, Boulder −9%, Easton −9%,
Park −12%, Mazama −14%, Rainbow −14%, Squak −12%, Talum −26%, Sholes −17%, Thunder −21%, Hadley −44%. The small
glaciers lose the largest share.

## Year series, Landsat 8/9 2013–2026 (`landsat` command)

86 late-season scenes; 24 usable (white < 2%, core > 50%, no-data < 1%, 25 Aug–30 Sep). Share of the PSU 2015
outline area that is bright, median of each year's usable scenes (`landsat-series.csv`; sheet `baker-landsat-series.jpg`):

| 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2022 | 2023 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 97% | 95% | 94% | 94% | 98% | 92% | 92% | 94% | 91% | 87% | 85% | 82% |

2021 and 2024: no usable scene (smoke and cloud; the 2024 candidates read 0.26–0.36 white). By eye: the 2015 median
scene (08-26) is hazy with smoke and the 2017 one (09-16) has cloud in the south-west corner; both pass the automatic
checks, so read those two years as uncertain. 2013 and 2014 show seasonal snow beyond the outlines, which this measure
ignores (it caps at 100% of the outline). Reading: > 90% every year to 2022, then a steady fall to 82% in 2026, the
lowest. Smaller than Hood's drop (≈ 75% → 50%), consistent with Baker's cleaner ice.

## Independent checks (from the whatcom.land build)

- USGS South Cascade Glacier (benchmark glacier, ~50 km east): measured area 1.822 km² (Oct 2015) and 1.800 (Aug 2021).
  This method: 1.69 (2015), 1.61 (Sep 2021), 1.35 (Sep 2025). Both show little change to 2021; our steep drop falls in
  2022–25, which include the most negative mass-balance years on record there (2023 −2.82, 2025 −3.55 m w.e.). USGS has
  no measured area after 2021 yet.
- whatcom.land's published 2025 Baker figure (35.8 km²) uses a more conservative outline rule: parts of the 2015
  outline the method cannot judge (debris-covered snouts, deep shade) are kept as in 2015.

## What this does and does not show

Shows: Mount Baker's bright snow and clean ice within 10 km of the summit shrank by about 14% from 2015 to 2025, from
the edges inward, with no recovery in 2026. Against the 1970s maps, the PSU inventory itself shows −16% from 1974–75 to
2015.
Does not show: thinning (a glacier can lose much of its volume while keeping its outline), or ice under rock. On Baker
the second matters less than on Hood: the method matched PSU's 2015 outlines within 1%.

## Rerun

    uv run python -m glacier_change glims baker
    uv run python -m glacier_change read baker 2015-10-04 2025-09-23 2026-09-16
    uv run python -m glacier_change measure baker 2015-10-04 2025-09-23 2026-09-16
    uv run python -m glacier_change qc baker methods/baker-sentinel2-2015-2026.jpg 2015-10-04 ...
    PYTHONPATH=. uv run python methods/baker_change.py 2015-10-04 2025-09-23 methods/baker-change-2015-2025.jpg
    uv run python -m glacier_change landsat baker 2013 2026
    uv run python -m glacier_change landsat-qc baker methods/baker-landsat-series.jpg

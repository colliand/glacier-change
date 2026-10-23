"""Mount Baker: where bright ice was lost between two Sentinel-2 scenes (ratio > 2), on the later scene in true colour.

    PYTHONPATH=. uv run python methods/baker_change.py 2015-10-04 2025-09-23 methods/baker-change-2015-2025.jpg

Lost (bright then, not now) in orange, gained in cyan, Portland State 2015 outlines in thin white. Also prints how far
the lost pixels lie inside the earlier ice edge.
"""
import sys

import numpy as np
from PIL import Image
from rasterio import features
from scipy import ndimage

from glacier_change import measure, region, s2

SCALE = 4000

r = region.load("baker")
d0, d1, out = sys.argv[1:4]
b0, tr = s2.load(r, d0, 0)
b1, _ = s2.load(r, d1, 0)
ref = features.rasterize([(g, 1) for g in measure.reference(r).geometry], out_shape=b0["B04"].shape,
                         transform=tr).astype(bool)
zone = features.rasterize([(g, 1) for g in measure.reference(r).buffer(measure.ZONE_M)], out_shape=ref.shape,
                          transform=tr).astype(bool)
i0, i1 = measure.ice(b0, 2.0) & zone, measure.ice(b1, 2.0) & zone
lost, gained = i0 & ~i1, i1 & ~i0
dist = ndimage.distance_transform_edt(i0) * 10  # metres inside the earlier ice edge
print(f"lost {lost.sum() / 1e4:.2f} km², gained {gained.sum() / 1e4:.2f} km²; lost pixels inside the {d0} edge: "
      f"median {np.median(dist[lost]):.0f} m, 90% within {np.percentile(dist[lost], 90):.0f} m")

rgb = np.clip(np.dstack([b1["B04"], b1["B03"], b1["B02"]]) / SCALE * 255, 0, 255).astype("float32")
rgb = rgb * 0.75
rgb[lost] = [240, 120, 30]
rgb[gained] = [40, 220, 230]
rgb[ref & ~ndimage.binary_erosion(ref)] = [255, 255, 255]
Image.fromarray(rgb.astype("uint8")).save(out, quality=88)

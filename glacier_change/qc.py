"""Contact sheet for checking scenes by eye: true colour, with the reference outlines in red and the ice mask (T=2)
edge in cyan. Look for fresh snow (bright rock ribs, white below the glaciers), smoke haze, and cloud.

    python -m glacier_change qc REGION OUT.png DATE [DATE ...]
"""
import numpy as np
from PIL import Image, ImageDraw
from rasterio import features
from scipy import ndimage

from . import measure, s2
from .region import Region

SCALE = 4000  # reflectance (x10000) shown as white
LABEL_H = 22


def tile(r: Region, date: str, n: int = 0) -> Image.Image:
    b, tr = s2.load(r, date, n)
    rgb = np.clip(np.dstack([b["B04"], b["B03"], b["B02"]]) / SCALE * 255, 0, 255).astype("uint8")
    ref = features.rasterize([(g, 1) for g in measure.reference(r).geometry], out_shape=rgb.shape[:2],
                             transform=tr).astype(bool)
    ice = measure.ice(b, 2.0)
    rgb[ref & ~ndimage.binary_erosion(ref)] = [230, 40, 40]
    rgb[ice & ~ndimage.binary_erosion(ice)] = [40, 220, 230]
    im = Image.new("RGB", (rgb.shape[1], rgb.shape[0] + LABEL_H), "white")
    im.paste(Image.fromarray(rgb), (0, LABEL_H))
    ImageDraw.Draw(im).text((6, 5), date, fill="black")
    return im


def sheet(r: Region, out: str, dates: list[str], cols: int = 3) -> None:
    tiles = [tile(r, d) for d in dates]
    w, h = tiles[0].size
    rows = -(-len(tiles) // cols)
    im = Image.new("RGB", (w * cols, h * rows), "white")
    for i, t in enumerate(tiles):
        im.paste(t, ((i % cols) * w, (i // cols) * h))
    im.save(out)

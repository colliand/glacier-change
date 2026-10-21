"""Landsat 8/9 Collection 2 Level-2 from Microsoft Planetary Computer: one number per late-season scene, then one per
year, for a long series at 30 m.

Per scene: the share of the reference ("now") outline area that is bright (red / SWIR1 > 2, patches of 11+ pixels,
about 0.01 km²), plus two visibility checks:
- "white": share of the 100 m zone bright in both red (> 0.3) and SWIR1 (> 0.2). Snow and ice are dark in SWIR1;
  cloud is not.
- "core": share of the glacier interiors (more than CORE_M inside the outlines) that is bright. Haze and thin cloud
  take it to ~0; fresh snow and a hot summer barely move it.
QA_PIXEL is not used: on Hood (2015) it flagged 6-19% of the zone as cloud on clear days and marked a solid overcast
as 75% bright-ice-compatible. It is reported as qa_cloud_zone only.
Per year: the median over the usable scenes from 25 August to 30 September (white < 2%, core > 50%, no-data < 1%).
Not the minimum: on Hood the least-bright scene was often wildfire smoke (2021-09-04, 2024-09-19 pass both checks).
Not October: low sun leaves the north-side glaciers in deep shadow and bright area reads low. Fresh snow pushes the
median up and haze pushes it down, so years with few scenes are noisier; min and max are kept. Check the scenes by
eye (`landsat-qc`, which shows the scene nearest each year's median).

Pitfalls: surface reflectance is DN * 0.0000275 - 0.2; Planetary Computer rate-limits (HTTP 429), so requests back off.
"""
import json
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import rasterio
from PIL import Image, ImageDraw
from rasterio import features
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
from scipy import ndimage

from . import measure, s2
from .region import Region

PC = s2.PC
ASSETS = ["red", "green", "blue", "swir16", "qa_pixel"]
SEASON = ("08-20", "10-15")  # searched; the series uses SERIES_SEASON
SERIES_SEASON = ("08-25", "09-30")
MIN_PIXELS = 11
MAX_BAD = 0.01
MAX_WHITE = 0.02
MIN_CORE = 0.5
CORE_M = 150
PX_KM2 = 9e-4  # one 30 m pixel


def _json(url, data=None):
    for i in range(8):
        try:
            return s2._json(url, data)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(30 * (i + 1))
    raise SystemExit("Planetary Computer still rate-limiting; try later")


def grid(r: Region):
    """A 30 m grid over all the region's windows."""
    w = np.array(s2.windows(r))
    x0, y0 = w[:, 0].min() // 30 * 30, w[:, 1].min() // 30 * 30
    x1, y1 = -(-w[:, 2].max() // 30) * 30, -(-w[:, 3].max() // 30) * 30
    return rasterio.Affine(30, 0, x0, 0, -30, y1), ((y1 - y0) // 30, (x1 - x0) // 30)


def search(r: Region, years: range) -> list[dict]:
    out = []
    for y in years:
        out += _json(f"{PC}/stac/v1/search", {
            "collections": ["landsat-c2-l2"], "bbox": list(r.bbox), "limit": 100,
            "datetime": f"{y}-{SEASON[0]}T00:00:00Z/{y}-{SEASON[1]}T23:59:59Z",
            "query": {"platform": {"in": ["landsat-8", "landsat-9"]}, "eo:cloud_cover": {"lt": 70}}})["features"]
    return sorted(out, key=lambda f: f["id"])


def read(r: Region, item: dict, token: str) -> dict:
    """Bands on the 30 m grid, cached as cache/<region>/landsat/<item id>.npz."""
    f = r.cache / "landsat" / f"{item['id']}.npz"
    if f.exists():
        return dict(np.load(f))
    tr, shape = grid(r)
    out = {}
    for k in ASSETS:
        for i in range(8):
            try:
                with rasterio.open(item["assets"][k]["href"] + "?" + token) as src, \
                        WarpedVRT(src, crs=r.crs, transform=tr, width=shape[1], height=shape[0],
                                  resampling=Resampling.nearest, nodata=0) as v:
                    out[k] = v.read(1)
                break
            except rasterio.errors.RasterioIOError:
                time.sleep(30 * (i + 1))
        else:
            raise SystemExit(f"could not read {item['id']} {k}")
    f.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(f, **out)
    return out


def bright(b: dict) -> np.ndarray:
    sr = {k: b[k].astype("float32") * 0.0000275 - 0.2 for k in ("red", "swir16")}
    m = (sr["red"] / np.maximum(sr["swir16"], 1e-3) > 2) & (b["red"] > 0)
    lab, n = ndimage.label(m)
    if n == 0:
        return m
    return np.isin(lab, 1 + np.flatnonzero(ndimage.sum(m, lab, range(1, n + 1)) >= MIN_PIXELS))


def scenes(r: Region, years: range) -> pd.DataFrame:
    """One row per scene → data/<region>/landsat-scenes.csv."""
    tr, shape = grid(r)
    g = measure.reference(r)
    ref = features.rasterize([(x, 1) for x in g.geometry], out_shape=shape, transform=tr).astype(bool)
    zone = features.rasterize([(x, 1) for x in g.buffer(measure.ZONE_M)], out_shape=shape, transform=tr).astype(bool)
    core = features.rasterize([(x, 1) for x in g.buffer(-CORE_M) if not x.is_empty], out_shape=shape,
                              transform=tr).astype(bool)
    token = _json(f"{PC}/sas/v1/token/landsat-c2-l2")["token"]
    rows, seen = [], set()
    for it in search(r, years):
        date = it["properties"]["datetime"][:10]
        if date in seen:
            continue  # the next WRS row of the same overpass
        b = read(r, it, token)
        if not (b["red"][zone] > 0).any():
            continue  # scene misses the mountain
        seen.add(date)
        qa = b["qa_pixel"]
        red, sw = (b[k].astype("float32") * 0.0000275 - 0.2 for k in ("red", "swir16"))
        m = bright(b)
        rows.append({"date": date, "id": it["id"],
                     "platform": it["properties"]["platform"],
                     "bright_ref_km2": round((m & ref).sum() * PX_KM2, 3),
                     "ref_km2": round(ref.sum() * PX_KM2, 3),
                     "bright_share": round((m & ref).sum() / ref.sum(), 3),
                     "white_zone": round(((red > 0.3) & (sw > 0.2))[zone].mean(), 3),
                     "core_bright": round(m[core].mean(), 3),
                     "qa_cloud_zone": round(((qa & 0b1010) > 0)[zone].mean(), 3),
                     "nodata_zone": round((b["red"][zone] == 0).mean(), 3)})
        print(rows[-1]["date"], rows[-1]["platform"], f"{rows[-1]['bright_share']:.0%}",
              f"white {rows[-1]['white_zone']:.1%} core {rows[-1]['core_bright']:.0%}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(r.data / "landsat-scenes.csv", index=False)
    return df


def series(r: Region) -> pd.DataFrame:
    """Median bright share of each year's usable late-summer scenes → data/<region>/landsat-series.csv."""
    df = pd.read_csv(r.data / "landsat-scenes.csv")
    md = df.date.str[5:]
    ok = df[(df.white_zone < MAX_WHITE) & (df.core_bright > MIN_CORE) & (df.nodata_zone < MAX_BAD)
            & (md >= SERIES_SEASON[0]) & (md <= SERIES_SEASON[1])].copy()
    ok["year"] = ok.date.str[:4].astype(int)
    out = ok.groupby("year").bright_share.agg(["median", "min", "max", "size"]).reset_index()
    out.columns = ["year", "bright_share", "min_share", "max_share", "scenes"]
    near = ok.assign(d=(ok.bright_share - ok.year.map(out.set_index("year").bright_share)).abs())
    near = near.loc[near.groupby("year").d.idxmin()].set_index("year")
    out["date"], out["id"], out["platform"] = (out.year.map(near[k]) for k in ("date", "id", "platform"))
    out["bright_share"] = out.bright_share.round(3)
    ok.drop(columns="year").to_csv(r.data / "landsat-usable.csv", index=False)
    out.to_csv(r.data / "landsat-series.csv", index=False)
    return out


def qc(r: Region, out: str, cols: int = 5) -> None:
    """True-colour sheet of the series scenes, reference outlines in red, bright edge in cyan."""
    tr, shape = grid(r)
    ref = features.rasterize([(x, 1) for x in measure.reference(r).geometry], out_shape=shape,
                             transform=tr).astype(bool)
    tiles = []
    for _, s in pd.read_csv(r.data / "landsat-series.csv").iterrows():
        b = dict(np.load(r.cache / "landsat" / f"{s['id']}.npz"))
        rgb = np.dstack([b[k].astype("float32") * 0.0000275 - 0.2 for k in ("red", "green", "blue")])
        rgb = np.nan_to_num(np.clip(rgb / 0.45 * 255, 0, 255)).astype("uint8")
        m = bright(b)
        rgb[ref & ~ndimage.binary_erosion(ref)] = [230, 40, 40]
        rgb[m & ~ndimage.binary_erosion(m)] = [40, 220, 230]
        im = Image.fromarray(rgb).resize((shape[1] * 2, shape[0] * 2), Image.NEAREST)
        t = Image.new("RGB", (im.width, im.height + 22), "white")
        t.paste(im, (0, 22))
        ImageDraw.Draw(t).text((6, 5), f"{s['date']}  {s['bright_share']:.0%} (median {s['year']})", fill="black")
        tiles.append(t)
    w, h = tiles[0].size
    sheet = Image.new("RGB", (w * cols, h * -(-len(tiles) // cols)), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * w, (i // cols) * h))
    sheet.save(out)

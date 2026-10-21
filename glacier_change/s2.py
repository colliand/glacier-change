"""Sentinel-2 Level-2A from Microsoft Planetary Computer: list scenes, and read one date onto 10 m windows around the
reference glaciers.

Pitfalls (met on Mount Baker, 2026-10-10):
- Scenes processed with baseline >= 04.00 (from January 2022) carry a +1000 offset in reflectance. Remove it, or the
  red/SWIR ratio is squeezed toward 1 and ice looks ~9% smaller.
- The STAC item's tile-wide eo:cloud_cover says nothing about the mountain. Look at every scene.
"""
import json
import urllib.request

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

from . import glims
from .region import Region

PC = "https://planetarycomputer.microsoft.com/api"
BANDS = ["B02", "B03", "B04", "B08", "B11", "SCL"]
WINDOW_BUFFER_M = 500


def _json(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def search(r: Region, datetime: str, max_cloud: float = 60) -> list[dict]:
    """Items over the region in a date range ("2025-08-01/2025-10-15"), oldest first, one per tile and day."""
    items = _json(f"{PC}/stac/v1/search", {"collections": ["sentinel-2-l2a"], "bbox": list(r.bbox), "datetime": datetime,
                                           "limit": 500, "query": {"eo:cloud_cover": {"lt": max_cloud}}})["features"]
    newest = {}
    for it in sorted(items, key=lambda i: i["id"]):  # reprocessed duplicates differ only in processing time
        p = it["properties"]
        newest[(p["datetime"][:10], p["s2:mgrs_tile"])] = it
    return [newest[k] for k in sorted(newest)]


def windows(r: Region) -> list[list[int]]:
    """One window per cluster of reference outlines ("now" era, buffered and merged), snapped to the 10 m grid."""
    g = glims.read(r)
    g = g[g.era == "now"].to_crs(r.crs)
    blobs = gpd.GeoSeries(g.buffer(WINDOW_BUFFER_M).union_all(), crs=r.crs).explode(index_parts=False)
    out = []
    for b in blobs:
        x0, y0, x1, y1 = b.bounds
        out.append([int(x0 // 10 * 10), int(y0 // 10 * 10), int(-(-x1 // 10) * 10), int(-(-y1 // 10) * 10)])
    return sorted(out)


def read(r: Region, date: str) -> None:
    """Save cache/<region>/<date>/wNN.npz (bands as uint16, offset removed) for every window. Skips windows done."""
    ddir = r.cache / date
    ddir.mkdir(parents=True, exist_ok=True)
    wins = windows(r)
    (r.cache / "windows.json").write_text(json.dumps(wins))
    items = [it for it in search(r, f"{date}T00:00:00Z/{date}T23:59:59Z", max_cloud=101)]
    if not items:
        raise SystemExit(f"no Sentinel-2 items over {r.id} on {date}")
    token = _json(f"{PC}/sas/v1/token/sentinel-2-l2a")["token"]
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2"):
        srcs = []
        for it in items:
            off = 1000 if float(it["properties"].get("s2:processing_baseline", "0")) >= 4.0 else 0
            srcs.append((off, {b: rasterio.open(it["assets"][b]["href"] + "?" + token) for b in BANDS}))
        for n, (x0, y0, x1, y1) in enumerate(wins):
            f = ddir / f"w{n:02d}.npz"
            if f.exists():
                continue
            tr = rasterio.Affine(10, 0, x0, 0, -10, y1)
            shape = ((y1 - y0) // 10, (x1 - x0) // 10)
            arr = {b: np.zeros(shape, "uint16") for b in BANDS}
            for off, rs in srcs:
                for b in BANDS:
                    tmp = np.zeros(shape, "uint16")
                    reproject(rasterio.band(rs[b], 1), tmp, dst_transform=tr, dst_crs=r.crs, src_nodata=0, dst_nodata=0,
                              resampling=Resampling.nearest if b == "SCL" else Resampling.bilinear)
                    if off and b != "SCL":
                        tmp = np.where(tmp > 0, np.clip(tmp.astype("int32") - off, 1, None), 0).astype("uint16")
                    fill = (arr[b] == 0) & (tmp > 0)
                    arr[b][fill] = tmp[fill]
            np.savez_compressed(f, transform=np.array(tr)[:6], **arr)
            print(f"  {date} w{n:02d} {shape}", flush=True)


def load(r: Region, date: str, n: int) -> tuple[dict, rasterio.Affine]:
    z = np.load(r.cache / date / f"w{n:02d}.npz")
    return {b: z[b] for b in BANDS}, rasterio.Affine(*z["transform"])

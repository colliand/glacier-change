"""Ice per glacier on one date, and a check against the reference outlines.

Ice = red / shortwave infrared (B04 / B11) > T, the standard band-ratio method of glacier inventories, with patches
under 0.01 km² (100 pixels) dropped. Only pixels within ZONE_M of a reference ("now") outline count, each assigned to its
nearest glacier, so seasonal snow far from any glacier is ignored. No-data pixels are "unseen".
The scene classification's cloud classes (SCL 8-10) are only reported ("cloud"), never used to hide pixels: on Mount
Hood (25 Sep 2016, a clear day) they flagged bright snow on the south side as cloud. Check every scene by eye.
Known blind spot: debris-covered ice reads as rock (Eliot and Coe tongues on Hood; Deming, Easton on Baker).
"""
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio import features
from scipy import ndimage
from shapely.geometry import box

from . import glims, s2
from .region import Region

THRESHOLDS = (1.5, 2.0, 2.5)
MIN_PIXELS = 100
ZONE_M = 100
PX_KM2 = 1e-4  # one 10 m pixel


def ice(b: dict, t: float) -> np.ndarray:
    b4, b11 = b["B04"].astype("float32"), b["B11"].astype("float32")
    m = (b4 / np.maximum(b11, 1) > t) & (b11 > 0)
    lab, n = ndimage.label(m)
    if n == 0:
        return m
    size = ndimage.sum(m, lab, range(1, n + 1))
    return np.isin(lab, 1 + np.flatnonzero(size >= MIN_PIXELS))


def reference(r: Region) -> gpd.GeoDataFrame:
    g = glims.read(r)
    g = g[g.era == "now"].to_crs(r.crs).reset_index(drop=True)
    g["gid"] = np.arange(1, len(g) + 1)
    return g


def areas(r: Region, date: str) -> pd.DataFrame:
    """Per reference glacier: ice km² at each threshold, plus unseen, flagged-cloud and zone km². The overlap of the
    ice mask with the reference outlines (IoU at T=2) goes in the frame's attrs."""
    g = reference(r)
    wins = json.loads((r.cache / "windows.json").read_text())
    zone_geom = g.buffer(ZONE_M)
    acc = {k: np.zeros(len(g) + 1) for k in [f"t{t}" for t in THRESHOLDS] + ["unseen", "cloud", "zone"]}
    inter = union = 0
    for n in range(len(wins)):
        b, tr = s2.load(r, date, n)
        shape = b["B04"].shape
        here = g.intersects(box(*wins[n]))
        if not here.any():
            continue
        idx = features.rasterize(list(zip(g.geometry[here], g.gid[here])), out_shape=shape, transform=tr, dtype="int32")
        zone = features.rasterize([(z, 1) for z in zone_geom[here]], out_shape=shape, transform=tr).astype(bool)
        _, (ii, jj) = ndimage.distance_transform_edt(idx == 0, return_indices=True)
        near = idx[ii, jj]
        unseen = b["B04"] == 0
        cloud = np.isin(b["SCL"], [8, 9, 10]) & ~unseen
        acc["zone"] += np.bincount(near[zone], minlength=len(g) + 1)
        acc["unseen"] += np.bincount(near[zone & unseen], minlength=len(g) + 1)
        acc["cloud"] += np.bincount(near[zone & cloud], minlength=len(g) + 1)
        for t in THRESHOLDS:
            m = ice(b, t) & zone & ~unseen
            acc[f"t{t}"] += np.bincount(near[m], minlength=len(g) + 1)
            if t == 2.0:
                ref = idx > 0
                inter += (m & ref).sum()
                union += ((m | ref) & ~unseen & zone).sum()
    out = g[["gid", "glac_id", "name", "date", "km2"]].rename(columns={"km2": "ref_km2", "date": "ref_date"})
    for k, v in acc.items():
        out[f"{k}_km2"] = (v[1:] * PX_KM2).round(4)
    out.attrs["iou"] = inter / union if union else float("nan")
    return out


def write(r: Region, date: str, df: pd.DataFrame) -> None:
    r.data.mkdir(parents=True, exist_ok=True)
    df.to_csv(r.data / f"areas-{date}.csv", index=False)

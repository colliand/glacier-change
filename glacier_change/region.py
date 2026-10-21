"""A region is one JSON file in regions/: bounding box, working CRS, summit and radius, and which GLIMS submitter's
outlines to use as the reference."""
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Region:
    id: str
    name: str
    bbox: tuple[float, float, float, float]  # lon/lat: west, south, east, north
    crs: str  # a metric UTM CRS; Sentinel-2 is read onto a 10 m grid in it
    summit: tuple[float, float]  # lon, lat
    radius_m: float  # glaciers counted within this distance of the summit
    glims_source: str  # GLIMS chief_affl of the reference inventory
    era_split_year: int  # outlines dated up to this year are "then", later ones "now"

    @property
    def data(self) -> Path:
        return ROOT / "data" / self.id

    @property
    def cache(self) -> Path:
        return ROOT / "cache" / self.id


def load(region_id: str) -> Region:
    cfg = json.loads((ROOT / "regions" / f"{region_id}.json").read_text())
    cfg["bbox"], cfg["summit"] = tuple(cfg["bbox"]), tuple(cfg["summit"])
    return Region(**cfg)

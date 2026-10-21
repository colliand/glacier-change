"""Reference outlines from the GLIMS Glacier Database (NSIDC), filtered to one submitter's inventory.

Use WFS 1.0.0: in 1.1.0 the bounding box is read lat,lon and returns nothing.
"""
import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

from .region import Region

GLIMS = "https://www.glims.org/geoserver/GLIMS/ows"
PLACEHOLDER_NAMES = {"", "None", "OR", "WA", "AK", "MT", "CA", "WY"}  # GLIMS uses the state code when unnamed


def fetch(r: Region) -> gpd.GeoDataFrame:
    w, s, e, n = r.bbox
    resp = requests.get(GLIMS, params={
        "service": "WFS", "version": "1.0.0", "request": "GetFeature", "typeName": "GLIMS:GLIMS_Glacier_Outlines",
        "bbox": f"{w},{s},{e},{n}", "outputFormat": "application/json", "maxFeatures": 10000,
        "propertyName": "entity_geom,glac_id,anlys_id,glac_name,src_date,line_type,rec_status,chief_affl"}, timeout=300)
    resp.raise_for_status()
    g = gpd.GeoDataFrame.from_features(resp.json()["features"], crs=4326)
    g = g[(g.line_type == "glac_bound") & (g.rec_status == "okay") & (g.chief_affl == r.glims_source)].copy()
    g["date"] = g.src_date.str[:10]
    g["year"] = pd.to_numeric(g.date.str[:4])
    g["era"] = g.year.map(lambda y: "then" if y <= r.era_split_year else "now")
    g["name"] = g.glac_name.where(~g.glac_name.fillna("").isin(PLACEHOLDER_NAMES))
    g["geometry"] = g.geometry.make_valid()
    summit = gpd.GeoSeries([Point(*r.summit)], crs=4326).to_crs(r.crs)[0]
    m = g.to_crs(r.crs)
    g = g[m.distance(summit) < r.radius_m].copy()
    g["km2"] = g.to_crs(r.crs).area.round(-2) / 1e6
    return g[["glac_id", "anlys_id", "name", "date", "year", "era", "km2", "geometry"]].reset_index(drop=True)


def save(r: Region, g: gpd.GeoDataFrame) -> None:
    r.data.mkdir(parents=True, exist_ok=True)
    g.to_file(r.data / "glims_outlines.geojson", driver="GeoJSON")


def read(r: Region) -> gpd.GeoDataFrame:
    return gpd.read_file(r.data / "glims_outlines.geojson")

"""python -m glacier_change <command> <region> [args]

    glims    REGION                   fetch reference outlines → data/REGION/glims_outlines.geojson
    scenes   REGION 2025-08-01/2025-10-15   list Sentinel-2 scenes (date, tile, cloud %, snow/ice %)
    read     REGION DATE [DATE ...]   download the windows for each date → cache/REGION/DATE/
    measure  REGION DATE [DATE ...]   per-glacier ice areas → data/REGION/areas-DATE.csv, prints totals and IoU
    qc       REGION OUT.png DATE ...  contact sheet for checking scenes by eye
"""
import sys

from . import glims, measure, qc, s2
from .region import load


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    cmd, r, args = argv[0], load(argv[1]), argv[2:]
    if cmd == "glims":
        g = glims.fetch(r)
        glims.save(r, g)
        print(g.groupby(["era", "year"]).km2.agg(["size", "sum"]).round(2).to_string())
    elif cmd == "scenes":
        for it in s2.search(r, args[0]):
            p = it["properties"]
            print(p["datetime"][:10], p["s2:mgrs_tile"], p["platform"], f'{p["eo:cloud_cover"]:5.1f}',
                  f'{p.get("s2:snow_ice_percentage", -1):5.1f}', p.get("s2:processing_baseline"))
    elif cmd == "read":
        for d in args:
            s2.read(r, d)
    elif cmd == "measure":
        for d in args:
            df = measure.areas(r, d)
            measure.write(r, d, df)
            tot = " ".join(f"T{t}={df[f't{t}_km2'].sum():.2f}" for t in measure.THRESHOLDS)
            print(f"{d}: reference {df.ref_km2.sum():.2f} km²  ours {tot}  unseen {df.unseen_km2.sum():.2f} of "
                  f"zone {df.zone_km2.sum():.2f}  flagged cloud {df.cloud_km2.sum():.2f}  IoU(T2) {df.attrs['iou']:.3f}")
    elif cmd == "qc":
        qc.sheet(r, args[0], args[1:])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])

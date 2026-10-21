import sys, json, time, urllib.request, urllib.error, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio import features
from scipy import ndimage
from PIL import Image
from glacier_change import region, measure
S=sys.argv[1]
r=region.load("hood"); PC="https://planetarycomputer.microsoft.com/api"
def J(u,d=None):
    for i in range(8):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,data=json.dumps(d).encode() if d else None,headers={"Content-Type":"application/json"}),timeout=120))
        except urllib.error.HTTPError as e:
            if e.code!=429: raise
            time.sleep(30*(i+1))
    raise SystemExit("still rate-limited")
tok=J(f"{PC}/sas/v1/token/landsat-c2-l2")["token"]
w=json.load(open(r.cache/"windows.json"))[0]; x0,y0,x1,y1=w
tr=rasterio.Affine(30,0,x0,0,-30,y1); shape=((y1-y0)//30,(x1-x0)//30)
g=measure.reference(r)
ref=features.rasterize([(x,1) for x in g.geometry],out_shape=shape,transform=tr).astype(bool)
zone=features.rasterize([(x,1) for x in g.buffer(100)],out_shape=shape,transform=tr).astype(bool)
tiles=[]
for d in ["2015-09-27","2016-09-13","2023-09-09","2025-09-22"]:
    fs=J(f"{PC}/stac/v1/search",{"collections":["landsat-c2-l2"],"bbox":list(r.bbox),"datetime":f"{d}T00:00:00Z/{d}T23:59:59Z","limit":10})["features"]
    band={}
    for k in ("red","green","blue","swir16"):
        arr=np.zeros(shape,"float32")
        for f in fs:
            with rasterio.open(f["assets"][k]["href"]+"?"+tok) as src:
                tmp=np.zeros(shape,"float32")
                reproject(rasterio.band(src,1),tmp,dst_transform=tr,dst_crs=r.crs,src_nodata=0,dst_nodata=0,resampling=Resampling.nearest)
                arr=np.where(arr==0,tmp,arr)
        band[k]=arr
    sr={k:np.where(band[k]>0,band[k]*0.0000275-0.2,np.nan) for k in band}
    m=sr["red"]/np.maximum(sr["swir16"],1e-3)>2
    lab,n=ndimage.label(m); sz=ndimage.sum(m,lab,range(1,n+1)); m=np.isin(lab,1+np.flatnonzero(sz>=11))
    print(f"{d} Landsat: bright in zone {(m&zone).sum()*9e-4:5.2f} km2; inside PSU outlines {(m&ref).sum()*9e-4:5.2f} of {ref.sum()*9e-4:5.2f} ({100*(m&ref).sum()/ref.sum():3.0f}%)",flush=True)
    rgb=np.nan_to_num(np.clip(np.dstack([sr["red"],sr["green"],sr["blue"]])/0.45*255,0,255)).astype("uint8")
    tiles.append(Image.fromarray(rgb).resize((shape[1]*2,shape[0]*2)))
W,H=tiles[0].size; im=Image.new("RGB",(W*4,H),"white")
for i,t in enumerate(tiles): im.paste(t,(i*W,0))
im.save(f"{S}/hood-landsat.png")

"""Download only publicly licensed study materials. No credentials required."""
import hashlib, json, pathlib, urllib.request, urllib.parse, zipfile, shutil
ROOT=pathlib.Path("production-assets")
ROOT.mkdir(exist_ok=True)
UA={"User-Agent":"OryzoStudy/1.0 (independent educational project)"}
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=90) as r:
        return r.read()
def get_json(url): return json.loads(fetch(url))
def download(url,p,md5=None):
    print("Downloading",url,flush=True)
    data=fetch(url)
    if md5 and hashlib.md5(data).hexdigest()!=md5: raise ValueError("Checksum mismatch: "+str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(data)
    return len(data)
def poly(slug,res,maps):
    info=get_json("https://api.polyhaven.com/files/"+slug)
    for key,ext in maps:
        entry=info[key][res][ext]
        url=entry["url"]
        p=ROOT/slug/pathlib.Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name
        download(url,p,entry.get("md5"))
def cork():
    for slug in ("Cork001","Cork003"):
        try:
            data=get_json("https://ambientcg.com/api/v2/full_json?id="+slug+"&include=downloadData")
            def links(obj):
                if isinstance(obj,dict):
                    for k,v in obj.items():
                        if k in ("downloadLink","rawLink") and isinstance(v,str): yield v
                        else: yield from links(v)
                elif isinstance(obj,list):
                    for v in obj: yield from links(v)
            urls=list(dict.fromkeys(links(data)))
            candidates=[u for u in urls if "4K-JPG" in urllib.parse.unquote(u).upper()]
            if not candidates: raise ValueError("No 4K JPG package returned")
            z=ROOT/(slug+".zip");download(candidates[0],z)
            with zipfile.ZipFile(z) as archive:
                for name in archive.namelist():
                    if pathlib.Path(name).suffix.lower() in (".jpg",".jpeg",".png",".txt"):
                        target=ROOT/slug/pathlib.Path(name).name;target.parent.mkdir(exist_ok=True)
                        with archive.open(name) as src,target.open("wb") as out: shutil.copyfileobj(src,out)
            z.unlink()
            return
        except Exception as e: print(slug,e,flush=True)
    raise RuntimeError("No verified ambientCG cork package could be retrieved")
tasks=[("wood",lambda:poly("wood_table_001","4k",[("diff","jpg"),("nor_gl","jpg"),("rough","jpg"),("disp","jpg")])),("HDRI",lambda:poly("studio_small_03","2k",[("hdri","hdr")])),("cork",cork)]
results={}
for name,fn in tasks:
    try: fn();results[name]="OK"
    except Exception as e: results[name]="FAILED: "+str(e);print(results[name],flush=True)
(ROOT/"manifest.json").write_text(json.dumps(results,indent=2))
(ROOT/"SOURCES.txt").write_text("Powered by Poly Haven (https://polyhaven.com), CC0. Cork: ambientCG (https://ambientcg.com), CC0. See manifest.json for actual download results.\n")
print(results)
if any(v!="OK" for v in results.values()): raise SystemExit(1)

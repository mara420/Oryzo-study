"""Prepare independently moving photographic layers from the five approved images.
Hand-authored silhouettes in normalized source coordinates. Reconstructed
background is only meant for small disocclusions, not unrestricted orbit.
No external model or image service is used.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import json

SOURCE = Path("photo/assets")
OUT = Path("assets/immersive-v14")
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1280, 720

# Polygon vertices follow the approved composition (x/y normalized).
# Foreground groups intentionally preserve contact between hand/product and mug/coaster.
# Avoid all embedded typography, including bottom chapter indicators.
SCENES = {
 "workshop": ("01-workshop.png", [
  ("cup", [(0,0),(.218,0),(.213,.095),(.201,.154),(.177,.200),(.144,.226),(.102,.228),(.066,.209),(.042,.175),(.029,.13),(.018,.066)], 1.6, 1.5),
  ("pencil", [(.615,0),(.66,0),(.71,.108),(.756,.22),(.775,.29),(.795,.367),(.784,.37),(.747,.302),(.701,.222),(.664,.14)], 1.8, 2.0),
  ("ruler", [(.757,.708),(.963,.601),(1,.577),(1,.652),(.774,.791)], 1.6, 1.5),
  ("clip", [(.804,.378),(.829,.37),(.852,.382),(.853,.42),(.843,.454),(.853,.467),(.846,.51),(.819,.521),(.795,.497),(.798,.452),(.813,.445),(.813,.419)], 1.7, 1.4),
 ]),
 "touch": ("03-touch.png", [
  ("hand-and-coaster", [(.346,.44),(.35,.348),(.37,.29),(.412,.224),(.459,.189),(.512,.18),(.565,.20),(.606,.235),(.617,.237),(.641,.24),(.673,.272),(.714,.326),(.76,.368),(.802,.425),(.846,.504),(.9,.604),(.931,.647),(1,.682),(1,1),(.802,1),(.739,.932),(.693,.9),(.647,.856),(.603,.827),(.54,.803),(.49,.768),(.45,.735),(.419,.704),(.39,.682),(.359,.645),(.348,.604),(.34,.574),(.341,.542),(.35,.516)], 2.8, 2.5),
 ]),
 "ritual": ("05-ritual.png", [
  ("mug-and-coaster", [(.559,.272),(.574,.228),(.61,.198),(.658,.186),(.709,.183),(.753,.198),(.791,.226),(.811,.277),(.833,.27),(.858,.271),(.881,.296),(.892,.335),(.887,.38),(.867,.421),(.838,.451),(.818,.469),(.844,.507),(.859,.554),(.862,.604),(.845,.671),(.806,.736),(.751,.773),(.681,.799),(.614,.801),(.552,.777),(.512,.744),(.493,.7),(.496,.653),(.506,.604),(.535,.558),(.555,.528)], 2.5, 2.0),
  ("beans", [(.368,.687),(.389,.676),(.408,.694),(.404,.729),(.451,.722),(.476,.73),(.47,.77),(.453,.799),(.499,.832),(.518,.866),(.5,.9),(.477,.895),(.471,.867),(.418,.819),(.405,.782),(.377,.746)], 2.0, 1.8),
  # The blurred foreground foliage is kept softly feathered and confined away from text.
  ("foliage", [(0,.674),(.056,.727),(.104,.775),(.162,.814),(.206,.852),(.28,.929),(.35,1),(0,1)], 5.0, 3.5)
 ])
}

manifest = {}
for name,(filename,definitions) in SCENES.items():
    im = Image.open(SOURCE/filename).convert("RGB").resize((W,H),Image.Resampling.LANCZOS)
    rgb=np.asarray(im).copy()
    # Fill only a boundary belt: hidden interior can remain original because
    # foreground motion is bounded by a few dozen pixels and covers it.
    # This is substantially more faithful near the silhouette than filling
    # the whole unseen hand or mug from a single flat image.
    union=np.zeros((H,W),np.uint8)
    entries=[]
    for key,points,feather,depth in definitions:
        mask=Image.new("L",(W,H))
        ImageDraw.Draw(mask).polygon([(round(x*W),round(y*H)) for x,y in points],fill=255)
        if key=="foliage":
            # Keep the original baked chapter counter and progress bar stationary.
            ImageDraw.Draw(mask).rectangle((0,round(.89*H),round(.245*W),round(.95*H)),fill=0)
        solid=np.asarray(mask)
        union=np.maximum(union,solid)
        soft=mask.filter(ImageFilter.GaussianBlur(feather))
        rgba=im.convert("RGBA");rgba.putalpha(soft)
        layer_file=f"{name}-{key}.webp"
        rgba.save(OUT/layer_file,"WEBP",quality=92,method=6)
        entries.append({"file":layer_file,"name":key,"depth":depth})
    # Full silhouette reconstruction at half res, composited under its
    # feathered edge; larger gaps are explicitly approximate.
    small=cv2.resize(rgb,(W//2,H//2),interpolation=cv2.INTER_AREA)
    m=cv2.resize(union,(W//2,H//2),interpolation=cv2.INTER_NEAREST)
    m=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
    filled=cv2.inpaint(small,m,4,cv2.INPAINT_TELEA)
    filled=cv2.resize(filled,(W,H),interpolation=cv2.INTER_CUBIC)
    alpha=cv2.GaussianBlur(cv2.dilate(union,np.ones((9,9),np.uint8)),(0,0),2.3).astype(np.float32)/255.
    base=np.rint(rgb*(1-alpha[:,:,None])+filled*alpha[:,:,None]).clip(0,255).astype(np.uint8)
    base_file=f"{name}-base.webp"
    Image.fromarray(base).save(OUT/base_file,"WEBP",quality=94,method=6)
    manifest[name]={"base":base_file,"layers":entries}
    print(name, len(entries), "independent layers",flush=True)
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2))
print("Prepared",sum(len(x["layers"]) for x in manifest.values()),"photo foreground layers")

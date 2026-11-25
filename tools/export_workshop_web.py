"""Export a web-ready version of the verified Blender workshop scene."""
import bpy, pathlib, math, shutil, os
from mathutils import Vector
out=pathlib.Path("assets/workshop-v04").resolve()
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
# Keep the original coaster geometry. Name its parts for the web camera/pivot.
coasters=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("Official Lusion coaster")]
if not coasters: raise RuntimeError("No coaster meshes found")
pivot=bpy.data.objects.new("CoasterProduct",None)
scene.collection.objects.link(pivot)
pivot.location=(0,0,0)
for o in coasters:
    matrix=o.matrix_world.copy()
    o.parent=pivot
    o.matrix_world=matrix
# Compact original licensed image maps for web; do not resize HDRI.
for im in bpy.data.images:
    if im.source!="FILE" or not im.has_data or max(im.size)<=1024 or im.name.lower().endswith((".hdr",".exr")): continue
    w,h=im.size
    scale=1024/max(w,h)
    im.scale(max(1,round(w*scale)),max(1,round(h*scale)))
    im.pack()
# Tone down the printed cutting mat and slightly warm the work surface.
mat=bpy.data.materials.get("Cutting mat")
if mat:
    mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.020,.046,.029,1)
grid=bpy.data.materials.get("Faded printed grid")
if grid:
    grid.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.18,.22,.16,1)
# Rotate mat and its grid together about its centre, leaving coaster independent.
from mathutils import Matrix
origin=Vector((3.8,.5,0))
rot=Matrix.Translation(origin) @ Matrix.Rotation(math.radians(5),4,"Z") @ Matrix.Translation(-origin)
for o in scene.objects:
    if o.name=="Mat" or o.name.startswith("Grid "):
        o.matrix_world=rot @ o.matrix_world
# Real-time lights are supplied by the web renderer, not baked into glTF.
bpy.ops.export_scene.gltf(filepath=str(out/"workshop.glb"),export_format="GLB",export_apply=True,export_cameras=False,export_lights=False)
hdr=next(pathlib.Path("production-assets").rglob("*.hdr"))
shutil.copyfile(hdr,out/"studio.hdr")
# Preserve original Cycles reference separately for side-by-side review.
shutil.copyfile("reference/workshop-hero.png",out/"cycles-reference.png")
for p in out.iterdir():
    print("Web asset:",p.name,p.stat().st_size,flush=True)
    if not p.stat().st_size: raise RuntimeError("Empty asset")

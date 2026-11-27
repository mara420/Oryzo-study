"""V2: a real spatial workshop with baked Cycles lighting, plus live cork geometry.
Runs from the original packed workshop.blend. Existing CC0/MIT assets only.
"""
import bpy, math, pathlib, random
from mathutils import Vector
# Reuse actual V1.1 scene construction, without its fixed-camera render calls.
src=pathlib.Path("tools/render_hero_v11.py").read_text().split("def render(name,w,h,x,height,z,show_product):",1)[0]
exec(compile(src,"tools/render_hero_v11.py","exec"),globals())
out=pathlib.Path("assets/world-v20").resolve();out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
# Additional geometry, not image overlays.
tube("Ceramic handle",[(-10.28+1.03*math.sin(i*math.pi/48),8.5,1.42+1.0*math.cos(i*math.pi/48)) for i in range(49)],.18,ceramic)
tape=material("Paper tape",(.49,.38,.22),.94);noise_surface(tape,55,3,.3,.007)
lathe("Tape roll",[(1.20,0),(1.47,0),(1.50,.04),(1.50,.89),(1.47,.93),(1.20,.93),(1.17,.89),(1.17,.04),(1.20,0)],(13,-1,.12),tape)
brass=material("Warm brass",(.48,.28,.085),.32,.76)
cube("Binder clip body",(9,-3,.32),(.9,.64,.4),dark,.07,.18)
for d in (-.24,.24):
    tube("Binder clip brass wire",[(9+d,-3,.52),(9+d,-2.88,.85),(9+d,-2.65,1.02),(9+d*.6,-2.48,.92),(9+d*.35,-2.75,.58)],.034,brass)
# Remove old hidden props from export. Use a real curved cloth instead of flat photo.
for o in list(scene.objects):
    if o.hide_render and o.type in {"MESH","CURVE","FONT"}:bpy.data.objects.remove(o,do_unlink=True)
# Coaster stays a separately transformable product with the existing physical cork maps.
product=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("Official Lusion coaster")]
assert product
for o in product:o.visible_camera=True
# Calibrate material response from the actual V2.0 and Cycles review frames.
# Existing wood roughness/normal response is too glossy and pink cork too pale.
def tune(mat,rough,spec,normal):
    n=mat.node_tree.nodes;links=mat.node_tree.links;bs=n.get("Principled BSDF")
    for link in list(bs.inputs["Roughness"].links):links.remove(link)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Specular IOR Level"].default_value=spec
    for node in n:
        if node.bl_idname=="ShaderNodeNormalMap":node.inputs["Strength"].default_value=normal
        if node.bl_idname=="ShaderNodeBump":node.inputs["Strength"].default_value=min(normal,node.inputs["Strength"].default_value)
tune(wood,.96,.19,.16);tune(cork,.94,.23,.24)
for m,sat,val,hue in [(wood,.78,1.02,.515),(cork,1.35,.67,.545)]:
    for n in m.node_tree.nodes:
        if n.bl_idname=="ShaderNodeHueSaturation":
            n.inputs["Saturation"].default_value=sat;n.inputs["Value"].default_value=val;n.inputs["Hue"].default_value=hue
for light in scene.objects:
    if light.type=="LIGHT" and light.name.startswith("Afternoon window"):
        light.data.color=(1,.82,.61);light.data.energy=2600
    elif light.type=="LIGHT" and light.name.startswith("Room bounce"):
        light.data.energy=290
scene.view_settings.exposure=.12
# Render actual reference frames before baking; useful to compare with runtime.
cam=scene.camera;scene.render.resolution_x=1100;scene.render.resolution_y=619;scene.cycles.samples=32
for name,position,target in [
    ("01-overhead",(-3,-2.4,31.5),(-3,0,.8)),
    ("02-low-angle",(-7,-16,13),(-1,0,1)),
]:
    cam.location=position;aim(cam,target);scene.render.filepath=str(out/(name+".jpg"))
    bpy.ops.render.render(write_still=True);print("Reference",name,flush=True)
# Preserve the source in a packed Blender artifact before destructively baking.
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath="/tmp/world-v20-source.blend")
# Hide moving product from static illumination. Live shadow is added in Three.js.
for o in product:o.hide_render=True;o.hide_set(True)
# Product texture stays directly exportable; use calibrated real-time color at runtime.
bs=cork.node_tree.nodes.get("Principled BSDF");inp=bs.inputs["Base Color"]
if inp.is_linked and inp.links[0].from_node.bl_idname=="ShaderNodeHueSaturation":
    adj=inp.links[0].from_node;source=adj.inputs["Color"].links[0].from_socket
    cork.node_tree.links.remove(inp.links[0]);cork.node_tree.links.new(source,inp)
# Bake static geometry into three real mesh atlases (wood, cutting mat, props).
# Explicitly bind original UV coordinates so creating bake UVs cannot change source maps.
for m in list(bpy.data.materials):
    if not m.use_nodes or m==cork:continue
    for n in list(m.node_tree.nodes):
        if n.bl_idname=="ShaderNodeTexCoord":
            for link in list(n.outputs["UV"].links):
                u=m.node_tree.nodes.new("ShaderNodeUVMap");u.uv_map="SourceUV"
                dest=link.to_socket;m.node_tree.links.remove(link);m.node_tree.links.new(u.outputs["UV"],dest)
static=[]
for o in list(scene.objects):
    if o in product or o.type not in {"MESH","CURVE","FONT"}:continue
    bpy.ops.object.select_all(action="DESELECT");o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target="MESH")
    o=bpy.context.object
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="SourceUV")
    else:o.data.uv_layers[0].name="SourceUV"
    static.append(o)
woodObjects=[o for o in static if o.name.startswith("Wooden work surface")]
matObjects=[o for o in static if o.name=="Mat" or o.name.startswith(("Grid ","Fine cutting wear"))]
props=[o for o in static if o not in woodObjects and o not in matObjects]
assert woodObjects and matObjects and props
def join_group(objects,name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    if len(objects)>1:bpy.ops.object.join()
    o=bpy.context.object;o.name=name
    return o
scene.cycles.samples=24;scene.render.bake.use_clear=True
def bake_group(objects,name,res):
    o=join_group(objects,name)
    assert o.data.uv_layers.get("SourceUV")
    uv=o.data.uv_layers.new(name="BakeUV")
    o.data.uv_layers.active_index=len(o.data.uv_layers)-1
    bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012)
    bpy.ops.object.mode_set(mode="OBJECT")
    im=bpy.data.images.new(name+"-light",width=res,height=res,alpha=False,float_buffer=False)
    im.colorspace_settings.name="sRGB"
    nodes=[]
    for m in set(o.data.materials):
        if not m or not m.use_nodes:continue
        n=m.node_tree.nodes.new("ShaderNodeTexImage");n.image=im
        for other in m.node_tree.nodes:other.select=False
        n.select=True;m.node_tree.nodes.active=n;nodes.append((m,n))
    print("Baking",name,res,flush=True)
    bpy.ops.object.bake(type="COMBINED",uv_layer="BakeUV",margin=8)
    im.filepath_raw=str(out/(name+".png"));im.file_format="PNG";im.save();im.pack()
    for m,n in nodes:m.node_tree.nodes.remove(n)
    # Keep one texture per group. Three.js uses unlit maps, so illumination
    # will not be multiplied by a second set of lights.
    baked=material(name+"-Baked",(.8,.8,.8),1)
    nodes=baked.node_tree.nodes;links=baked.node_tree.links
    tex=nodes.new("ShaderNodeTexImage");tex.image=im
    uvnode=nodes.new("ShaderNodeUVMap");uvnode.uv_map="BakeUV";links.new(uvnode.outputs["UV"],tex.inputs["Vector"])
    links.new(tex.outputs["Color"],nodes.get("Principled BSDF").inputs["Base Color"])
    o.data.materials.clear();o.data.materials.append(baked)
    for face in o.data.polygons:face.material_index=0
    # Blender 5 can expose internal UV selection attributes; never remove them.
    # Explicit UVMap and active render layer preserve the correct glTF UV channel.
    index=o.data.uv_layers.find("BakeUV");assert index>=0
    o.data.uv_layers.active_index=index;o.data.uv_layers[index].active_render=True
    print("Baked",name,flush=True)
# Bake all groups with original surrounding geometry present. The previously
# baked materials are color-only when the next group is baked; indirect bounce
# is approximate, but direct illumination and spatial shadows remain.
bake_group(woodObjects,"BakedWood",1536)
bake_group(matObjects,"BakedMat",1536)
bake_group(props,"BakedProps",1536)
for o in product:o.hide_render=False;o.hide_set(False)
pivot=bpy.data.objects.new("CoasterProduct",None);scene.collection.objects.link(pivot)
for o in product:
    matrix=o.matrix_world.copy();o.parent=pivot;o.matrix_world=matrix
# Keep original cork UV texture export compact; baked atlas remains 1536.
for im in bpy.data.images:
    if im.source=="FILE" and im.has_data and not im.name.endswith((".hdr",".exr")) and not im.name.endswith("-light") and max(im.size)>1024:
        w,h=im.size;s=1024/max(w,h);im.scale(max(1,round(w*s)),max(1,round(h*s)));im.pack()
bpy.ops.export_scene.gltf(filepath=str(out/"workshop.glb"),export_format="GLB",export_apply=True,export_cameras=False,export_lights=False)
print("Exported", (out/"workshop.glb").stat().st_size,flush=True)
(out/"README.txt").write_text("V2 spatial geometry; Cycles baked static illumination, separate MIT Lusion coaster and live shadow. Source materials CC0 Poly Haven and ambientCG; procedural props. Not a trained Gaussian Splat.\n")

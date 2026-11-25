"""Bake static indirect illumination and AO for the existing licensed workshop.
The moving product is excluded so its shadow remains dynamic in Three.js.
Outputs use the same UV0 as the exported workshop GLB.
"""
import bpy, pathlib, re
out=pathlib.Path("assets/workshop-v06").resolve()
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.bake.margin=12
scene.render.bake.use_clear=True
scene.render.bake.use_selected_to_active=False
def norm(s): return re.sub(r"[^a-z0-9]","",s.lower())
for obj in scene.objects:
    n=norm(obj.name)
    if n.startswith("officiallusioncoaster") or n.startswith("gridvertical") or n.startswith("gridhorizontal"):
        obj.hide_render=True
        obj.hide_set(True)
targets={}
for obj in scene.objects:
    if obj.type!="MESH": continue
    names=" ".join(norm(m.name) for m in obj.data.materials if m)
    if "cc0oakworktop" in names: targets["wood"]=obj
    if "cuttingmat" in names: targets["mat"]=obj
assert set(targets)=={"wood","mat"}, "Missing bake surfaces: "+str(targets)
def bake(obj,name,kind,size):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False);obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    assert obj.data.uv_layers, "UV missing "+obj.name
    obj.data.uv_layers.active_index=0
    obj.data.uv_layers[0].active_render=True
    im=bpy.data.images.new(name,width=size,height=size,alpha=False,float_buffer=False)
    im.colorspace_settings.name="Non-Color"
    nodes=[]
    for mat in obj.data.materials:
        if not mat or not mat.use_nodes: continue
        n=mat.node_tree.nodes.new("ShaderNodeTexImage");n.image=im
        for node in mat.node_tree.nodes: node.select=False
        n.select=True;mat.node_tree.nodes.active=n;nodes.append((mat,n))
    assert nodes
    print("BAKE",obj.name,kind,size,flush=True)
    if kind=="DIFFUSE":
        bpy.ops.object.bake(type="DIFFUSE",pass_filter={"DIRECT","INDIRECT"},margin=12)
    else:
        bpy.ops.object.bake(type="AO",margin=12)
    im.filepath_raw=str(out/(name+".png"));im.file_format="PNG";im.save()
    for mat,node in nodes: mat.node_tree.nodes.remove(node)
    print("SAVED",im.filepath_raw,pathlib.Path(im.filepath_raw).stat().st_size,flush=True)
for name,obj in targets.items():
    bake(obj,name+"-ao","AO",1024)
    bake(obj,name+"-irradiance","DIFFUSE",1024)
(out/"README.txt").write_text("Original UV0; static Cycles AO and diffuse direct+indirect illumination, without color, product or printed grid. Independent study using CC0 ambientCG and Poly Haven materials; geometry based on our workshop. Lusion OBJ MIT.\n")

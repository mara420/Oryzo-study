"""Independent ORYZO material and lighting study; run with Blender 5."""
import bpy, math, pathlib, random
from mathutils import Vector
P=pathlib.Path("production-assets").resolve()
OUT=pathlib.Path("renders").resolve()
OUT.mkdir(exist_ok=True)
random.seed(42)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
def find(pattern):
    files=sorted(P.rglob(pattern))
    if not files: raise RuntimeError("Missing material: "+pattern)
    return str(files[0])
def image(path, data=False):
    im=bpy.data.images.load(path,check_existing=True)
    if data: im.colorspace_settings.name="Non-Color"
    return im
def material(name,color,roughness=.65,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*color,1)
    b.inputs["Roughness"].default_value=roughness
    b.inputs["Metallic"].default_value=metal
    return m
def pbr(name,diff,normal,rough,scale=(1,1,1)):
    m=material(name,(.5,.5,.5));n=m.node_tree.nodes;l=m.node_tree.links
    b=n.get("Principled BSDF")
    uv=n.new("ShaderNodeTexCoord");mapping=n.new("ShaderNodeMapping");mapping.inputs["Scale"].default_value=scale
    l.new(uv.outputs["UV"],mapping.inputs["Vector"])
    for path,channel in ((diff,"Base Color"),(rough,"Roughness"),(normal,"Normal")):
        t=n.new("ShaderNodeTexImage");t.image=image(path,channel!="Base Color");l.new(mapping.outputs["Vector"],t.inputs["Vector"])
        if channel=="Normal":
            nm=n.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=.45;l.new(t.outputs["Color"],nm.inputs["Color"]);l.new(nm.outputs["Normal"],b.inputs["Normal"])
        else: l.new(t.outputs["Color"],b.inputs[channel])
    return m
def cube(name,loc,size,m,bevel=.02):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(m)
    if bevel:
        mod=o.modifiers.new("Edge softness","BEVEL");mod.width=bevel;mod.segments=3
        mod=o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return o
def plane(name,loc,size,m):
    bpy.ops.mesh.primitive_plane_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=(size[0],size[1],1);o.data.materials.append(m);return o
wood=pbr("CC0 oak worktop",find("wood_table_*_diff_4k.jpg"),find("wood_table_*_nor_gl_4k.jpg"),find("wood_table_*_rough_4k.jpg"),(2,2,1))
cork=pbr("CC0 cork",find("Cork*Color.jpg"),find("Cork*NormalGL.jpg"),find("Cork*Roughness.jpg"),(2,2,1))
plane("Wooden work surface",(0,0,0),(70,55),wood)
mat=material("Cutting mat",(.025,.071,.045),.92)
grid=material("Faded printed grid",(.23,.30,.22),.93)
rubber=material("Graphite rubber",(.027,.027,.021),.8)
steel=material("Brushed steel",(.42,.43,.43),.28,.85)
orange=material("Cutter polymer",(.38,.12,.035),.49)
pencil=material("Pencil lacquer",(.32,.25,.12),.48)
raw=material("Pencil wood",(.43,.30,.17),.74)
# Work mat, with fine physical printed marks on surface.
cube("Mat",(3.8,.5,.045),(24,17,.09),mat,.05)
for i in range(1,32):
    x=3.8-12+i*.75
    cube("Grid vertical",(x,.5,.092),(.009 if i%5 else .017,16.5,.001),grid,0)
for i in range(1,23):
    y=.5-8.5+i*.75
    cube("Grid horizontal",(3.8,y,.092),(23.5,.009 if i%5 else .017,.001),grid,0)
# The original licensed OBJ uses Y-up; Blender's OBJ importer converts it to Z-up.
bpy.ops.wm.obj_import(filepath=str(pathlib.Path("assets/coaster.obj").resolve()),forward_axis="NEGATIVE_Z",up_axis="Y")
objs=list(bpy.context.selected_objects)
if not objs: raise RuntimeError("OBJ import empty")
for o in objs:
    if o.type=="MESH":
        o.name="Official Lusion coaster"
        o.data.materials.clear();o.data.materials.append(cork)
        if not o.data.uv_layers:
            bpy.context.view_layer.objects.active=o
            bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT");bpy.ops.uv.smart_project();bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()
mins=[(o.matrix_world @ Vector(v)).z for o in objs if o.type=="MESH" for v in o.bound_box]
for o in objs: o.location.z+=.11-min(mins)
# Small, separate geometry studies for props; not scanned assets.
def cylinder(name,r1,r2,depth,loc,m,angle=0,vertices=32):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r1,radius2=r2,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.rotation_euler=(0,math.pi/2,angle);o.data.materials.append(m);return o
def make_pencil(x,y,angle,length):
    direction=Vector((math.cos(angle),math.sin(angle),0))
    center=Vector((x,y,.22))
    cylinder("Hexagonal pencil",.12,.12,length,center,pencil,angle,6)
    cylinder("Sharpened wood",.12,.035,.52,center+direction*(length/2+.26),raw,angle,6)
    cylinder("Graphite tip",.035,0,.16,center+direction*(length/2+.60),rubber,angle,12)
make_pencil(8,6.7,1.08,8.8)
make_pencil(-10,-5.2,-.5,6.5)
angle=.63;center=Vector((10,-6,.30))
def cutterpart(name,dx,dy,dz,size,m,bevel=.04):
    p=center+Vector((dx*math.cos(angle)-dy*math.sin(angle),dx*math.sin(angle)+dy*math.cos(angle),dz))
    o=cube(name,p,size,m,bevel);o.rotation_euler.z=angle
cutterpart("Cutter body",0,0,0,(6.6,1.05,.4),orange,.15)
cutterpart("Steel slider track",0,0,.23,(5.7,.52,.07),steel)
cutterpart("Retractable slider",-.8,0,.30,(1.05,.70,.13),rubber)
cutterpart("Exposed metal blade",-3.85,0,-.04,(1.45,.72,.055),steel,.01)
for i in range(5): cutterpart("Slider rib",-1.2+i*.2,0,.38,(.075,.6,.035),rubber,.01)
def clip(x,y,angle):
    cr=bpy.data.curves.new("Paper clip wire","CURVE");cr.dimensions="3D";cr.bevel_depth=.025;cr.bevel_resolution=4
    sp=cr.splines.new("POLY");pts=[]
    for i in range(65):
        a=math.pi*2*i/64;pts.append((math.cos(a)*.27,math.sin(a)*.60))
    pts.extend([(.13,-.36),(-.12,.33)])
    sp.points.add(len(pts)-1)
    for pt,(u,v) in zip(sp.points,pts):pt.co=(u,v,0,1)
    obj=bpy.data.objects.new("Paper clip",cr);scene.collection.objects.link(obj);obj.location=(x,y,.14);obj.rotation_euler.z=angle;cr.materials.append(steel)
clip(-11,3.8,.55);clip(-9,5,-.25);clip(-8.5,-3.5,.65)
cube("Eraser",(-8,-7,.23),(1.5,.8,.35),material("Eraser",(.43,.42,.38),.95),.08)
# Physical light and environment.
world=bpy.data.worlds.new("Studio HDRI");scene.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;links=world.node_tree.links
env=nodes.new("ShaderNodeTexEnvironment");env.image=image(find("studio_small_03*2k.hdr"));links.new(env.outputs["Color"],nodes.get("Background").inputs["Color"]);nodes.get("Background").inputs["Strength"].default_value=.4
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,"AREA");d.energy=power;d.shape="DISK";d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,(0,0,0))
area("Large soft key",(-9,-7,17),1900,13,(1,.94,.86))
area("Fill", (12,6,13),750,10,(.86,.93,1))
camdata=bpy.data.cameras.new("Hero camera");cam=bpy.data.objects.new("Hero camera",camdata);scene.collection.objects.link(cam);cam.location=(0,-2,29);aim(cam,(0,0,.7));camdata.lens=35;scene.camera=cam
scene.render.engine="CYCLES";scene.cycles.device="CPU";scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.view_settings.view_transform="AgX"
scene.render.image_settings.file_format="PNG";scene.render.filepath=str(OUT/"workshop-hero.png")
bpy.ops.wm.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"workshop.blend"))
bpy.ops.render.render(write_still=True)
print("Workshop scene and hero rendered")

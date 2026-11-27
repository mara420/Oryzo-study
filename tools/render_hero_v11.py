"""V1.1 photographic opening: static Cycles environment plates + live product.
The plate contains no visible coaster; its shadow is baked. All scene assets
are original geometry or existing CC0/MIT assets, not generated screenshots.
"""
import bpy, math, pathlib, random
from mathutils import Vector, Matrix
out=pathlib.Path("assets/hero-v11").resolve()
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
random.seed(812)
def material(name,color,rough=.6,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*color,1)
    b.inputs["Roughness"].default_value=rough;b.inputs["Metallic"].default_value=metal
    return m
def noise_surface(m,scale,detail,strength,distance,colors=None):
    n=m.node_tree.nodes;l=m.node_tree.links;b=n.get("Principled BSDF")
    tex=n.new("ShaderNodeTexNoise");tex.inputs["Scale"].default_value=scale;tex.inputs["Detail"].default_value=detail
    coord=n.new("ShaderNodeTexCoord");l.new(coord.outputs["Object"],tex.inputs["Vector"])
    bump=n.new("ShaderNodeBump");bump.inputs["Strength"].default_value=strength;bump.inputs["Distance"].default_value=distance
    l.new(tex.outputs["Fac"],bump.inputs["Height"]);l.new(bump.outputs["Normal"],b.inputs["Normal"])
    if colors:
        ramp=n.new("ShaderNodeValToRGB");ramp.color_ramp.elements[0].position=.17;ramp.color_ramp.elements[0].color=(*colors[0],1)
        ramp.color_ramp.elements[1].position=.83;ramp.color_ramp.elements[1].color=(*colors[1],1)
        l.new(tex.outputs["Fac"],ramp.inputs[0]);l.new(ramp.outputs["Color"],b.inputs["Base Color"])
def cube(name,loc,size,m,bevel=.04,rot=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.rotation_euler.z=rot;o.data.materials.append(m)
    if bevel:
        mod=o.modifiers.new("Rounded edges","BEVEL");mod.width=bevel;mod.segments=4
        o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return o
def tube(name,pts,r,m):
    cr=bpy.data.curves.new(name,"CURVE");cr.dimensions="3D";cr.bevel_depth=r;cr.bevel_resolution=4
    sp=cr.splines.new("POLY");sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,cr);scene.collection.objects.link(o);cr.materials.append(m);return o
def cyl(name,r,depth,loc,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object;o.name=name;o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    mod=o.modifiers.new("Edge detail","BEVEL");mod.width=min(.025,depth*.12);mod.segments=3
    o.modifiers.new("Weighted normals","WEIGHTED_NORMAL");return o
def tint_existing(m,saturation,value,hue=.5):
    n=m.node_tree.nodes;l=m.node_tree.links;b=n.get("Principled BSDF");inp=b.inputs["Base Color"]
    if inp.is_linked:
        old=inp.links[0];source=old.from_socket;l.remove(old)
        adj=n.new("ShaderNodeHueSaturation");adj.inputs["Hue"].default_value=hue
        adj.inputs["Saturation"].default_value=saturation;adj.inputs["Value"].default_value=value
        l.new(source,adj.inputs["Color"]);l.new(adj.outputs["Color"],inp)
wood=bpy.data.materials.get("CC0 oak worktop")
cork=bpy.data.materials.get("CC0 cork")
assert wood and cork
tint_existing(wood,.48,.75,.51);tint_existing(cork,.82,.82,.51)
mat=bpy.data.materials.get("Cutting mat");grid=bpy.data.materials.get("Faded printed grid")
noise_surface(mat,47,3,.28,.008,((.022,.034,.014),(.078,.092,.038)))
grid.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.24,.22,.14,1)
# Broaden and rotate the mat with printed grid; the coaster stays at the origin.
origin=Vector((3.8,.5,0));transform=Matrix.Translation(Vector((1.0,0,0))) @ Matrix.Translation(origin) @ Matrix.Rotation(math.radians(5),4,"Z") @ Matrix.Diagonal((1.12,1.12,1,1)) @ Matrix.Translation(-origin)
for o in list(scene.objects):
    if o.name=="Mat" or o.name.startswith("Grid "):o.matrix_world=transform@o.matrix_world
    if o.name.startswith(("Hexagonal pencil","Sharpened wood","Graphite tip","Cutter body","Steel slider","Retractable slider","Exposed metal","Slider rib","Paper clip","Eraser")):o.hide_render=True
# Scuff marks on the cutting mat, laid into the same transformed coordinates.
scuff=material("Subtle worn cuts",(.105,.112,.057),.98)
for i in range(105):
    x=random.uniform(-7.3,14.8);y=random.uniform(-7.2,8)
    angle=random.uniform(0,math.tau);length=random.uniform(.08,.48)
    a=transform@Vector((x,y,.0935));b=transform@Vector((x+math.cos(angle)*length,y+math.sin(angle)*length,.0935))
    tube("Fine cutting wear",[a,b],random.uniform(.003,.009),scuff)
# A small paper note, fine pencil drawing, metal drafting pencil and ruler.
paper=material("Warm drawing paper",(.54,.43,.29),.95);noise_surface(paper,140,2,.13,.003)
ink=material("Graphite sketch",(.12,.085,.044),.95)
note=cube("Drawing note",(-8.5,7.1,.16),(4.5,5.4,.055),paper,.025,-.18)
def notept(x,y,z=.194):
    a=-.18;return (-8.5+x*math.cos(a)-y*math.sin(a),7.1+x*math.sin(a)+y*math.cos(a),z)
for r in (1.12,1.35):
    tube("Drafted coaster circle",[notept(math.cos(i*math.tau/96)*r,math.sin(i*math.tau/96)*r) for i in range(97)],.008,ink)
for a,b in [((-1.8,0),(1.8,0)),((0,-1.7),(0,1.7)),((-1.4,-1.6),(1.4,-1.6))]:
    tube("Draft construction line",[notept(*a),notept(*b)],.006,ink)
steel=material("Brushed metal",(.32,.30,.25),.28,.85);noise_surface(steel,95,2,.13,.003)
dark=material("Dark pen grip",(.025,.026,.022),.44,.25)
penCenter=Vector((7.5,7.4,.29));direction=Vector((.49,-.872,0));rot=(0,math.pi/2,math.atan2(direction.y,direction.x))
cyl("Drafting pencil",.19,7.3,penCenter,steel,rot)
for i in range(19):
    cyl("Grip groove",.207,.022,penCenter+direction*(1.7+i*.075),dark,rot)
bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.18,radius2=.018,depth=.75,location=penCenter+direction*4.02,rotation=rot)
bpy.context.object.data.materials.append(steel)
# Tactile eraser and metal rule.
eraser=material("Used ivory eraser",(.52,.47,.37),.92);noise_surface(eraser,31,3,.45,.012,((.40,.35,.27),(.60,.55,.45)))
cube("Rounded eraser",(13,6.2,.28),(2.6,1.3,.42),eraser,.16,.45)
rule=material("Warm brushed rule",(.44,.36,.24),.39,.65)
a=.31;rc=Vector((12,-6.0,.19))
cube("Metal rule",rc,(11,1.3,.15),rule,.035,a)
for i in range(51):
    x=-5+i*.2;length=.36 if i%5==0 else .18
    def rp(dx,dy):return (rc.x+dx*math.cos(a)-dy*math.sin(a),rc.y+dx*math.sin(a)+dy*math.cos(a),.269)
    tube("Engraved rule tick",[rp(x,.58),rp(x,.58-length)],.009,ink)
# Ceramic cup, dark coffee and cloth-like material at the periphery.
ceramic=material("Speckled ceramic",(.57,.45,.31),.35);noise_surface(ceramic,36,3,.24,.012,((.30,.23,.15),(.65,.53,.38)))
def lathe(name,profile,loc,m):
    verts=[];faces=[];N=96
    for r,z in profile:
        for i in range(N):
            a=i*math.tau/N;verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(profile)-1):
        for i in range(N):
            k=j*N+i;n=j*N+(i+1)%N;faces.append((k,n,n+N,k+N))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.location=loc;mesh.materials.append(m)
    for p in mesh.polygons:p.use_smooth=True
    return obj
cup=(-12,8.5,.025)
lathe("Ceramic mug",[(.05,0),(1.43,0),(1.54,.12),(1.76,2.6),(1.80,2.75),(1.72,2.80),(1.61,2.73),(1.55,2.6),(1.32,.25),(.05,.22)],cup,ceramic)
coffee=material("Dark coffee",(.025,.013,.006),.24)
cyl("Coffee surface",1.58,.04,(-12,8.5,2.53),coffee)
linen=material("Natural linen",(.26,.20,.13),.96);noise_surface(linen,160,2,.6,.006,((.16,.12,.08),(.34,.27,.18)))
cloth=cube("Folded linen",(-12,-7.8,.12),(7.5,6,.19),linen,.09,-.29)
for i in range(5):
    cube("Linen fold",(-12.8+i*.26,-7.8,.23),(.20,5.6,.08),linen,.035,-.29)
# Lighting: soft directional afternoon window rather than an evenly lit studio.
for o in list(scene.objects):
    if o.type=="LIGHT":bpy.data.objects.remove(o,do_unlink=True)
world=scene.world;world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.18
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
def area(name,loc,power,sx,sy,color,target):
    d=bpy.data.lights.new(name,"AREA");d.energy=power;d.shape="RECTANGLE";d.size=sx;d.size_y=sy;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,target)
area("Afternoon window",(-10,1,15),2200,8,14,(1,.90,.77),(1,0,0))
area("Room bounce",(10,-9,12),380,11,11,(.85,.91,1),(0,0,0))
scene.render.engine="CYCLES";scene.cycles.device="CPU";scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.view_settings.view_transform="AgX";scene.view_settings.exposure=-.1
scene.render.resolution_percentage=100;scene.render.image_settings.file_format="JPEG";scene.render.image_settings.quality=94
cam=scene.camera;cam.data.type="PERSP";cam.data.sensor_fit="VERTICAL";cam.data.sensor_height=24
cam.data.lens=24/(2*math.tan(math.radians(35/2)));cam.data.dof.use_dof=False
product=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("Official Lusion coaster")]
assert product,"Original coaster missing"
def render(name,w,h,x,height,z,show_product):
    scene.render.resolution_x=w;scene.render.resolution_y=h
    cam.location=(x,-z,height);aim(cam,(x,0,.8))
    for o in product:o.visible_camera=show_product
    scene.render.filepath=str(out/(name+".jpg"));bpy.ops.render.render(write_still=True)
    print("RENDERED",name,(out/(name+".jpg")).stat().st_size,flush=True)
render("desktop-plate",1600,900,-3.0,31.5,2.4,False)
render("mobile-plate",900,1600,0,38,2.4,False)
render("desktop-reference",1600,900,-3.0,31.5,2.4,True)
for o in product:o.visible_camera=True
(out/"README.txt").write_text("Cycles camera-matched static environment plates with baked product shadow but product hidden from primary rays. Product is separately rendered live in Three.js. CC0 textures: ambientCG Cork001 and Poly Haven wood_table_001 / studio_small_03. Lusion coaster OBJ: MIT. Original procedural props. Desktop 16:9; mobile 9:16; vertical FOV 35 degrees.\n")

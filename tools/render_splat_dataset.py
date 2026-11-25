"""Create camera-calibrated synthetic images for a future trained 3DGS model.
Not itself a Gaussian optimization/training step.
"""
import bpy, pathlib, math, json
from mathutils import Vector
out=pathlib.Path("splat-dataset").resolve()
(out/"images").mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
cam=scene.camera
assert cam is not None
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=16
scene.cycles.use_denoising=True
w,h=640,480
scene.render.resolution_x=w
scene.render.resolution_y=h
scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGB"
cam.data.type="PERSP"
cam.data.sensor_fit="HORIZONTAL"
cam.data.sensor_width=36
cam.data.lens=34
cam.data.shift_x=cam.data.shift_y=0
fx=fy=cam.data.lens/cam.data.sensor_width*w
meta={"camera_model":"OPENCV","w":w,"h":h,"fl_x":fx,"fl_y":fy,"cx":w/2,"cy":h/2,"k1":0,"k2":0,"p1":0,"p2":0,"frames":[]}
target=Vector((1.0,0.0,.5))
def view(i,azimuth,elevation,radius,split):
    a,e=map(math.radians,(azimuth,elevation))
    cam.location=target+Vector((radius*math.cos(e)*math.cos(a),radius*math.cos(e)*math.sin(a),radius*math.sin(e)))
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    bpy.context.view_layer.update()
    rel="images/view_%03d.png"%i
    scene.render.filepath=str(out/rel)
    bpy.ops.render.render(write_still=True)
    assert (out/rel).stat().st_size>0
    meta["frames"].append({"file_path":rel,"transform_matrix":[list(row) for row in cam.matrix_world],"split":split})
    (out/"transforms.json").write_text(json.dumps(meta,indent=2))
    print("DATASET",i,split,azimuth,elevation,flush=True)
# Capture multiple views of our workbench with the same lighting and geometry.
i=0
for elev,radius,count,offset in [(42,25,8,0),(65,26,8,22.5),(83,29,4,0)]:
    for j in range(count):
        view(i,offset+j*360/count,elev,radius,"train");i+=1
for az,elev in [(15,54),(105,76),(195,54),(285,76)]:
    view(i,az,elev,26,"eval");i+=1
(out/"README.txt").write_text("Synthetic multi-view dataset, original Blender world coordinates, camera convention OpenGL/Blender (-Z viewing, +Y up), calibrated pinhole intrinsics. 20 training and 4 held-out views. Synthetic scene includes Lusion MIT coaster OBJ, CC0 ambientCG and Poly Haven textures, original procedural workshop geometry. No trained splat model is included.\n")
print("DATASET COMPLETE",len(meta["frames"]))

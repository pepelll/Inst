"""Tesla bags drop: Blender (bpy) scene with real rigid-body physics, rendered in Cycles.

Run:  python3 build.py [--preview] [--frames A-B] [--still N]
  - builds the bag mesh from the PNG silhouette (front texture / logo-free back texture),
  - simulates 5 bags with Bullet rigid bodies, bakes the result to keyframes,
  - renders 1920x1080 @ 60 fps, frames 1..126 (2.1 s) to render/frame_####.png.
Encode with: bash encode.sh
"""
import math
import os
import sys

import bpy  # noqa: I001  (bpy must be imported before bmesh/mathutils)
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "tex")
args = sys.argv[1:]
PREVIEW = "--preview" in args
FPS = 60
N_FRAMES = 126  # 2.1 s

# ---------------------------------------------------------------- bag geometry from the PNG
WIDTH_M = 0.56  # real duffel ~56 cm wide
DEPTH_HALF = 0.12  # half depth of the bag (24 cm deep)
COM_DROP = 0.035  # packed contents settle: centre of mass a bit below the geometric centre
EDGE_R = 0.095  # cross-section roundness (top/bottom edges)
END_R = 0.028  # rounding where the flat end panels meet the body

body_mask = np.array(Image.open(os.path.join(TEX, "body_mask.png"))) > 127
handle_mask = np.array(Image.open(os.path.join(TEX, "handle_mask.png"))) > 127
H_PX, W_PX = body_mask.shape
ys, xs = np.where(body_mask)
S = WIDTH_M / (xs.max() - xs.min())  # metres per pixel
CX = (xs.max() + xs.min()) / 2
CY = (ys.max() + ys.min()) / 2  # body centre -> object origin
BODY_HALF_H = (ys.max() - ys.min()) / 2 * S


def round_profile(d, r):
    return np.sqrt(np.clip(1 - (1 - np.minimum(d / r, 1)) ** 2, 0, 1))


def pillow_mesh(mask, depth_half, radius, step, name, y_offset=0.0, extend=None, duffel=False):
    """Closed mesh: front/back heightfields over the silhouette, meeting at the outline.
    duffel=True: rounded cross-section from the column's top/bottom + flat end panels (like a real duffel);
    otherwise a plain rounded tube from the distance to the outline (handles)."""
    m = mask
    if extend is not None:
        m = m | extend
    if duffel:
        rows = np.arange(H_PX)[:, None]
        cols = np.arange(W_PX)[None, :]
        anyc, anyr = m.any(0), m.any(1)
        top = np.where(anyc, m.argmax(0), 0)[None, :]
        bot = np.where(anyc, H_PX - 1 - m[::-1].argmax(0), 0)[None, :]
        left = np.where(anyr, m.argmax(1), 0)[:, None]
        right = np.where(anyr, W_PX - 1 - m[:, ::-1].argmax(1), 0)[:, None]
        dv = np.minimum(rows - top, bot - rows).clip(0) * S
        dh = np.minimum(cols - left, right - cols).clip(0) * S
        hgt = depth_half * round_profile(dv, radius) * round_profile(dh, END_R)
    else:
        dt = ndi.distance_transform_edt(m) * S
        hgt = depth_half * round_profile(dt, radius)
    gy = np.arange(0, H_PX, step)
    gx = np.arange(0, W_PX, step)
    inside = m[np.ix_(gy, gx)]
    quads = inside[:-1, :-1] & inside[1:, :-1] & inside[:-1, 1:] & inside[1:, 1:]
    used = np.zeros_like(inside)
    used[:-1, :-1] |= quads
    used[1:, :-1] |= quads
    used[:-1, 1:] |= quads
    used[1:, 1:] |= quads
    # boundary vertices = corners of quads touching a non-quad cell
    qpad = np.pad(quads, 1)
    cnt = qpad[:-1, :-1].astype(int) + qpad[1:, :-1] + qpad[:-1, 1:] + qpad[1:, 1:]
    boundary = used & (cnt < 4)

    vid_f = -np.ones(inside.shape, int)
    vid_b = -np.ones(inside.shape, int)
    verts, uvs = [], []
    ii, jj = np.where(used)
    for i, j in zip(ii, jj):
        px, py = gx[j], gy[i]
        x = (px - CX) * S
        z = (CY - py) * S
        h = 0.0 if boundary[i, j] else hgt[py, px]
        vid_f[i, j] = len(verts)
        verts.append([x, y_offset - h, z + COM_DROP])
        uvs.append((px / W_PX, 1 - py / H_PX))
        if boundary[i, j]:
            vid_b[i, j] = vid_f[i, j]
        else:
            vid_b[i, j] = len(verts)
            verts.append([x, y_offset + h, z + COM_DROP])
            uvs.append((px / W_PX, 1 - py / H_PX))
    verts = np.array(verts)

    # smooth the staircase outline along the boundary loop
    bverts = {vid_f[i, j] for i, j in zip(*np.where(boundary))}
    nbr = {v: set() for v in bverts}
    qi, qj = np.where(quads)
    for i, j in zip(qi, qj):
        c = [vid_f[i, j], vid_f[i, j + 1], vid_f[i + 1, j + 1], vid_f[i + 1, j]]
        for k in range(4):
            a_, b_ = c[k], c[(k + 1) % 4]
            if a_ in bverts and b_ in bverts:
                # an outline edge belongs to only one quad: check the neighbour quad across it
                nbr[a_].add(b_)
                nbr[b_].add(a_)
    blist = list(bverts)
    for _ in range(10):
        new = verts.copy()
        for v in blist:
            n = list(nbr[v])
            if n:
                new[v, [0, 2]] = 0.5 * verts[v, [0, 2]] + 0.5 * verts[n][:, [0, 2]].mean(0)
        verts = new

    faces, face_mat, face_uv = [], [], []
    for i, j in zip(qi, qj):
        f = [vid_f[i, j], vid_f[i + 1, j], vid_f[i + 1, j + 1], vid_f[i, j + 1]]
        b = [vid_b[i, j], vid_b[i, j + 1], vid_b[i + 1, j + 1], vid_b[i + 1, j]]
        faces.append(f)
        face_mat.append(0)
        faces.append(b)
        face_mat.append(1)

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces)
    me.update()
    uv = me.uv_layers.new(name="UV")
    loop_uv = np.array([uvs[l.vertex_index] for l in me.loops]).ravel()
    uv.data.foreach_set("uv", loop_uv)
    me.polygons.foreach_set("material_index", face_mat)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    # merge duplicated faces where front/back collapse onto the outline, fix normals
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    seen, dup = set(), []
    for f in bm.faces:
        key = frozenset(v.index for v in f.verts)
        if f.calc_area() < 1e-10 or key in seen:
            dup.append(f)
        seen.add(key)
    bmesh.ops.delete(bm, geom=dup, context="FACES")
    bm.to_mesh(me)
    bm.free()
    return me


def hull_mesh(src_me, name, stride=7):
    bm = bmesh.new()
    co = [v.co.copy() for v in src_me.vertices][::stride]
    for c in co:
        bm.verts.new(c)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start = 1
sc.frame_end = N_FRAMES


def image_node(nt, file):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(os.path.join(TEX, file))
    n.interpolation = "Cubic"
    return n


def leather_material(name, tex_file):
    """Front-projected photo where the surface faces the camera of the photo; tiled leather grain from the same
    photo on the top / bottom / ends (where projection would smear), plus a dark piping line along the seam."""
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    L = nt.links.new
    bsdf = nt.nodes["Principled BSDF"]
    img = image_node(nt, tex_file)

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    vt = nt.nodes.new("ShaderNodeVectorTransform")
    vt.vector_type, vt.convert_from, vt.convert_to = "NORMAL", "WORLD", "OBJECT"
    L(geo.outputs["True Normal"], vt.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(vt.outputs["Vector"], sep.inputs["Vector"])

    def absn(sock):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = "ABSOLUTE"
        L(sock, n.inputs[0])
        return n.outputs[0]

    def smooth(sock, a, b, invert=False):
        n = nt.nodes.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        n.inputs["From Min"].default_value = a
        n.inputs["From Max"].default_value = b
        n.inputs["To Min"].default_value = 1.0 if invert else 0.0
        n.inputs["To Max"].default_value = 0.0 if invert else 1.0
        L(sock, n.inputs["Value"])
        return n.outputs["Result"]

    side = smooth(absn(sep.outputs["Y"]), 0.55, 0.88, invert=True)
    ends = smooth(absn(sep.outputs["X"]), 0.55, 0.85)

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sc_ = nt.nodes.new("ShaderNodeVectorMath")
    sc_.operation = "SCALE"
    sc_.inputs["Scale"].default_value = 8.3  # tile = 12 cm, same grain size as the photo
    L(tc.outputs["Object"], sc_.inputs[0])
    grain = image_node(nt, "plain.png")
    grain.projection = "BOX"
    grain.projection_blend = 0.35
    grain.extension = "MIRROR"
    L(sc_.outputs["Vector"], grain.inputs["Vector"])
    dark = nt.nodes.new("ShaderNodeMix")
    dark.data_type = "RGBA"
    dark.blend_type = "MULTIPLY"
    dark.inputs["B"].default_value = (0.42, 0.42, 0.43, 1)
    L(ends, dark.inputs["Factor"])
    L(grain.outputs["Color"], dark.inputs["A"])

    # straps continue over the top / bottom (photo columns where the straps are)
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UV"
    smask = image_node(nt, "strap_mask.png")
    smask.image.colorspace_settings.name = "Non-Color"
    smask.interpolation = "Linear"
    L(uvn.outputs["UV"], smask.inputs["Vector"])
    no_end = smooth(absn(sep.outputs["X"]), 0.35, 0.6, invert=True)
    sfac = nt.nodes.new("ShaderNodeMath")
    sfac.operation = "MULTIPLY"
    L(smask.outputs["Color"], sfac.inputs[0])
    L(no_end, sfac.inputs[1])
    strap = nt.nodes.new("ShaderNodeMix")
    strap.data_type = "RGBA"
    strap.inputs["B"].default_value = (0.018, 0.018, 0.018, 1)
    L(sfac.outputs[0], strap.inputs["Factor"])
    L(dark.outputs["Result"], strap.inputs["A"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L(side, mix.inputs["Factor"])
    L(img.outputs["Color"], mix.inputs["A"])
    L(strap.outputs["Result"], mix.inputs["B"])

    # piping along the seam (object y ~ 0 on the outline)
    sep2 = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep2.inputs["Vector"])
    pipe = smooth(absn(sep2.outputs["Y"]), 0.004, 0.009, invert=True)
    pipe_k = nt.nodes.new("ShaderNodeMath")
    pipe_k.operation = "MULTIPLY"
    L(pipe, pipe_k.inputs[0])
    L(no_end, pipe_k.inputs[1])  # the zipper seam runs over the top, not across the end panels
    pipe_mix = nt.nodes.new("ShaderNodeMix")
    pipe_mix.data_type = "RGBA"
    pipe_mix.inputs["B"].default_value = (0.012, 0.012, 0.012, 1)
    L(pipe_k.outputs[0], pipe_mix.inputs["Factor"])
    L(mix.outputs["Result"], pipe_mix.inputs["A"])
    color = pipe_mix.outputs["Result"]
    L(color, bsdf.inputs["Base Color"])

    lum = nt.nodes.new("ShaderNodeRGBToBW")
    L(color, lum.inputs["Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["From Min"].default_value = 0.05
    rough.inputs["From Max"].default_value = 0.35
    rough.inputs["To Min"].default_value = 0.4
    rough.inputs["To Max"].default_value = 0.62
    L(lum.outputs["Val"], rough.inputs["Value"])
    L(rough.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.4
    bsdf.inputs["Coat Weight"].default_value = 0.06
    bsdf.inputs["Coat Roughness"].default_value = 0.35
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.0006
    L(lum.outputs["Val"], bump.inputs["Height"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


mat_front = leather_material("BagFront", "front.png")
mat_back = leather_material("BagBack", "back.png")

body_me = pillow_mesh(body_mask, DEPTH_HALF, EDGE_R, 4, "BagBody", duffel=True)
# handle: a thin rounded tube in the middle plane, sunk a little into the body top
yy, xx = np.mgrid[-14:15, -14:15]
handle_ext = ndi.binary_dilation(handle_mask, structure=(xx**2 + yy**2) <= 14**2) & body_mask
handle_me = pillow_mesh(handle_mask, 0.012, 0.011, 3, "BagHandle", extend=handle_ext)
for me in (body_me, handle_me):
    me.materials.append(mat_front)
    me.materials.append(mat_back)
# collision hull: same silhouette, slightly boxier edges (a packed bag sits on its faces instead of rolling)
hull_src = pillow_mesh(body_mask, DEPTH_HALF, 0.06, 8, "HullSrc", duffel=True)
hull_body_me = hull_mesh(hull_src, "HullBody", 2)
hull_handle_me = hull_mesh(handle_me, "HullHandle", 3)

# studio: shadow-catcher floor; the seamless grey backdrop is composited in encode (no horizon possible)
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
catcher = bpy.context.object
catcher.name = "FloorCatcher"
catcher.is_shadow_catcher = True
fm = bpy.data.materials.new("Floor")
fb = fm.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.42, 0.42, 0.43, 1)
fb.inputs["Roughness"].default_value = 0.8
catcher.data.materials.append(fm)

# camera: static, slightly above, looking down at the pile
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam_data.sensor_width = 36
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
cam.location = (0.0, -2.55, 0.92)
target = Vector((0.0, 0.0, 0.22))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam


def area(name, loc, look, size, energy, size_y=None, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = color
    if size_y:
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = size, size_y
    else:
        ld.size = size
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


area("Key", (-0.8, -1.2, 2.4), (0, 0, 0.1), 2.2, 120, 1.5)
area("Fill", (1.8, -2.0, 1.0), (0, 0, 0.3), 2.0, 28)
area("Top", (0.0, 0.5, 2.8), (0, 0.2, 0), 2.5, 50)
world = bpy.data.worlds.new("World")
sc.world = world
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.5, 0.5, 0.52, 1)
bg.inputs["Strength"].default_value = 0.15

# ---------------------------------------------------------------- bags + physics
bpy.ops.rigidbody.world_add()
rbw = sc.rigidbody_world
rbw.substeps_per_frame = 12
rbw.solver_iterations = 40
rbw.point_cache.frame_start = 1
rbw.point_cache.frame_end = N_FRAMES + 2

# floor collider: big passive box with its top at z = 0
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.5))
floor_box = bpy.context.object
floor_box.name = "FloorBox"
floor_box.scale = (12, 12, 1)
bpy.ops.rigidbody.object_add()
floor_box.rigid_body.type = "PASSIVE"
floor_box.rigid_body.friction = 0.8
floor_box.rigid_body.restitution = 0.05
floor_box.hide_render = True

# (release frame, location, rotation XYZ degrees) - bag 1 is already in frame at t = 0
# (release frame, location, rotation XYZ deg); picked by search_drops.py for a compact pile with logos to camera
DROPS = [
    (1, (-0.08, 0.05, 0.6), (8.8, -5.7, 6.8)),
    (13, (0.302, 0.188, 1.08), (-14.7, -6.5, -32.2)),
    (28, (-0.202, 0.007, 1.1), (19.6, -24.8, 25.4)),
    (37, (0.179, -0.284, 1.12), (-14.9, -10.0, -3.4)),
    (52, (-0.005, -0.066, 1.25), (-8.5, 8.4, 2.0)),
]
if os.environ.get("DROPS"):
    DROPS = [tuple(d) for d in __import__("json").loads(os.environ["DROPS"])]
V_ENTRY = -1.6  # m/s downward when released just above the frame
bags = []
bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
for k, (rel, loc, rot) in enumerate(DROPS):
    bag = bpy.data.objects.new(f"Bag{k}", body_me)
    sc.collection.objects.link(bag)
    handle = bpy.data.objects.new(f"Bag{k}_handle", handle_me)
    sc.collection.objects.link(handle)
    handle.parent = bag
    hb = bpy.data.objects.new(f"Bag{k}_hullBody", hull_body_me)
    hh = bpy.data.objects.new(f"Bag{k}_hullHandle", hull_handle_me)
    for h in (hb, hh):
        sc.collection.objects.link(h)
        h.parent = bag
        h.hide_render = True
        h.display_type = "WIRE"
    bag.location = loc
    bag.rotation_euler = Euler([math.radians(r) for r in rot])
    bags.append((bag, rel, [hb, hh], handle))

    for ob, shape in ((bag, "COMPOUND"), (hb, "CONVEX_HULL"), (hh, "CONVEX_HULL")):
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.rigidbody.object_add()
        ob.select_set(False)
        rb = ob.rigid_body
        rb.collision_shape = shape
        rb.mass = {"COMPOUND": 7.0, "CONVEX_HULL": 1.0}[shape] if ob is not hh else 0.2
        rb.friction = 1.0
        rb.restitution = 0.0
        rb.linear_damping = 0.25
        rb.angular_damping = 0.8
        rb.use_margin = True
        rb.collision_margin = 0.003
    # held (kinematic) high above its drop point (2 m apart, never overlapping), then for the last 3 frames moved
    # along a free-fall path: Blender hands the kinematic velocity to the dynamic body, so it enters already falling
    if rel > 1:
        x_, y_, z_ = loc
        bag.location = (x_, y_, 10.0 + 2.0 * k)
        bag.keyframe_insert("location", frame=1)
        bag.keyframe_insert("location", frame=rel - 4)
        for back in (3, 2, 1):
            t = -(back - 1) / FPS
            bag.location = (x_, y_, z_ + V_ENTRY * t - 0.5 * 9.81 * t * t)
            bag.keyframe_insert("location", frame=rel - back)
        bag.keyframe_insert("rotation_euler", frame=1)
        bag.rigid_body.kinematic = True
        bag.rigid_body.keyframe_insert("kinematic", frame=1)
        bag.rigid_body.keyframe_insert("kinematic", frame=rel - 1)
        bag.rigid_body.kinematic = False
        bag.rigid_body.keyframe_insert("kinematic", frame=rel)

# simulate and bake to plain keyframes (so Cycles motion blur sees the motion)
mats = {b.name: [] for b, *_ in bags}
for f in range(1, N_FRAMES + 2):
    sc.frame_set(f)
    for b, *_ in bags:
        mats[b.name].append(b.matrix_world.copy())
for b, rel, hulls, handle in bags:
    for h in hulls:
        bpy.data.objects.remove(h, do_unlink=True)
    bpy.context.view_layer.objects.active = b
    b.select_set(True)
    bpy.ops.rigidbody.object_remove()
    b.select_set(False)
    b.animation_data_clear()
    b.rotation_mode = "QUATERNION"
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    for f, m in enumerate(mats[b.name], start=1):
        loc, q, _ = m.decompose()
        b.location = loc
        b.rotation_quaternion = q
        b.keyframe_insert("location", frame=f)
        b.keyframe_insert("rotation_quaternion", frame=f)
bpy.data.objects.remove(floor_box, do_unlink=True)
sc.rigidbody_world.enabled = False

# dump the trajectory for quick checks (+ json with loc/quat for the drop search)
import json as _json

_traj = {b.name: [[*m.decompose()[0], *m.decompose()[1]] for m in mats[b.name]] for b, *_ in bags}
_json.dump(_traj, open(os.environ.get("TRAJ", os.path.join(HERE, "trajectory.txt")) + ".json", "w"))
with open(os.environ.get("TRAJ", os.path.join(HERE, "trajectory.txt")), "w") as fh:
    for f in range(N_FRAMES):
        row = []
        for b, *_ in bags:
            loc, q, _ = mats[b.name][f].decompose()
            row.append(f"{loc.x:+.3f},{loc.y:+.3f},{loc.z:+.3f}")
        fh.write(f"{f + 1:3d} " + "  ".join(row) + "\n")

if "--sim-only" in args:
    sys.exit(0)

# ---------------------------------------------------------------- render settings
r = sc.render
r.engine = "CYCLES"
sc.cycles.device = "CPU"
r.resolution_x, r.resolution_y = 1920, 1080
r.resolution_percentage = 40 if PREVIEW else 75  # 1440x810, upscaled to 1080p in encode.py
sc.cycles.samples = 24 if PREVIEW else 12
sc.cycles.adaptive_threshold = 0.06
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 3
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 0
sc.cycles.volume_bounces = 0
r.use_motion_blur = True
r.motion_blur_shutter = 0.35
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "Medium Contrast"
sc.view_settings.exposure = 0.0
r.film_transparent = True
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGBA"
r.image_settings.color_depth = "8"
r.threads_mode = "AUTO"
r.use_persistent_data = True
r.use_overwrite = False  # resumable: frames already on disk are skipped
r.use_placeholder = True

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "bags.blend"))

out = os.path.join(HERE, "render_preview" if PREVIEW else "render")
os.makedirs(out, exist_ok=True)
if "--still" in args:
    for fr in args[args.index("--still") + 1].split(","):
        sc.frame_set(int(fr))
        r.filepath = os.path.join(out, f"still_{int(fr):04d}.png")
        bpy.ops.render.render(write_still=True)
elif "--frames" in args:
    a_, b_ = map(int, args[args.index("--frames") + 1].split("-"))
    sc.frame_start, sc.frame_end = a_, b_
    r.filepath = os.path.join(out, "frame_")
    bpy.ops.render.render(animation=True)

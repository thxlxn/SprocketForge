import json
import math
import numpy as np
import cv2
from PIL import Image

# --- SETTINGS ---
TARGET_FACE_COUNT = 15000 
RENDER_SIZE = 800

def get_rotation_matrix(rot):
    """
    Creates a rotation matrix.
    """
    safe_rot = rot[:3]
    if len(safe_rot) < 3:
        safe_rot += [0] * (3 - len(safe_rot))

    rx, ry, rz = [math.radians(a) for a in safe_rot]

    # Roll
    mat_z = np.array([
        [math.cos(rz), -math.sin(rz), 0, 0],
        [math.sin(rz), math.cos(rz), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

    # Pitch
    mat_x = np.array([
        [1, 0, 0, 0],
        [0, math.cos(rx), -math.sin(rx), 0],
        [0, math.sin(rx), math.cos(rx), 0],
        [0, 0, 0, 1]
    ])

    # Yaw
    mat_y = np.array([
        [math.cos(ry), 0, math.sin(ry), 0],
        [0, 1, 0, 0],
        [-math.sin(ry), 0, math.cos(ry), 0],
        [0, 0, 0, 1]
    ])

    # combined rotation
    return np.dot(mat_y, np.dot(mat_x, mat_z))

def compose_transform(pos, rot, scale):
    """
    Composes the local transform matrix
    """
    safe_scale = scale[:3]
    if len(safe_scale) < 3: safe_scale += [1] * (3 - len(safe_scale))
    
    mat_s = np.identity(4)
    mat_s[0,0], mat_s[1,1], mat_s[2,2] = safe_scale

    mat_r = get_rotation_matrix(rot)

    safe_pos = pos[:3]
    if len(safe_pos) < 3: safe_pos += [0] * (3 - len(safe_pos))

    mat_t = np.identity(4)
    mat_t[:3, 3] = safe_pos

    # Order: T * R * S
    return np.dot(mat_t, np.dot(mat_r, mat_s))

def bake_geometry(data):
    """
    Flattens hierarchy and handles symmetry.
    """
    objects = {o["vuid"]: o for o in data.get("objects", [])}
    blueprints = {b["id"]: b for b in data.get("blueprints", [])}
    meshes = {m["vuid"]: m for m in data.get("meshes", [])}

    # 1. Calculate Global Matrices
    global_matrices = {}

    def get_global_matrix(vuid):
        if vuid in global_matrices: return global_matrices[vuid]
        if vuid not in objects: return np.identity(4)

        obj = objects[vuid]
        
        tf = obj.get("transform", {})
        pos = tf.get("pos", [0, 0, 0])
        rot = tf.get("rot", [0, 0, 0])
        scale = tf.get("scale", [1, 1, 1])
        local_mat = compose_transform(pos, rot, scale)

        parent_vuid = obj.get("pvuid", -1)
        if parent_vuid != -1:
            parent_mat = get_global_matrix(parent_vuid)
            global_mat = np.dot(parent_mat, local_mat)
        else:
            global_mat = local_mat

        global_matrices[vuid] = global_mat
        return global_mat

    # Pre-calculate matrices for everything (parents might be non-geometry)
    for vuid in objects:
        get_global_matrix(vuid)

    baked_vertices = []
    baked_faces = []
    vertex_offset = 0

    def add_mesh_to_scene(mesh_id, matrix):
        nonlocal vertex_offset
        if mesh_id not in meshes: return

        raw_mesh = meshes[mesh_id]["meshData"]["mesh"]
        verts = raw_mesh["vertices"]
        faces = raw_mesh["faces"]

        if not verts: return
        np_verts = np.array(verts).reshape(-1, 3)
        ones = np.ones((len(np_verts), 1))
        np_verts_homo = np.hstack((np_verts, ones))
        transformed_verts = np.dot(matrix, np_verts_homo.T).T[:, :3]

        baked_vertices.extend(transformed_verts.tolist())
        for f in faces:
            new_indices = [idx + vertex_offset for idx in f["v"]]
            baked_faces.append(new_indices)
        vertex_offset += len(transformed_verts)

    # 2. Iterate and Bake
    for vuid, obj in objects.items():
        
        # --- STRICT FILTER ---
        # 1. Ignore Procedural Cannons explicitly
        if "cannonBlueprintVuid" in obj: continue
        
        # 2. Only process objects that have a Structure Blueprint (Plates, Turrets, Hulls)
        bp_id = obj.get("structureBlueprintVuid", -1)
        if bp_id == -1 or bp_id not in blueprints: continue

        bp = blueprints[bp_id]
        if bp.get("type") in ["decal", "crew", "internal"]: continue

        mesh_id = bp.get("blueprint", {}).get("bodyMeshVuid", -1)
        
        # Render Original
        matrix = global_matrices[vuid]
        add_mesh_to_scene(mesh_id, matrix)

        # --- IMPLICIT SYMMETRY ---
        # If this is a structural object with symmetry enabled (Bit 3 / Value 4)
        # and no explicit mirror object exists, we generate the ghost.
        flags = obj.get("flags", 0)
        mirror_vuid = obj.get("transform", {}).get("mirrorVuid", -1)

        if (flags & 4) and mirror_vuid == -1:
            parent_vuid = obj.get("pvuid", -1)
            parent_mat = global_matrices.get(parent_vuid, np.identity(4))
            
            tf = obj.get("transform", {})
            pos = tf.get("pos", [0,0,0])
            rot = tf.get("rot", [0,0,0])
            scale = tf.get("scale", [1,1,1])

            mirrored_pos = [-pos[0], pos[1], pos[2]]
            mirrored_rot = [rot[0], -rot[1], -rot[2]]
            local_mirror_mat = compose_transform(mirrored_pos, mirrored_rot, scale)
            global_mirror_mat = np.dot(parent_mat, local_mirror_mat)
            
            add_mesh_to_scene(mesh_id, global_mirror_mat)

    return np.array(baked_vertices), baked_faces

def generate_render_frames(filepath, size=600, frames_count=60):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return []

    all_vertices, all_faces = bake_geometry(data)

    if len(all_vertices) == 0:
        return []

    min_vals = np.min(all_vertices, axis=0)
    max_vals = np.max(all_vertices, axis=0)
    center = (min_vals + max_vals) / 2
    dims = max_vals - min_vals
    max_dim = np.max(dims)
    if max_dim == 0: max_dim = 1
    
    padding = size * 0.2
    scale_factor = (size - padding) / max_dim

    stride = 1
    if len(all_faces) > TARGET_FACE_COUNT:
        stride = int(len(all_faces) / TARGET_FACE_COUNT)
    optimized_faces = all_faces[::stride]

    pil_frames = []

    for i in range(frames_count):
        img = np.zeros((size, size, 3), dtype=np.uint8)

        angle = (i / frames_count) * 2 * math.pi
        
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        tilt = math.radians(20)
        cos_t, sin_t = math.cos(tilt), math.sin(tilt)

        rot_y = np.array([
            [cos_a, 0, sin_a],
            [0, 1, 0],
            [-sin_a, 0, cos_a]
        ])
        
        rot_x = np.array([
            [1, 0, 0],
            [0, cos_t, -sin_t],
            [0, sin_t, cos_t]
        ])
        
        cam_mat = np.dot(rot_x, rot_y)

        v_centered = all_vertices - center
        v_rotated = np.dot(v_centered, cam_mat.T)
        
        sx = (v_rotated[:, 0] * scale_factor) + (size / 2)
        sy = (size / 2) - (v_rotated[:, 1] * scale_factor) 

        pts_cache = np.column_stack((sx, sy)).astype(np.int32)

        for face in optimized_faces:
            pts = pts_cache[face]
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (100, 200, 255), 1)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_frames.append(Image.fromarray(img_rgb))

    return pil_frames
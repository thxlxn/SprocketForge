import json
import math
import numpy as np
import cv2
from PIL import Image
import os
import zipfile

# --- SETTINGS ---
TARGET_FACE_COUNT = 15000 
RENDER_SIZE = 800

# ==========================================
# RENDERING MATH (collapsed)
# ==========================================
def get_rotation_matrix(rot):
    safe_rot = rot[:3]
    if len(safe_rot) < 3:
        safe_rot += [0] * (3 - len(safe_rot))

    rx, ry, rz = [math.radians(a) for a in safe_rot]

    mat_z = np.array([
        [math.cos(rz), -math.sin(rz), 0, 0],
        [math.sin(rz), math.cos(rz), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

    mat_x = np.array([
        [1, 0, 0, 0],
        [0, math.cos(rx), -math.sin(rx), 0],
        [0, math.sin(rx), math.cos(rx), 0],
        [0, 0, 0, 1]
    ])

    mat_y = np.array([
        [math.cos(ry), 0, math.sin(ry), 0],
        [0, 1, 0, 0],
        [-math.sin(ry), 0, math.cos(ry), 0],
        [0, 0, 0, 1]
    ])

    return np.dot(mat_y, np.dot(mat_x, mat_z))

def compose_transform(pos, rot, scale):
    safe_scale = scale[:3]
    if len(safe_scale) < 3: safe_scale += [1] * (3 - len(safe_scale))
    
    mat_s = np.identity(4)
    mat_s[0,0], mat_s[1,1], mat_s[2,2] = safe_scale

    mat_r = get_rotation_matrix(rot)

    safe_pos = pos[:3]
    if len(safe_pos) < 3: safe_pos += [0] * (3 - len(safe_pos))

    mat_t = np.identity(4)
    mat_t[:3, 3] = safe_pos

    return np.dot(mat_t, np.dot(mat_r, mat_s))

def bake_geometry(data):
    objects = {o["vuid"]: o for o in data.get("objects", [])}
    blueprints = {b["id"]: b for b in data.get("blueprints", [])}
    meshes = {m["vuid"]: m for m in data.get("meshes", [])}

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

    for vuid, obj in objects.items():
        if "cannonBlueprintVuid" in obj: continue
        
        bp_id = obj.get("structureBlueprintVuid", -1)
        if bp_id == -1 or bp_id not in blueprints: continue

        bp = blueprints[bp_id]
        if bp.get("type") in ["decal", "crew", "internal"]: continue

        mesh_id = bp.get("blueprint", {}).get("bodyMeshVuid", -1)
        
        matrix = global_matrices[vuid]
        add_mesh_to_scene(mesh_id, matrix)

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


# ==========================================
# FILE EDITING FUNCTIONS
# ==========================================

def recursive_thickness_update(data, target_thick):
    """Looks for the right thickness blocks and replaces their values"""
    # Crawl the whole JSON tree to find "t": [...]
    if isinstance(data, dict):
        for key, value in data.items():
            # found "t" list?
            if key == "t" and isinstance(value, list):
                # preserve exact length, fill with new value
                data[key] = [target_thick] * len(value)
            
            # keep digging deeply
            elif isinstance(value, (dict, list)):
                recursive_thickness_update(value, target_thick)
                
    elif isinstance(data, list):
        for item in data:
            recursive_thickness_update(item, target_thick)

def edit_blueprint_file(filepath, settings):
    try:
        # Load safely as JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # ------------------------------------------
        # 1. ARMOR THICKNESS (Global Recursive Fix)
        # ------------------------------------------
        if settings.get("use_thickness"):
            target_thick = settings.get("thickness_val", 5)
            recursive_thickness_update(data, target_thick)

        # ------------------------------------------
        # 2. TRACK OPTIONS
        # ------------------------------------------
        if settings.get("use_tracks"):
            
            # Invisible Tracks
            if settings.get("invisible_tracks"):
                track_guid = "843f3a65-30f6-4180-a719-f3af1e2bacfe"
                
                blueprints = data.get("blueprints", [])
                for bp in blueprints:
                    # Look for type "trackBelt"
                    if bp.get("type") == "trackBelt":
                        # Safety check: ensure "blueprint" dict exists
                        if "blueprint" not in bp:
                            bp["blueprint"] = {}
                        
                        # Apply the GUID to the inner blueprint data
                        bp["blueprint"]["segmentID"] = track_guid

        # ------------------------------------------
        # SAVE AS COPY
        # ------------------------------------------
        base_dir = os.path.dirname(filepath)
        base_name = os.path.basename(filepath)
        name_only, ext = os.path.splitext(base_name)
        
        new_name = f"{name_only} edited{ext}"
        new_path = os.path.join(base_dir, new_name)

        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return True, f"Saved as: {new_name}"

    except Exception as e:
        return False, f"Error: {str(e)}"
    

# ==========================================
# BLUEPRINT SHARING FUNCTIONS
# ==========================================

def get_blueprint_decals(blueprint_data):
    """
    Parses blueprint data and returns a unique set of local decal paths.
    Ignores external https links.
    """
    decals = set()
    blueprints = blueprint_data.get("blueprints", [])
    
    for bp in blueprints:
        if bp.get("type") == "decal":
            image_url = bp.get("blueprint", {}).get("imageURL")
            if image_url and not image_url.startswith("http"):
                decals.add(image_url)
                
    return list(decals)

def pack_blueprint_for_sharing(blueprint_path, sprocket_dir):
    """
    Takes a blueprint file, finds all required local decals in the user's directory,
    and packs everything into a ZIP file formatted for sharing.
    """
    try:
        with open(blueprint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        decal_paths = get_blueprint_decals(data)
        
        # prepare zip name
        base_name = os.path.basename(blueprint_path)
        name_only = os.path.splitext(base_name)[0]
        zip_name = f"{name_only}_package.zip"
        zip_path = os.path.join(os.path.dirname(blueprint_path), zip_name)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            
            zipf.write(blueprint_path, arcname=os.path.join("vehicles", base_name))
            
            
            for local_path in decal_paths:
                full_decal_path = os.path.join(sprocket_dir, local_path)
                
                if not os.path.exists(full_decal_path):
                    potential_path = os.path.join(sprocket_dir, "Sprocket_Data", "StreamingAssets", "Decals", os.path.basename(local_path))
                    if os.path.exists(potential_path):
                        full_decal_path = potential_path
                    else:
                        potential_path = os.path.join(sprocket_dir, "Decals", os.path.basename(local_path))
                        if os.path.exists(potential_path):
                            full_decal_path = potential_path

                if os.path.exists(full_decal_path):
                    decal_filename = os.path.basename(full_decal_path)
                    zipf.write(full_decal_path, arcname=os.path.join("decals", decal_filename))
                else:
                    print(f"Warning: Could not find decal file: {local_path}")
        
        return True, f"Created package: {zip_name}"
        
    except Exception as e:
        return False, f"Packaging error: {str(e)}"
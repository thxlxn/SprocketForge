import math
import json
import numpy as np
import cv2
from PIL import Image

def euler_to_matrix(rot_deg):
    """
    Converts Euler angles [x, y, z] in degrees to a rotation matrix.
    """
    ax, ay, az = [math.radians(a) for a in rot_deg[:3]]
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return np.dot(ry, np.dot(rx, rz))

def compose_matrix(pos, rot, scale):
    """
    Creates a 4x4 Global Transformation Matrix.
    """
    S = np.identity(4)
    S[0,0], S[1,1], S[2,2] = scale
    
    R = np.identity(4)
    R[:3, :3] = euler_to_matrix(rot)
    
    T = np.identity(4)
    T[:3, 3] = pos
    
    return np.dot(T, np.dot(R, S))

def apply_transform(vertices, matrix):
    """
    Applies the matrix to a list of vertices.
    """
    if not vertices: return []
    ones = np.ones((len(vertices), 1))
    v_homo = np.hstack((vertices, ones))
    v_transformed = np.dot(matrix, v_homo.T).T
    return v_transformed[:, :3].tolist()

def generate_render_frames(filepath, size=600, frames_count=60):
    """
    Main function: Reads a .blueprint and returns a list of PIL Images (frames).
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    objects = data.get("objects", [])
    blueprints = {b["id"]: b for b in data.get("blueprints", [])}
    meshes = {m["vuid"]: m for m in data.get("meshes", [])}
    obj_map = {obj["vuid"]: obj for obj in objects}
    global_transforms = {}

    def get_global_matrix(vuid):
        if vuid in global_transforms: return global_transforms[vuid]
        obj = obj_map.get(vuid)
        if not obj: return np.identity(4)
        
        tf = obj.get("transform", {})
        local = compose_matrix(tf.get("pos", [0,0,0]), tf.get("rot", [0,0,0]), tf.get("scale", [1,1,1]))
        
        parent_id = obj.get("pvuid", -1)
        if parent_id != -1 and parent_id in obj_map:
            glob = np.dot(get_global_matrix(parent_id), local)
        else:
            glob = local
            
        global_transforms[vuid] = glob
        return glob

    all_vertices = []
    all_faces = []
    vertex_offset = 0

    # 1. Geometry Extraction
    for obj in objects:
        bp_vuid = obj.get("structureBlueprintVuid", -1)
        if bp_vuid == -1: continue
        
        bp = blueprints.get(bp_vuid)
        if not bp: continue
        
        mesh_vuid = bp.get("blueprint", {}).get("bodyMeshVuid", -1)
        mesh = meshes.get(mesh_vuid)
        if not mesh: continue

        raw_verts = mesh["meshData"]["mesh"]["vertices"]
        raw_faces = mesh["meshData"]["mesh"]["faces"]
        local_verts = [raw_verts[i:i+3] for i in range(0, len(raw_verts), 3)]
        
        matrix = get_global_matrix(obj["vuid"])
        world_vertices = apply_transform(local_verts, matrix)
        
        all_vertices.extend(world_vertices)
        
        for f in raw_faces:
            new_indices = [idx + vertex_offset for idx in f["v"]]
            all_faces.append(new_indices)
            
        vertex_offset += len(world_vertices)

    # 2. Frame Generation
    pil_frames = []
    v_array = np.array(all_vertices)
    
    if len(v_array) == 0:
        return []

    for i in range(frames_count):
        rot_progress = i / frames_count
        rot_y = math.pi * 2 * rot_progress
        rot_x = math.radians(15)

        # Camera Matrix
        ry = np.array([[math.cos(rot_y), 0, math.sin(rot_y)], [0, 1, 0], [-math.sin(rot_y), 0, math.cos(rot_y)]])
        rx = np.array([[1, 0, 0], [0, math.cos(rot_x), -math.sin(rot_x)], [0, math.sin(rot_x), math.cos(rot_x)]])
        cam_matrix = np.dot(rx, ry)

        rotated_verts = np.dot(cam_matrix, v_array.T).T
        
        # Projection
        proj_x = rotated_verts[:, 0]
        proj_y = rotated_verts[:, 1]

        min_x, max_x = np.min(proj_x), np.max(proj_x)
        min_y, max_y = np.min(proj_y), np.max(proj_y)
        w, h = max_x - min_x, max_y - min_y
        
        if w == 0 or h == 0: continue
        
        padding = 50
        scale = min((size - 2*padding)/w, (size - 2*padding)/h)
        
        sx = (proj_x - min_x) * scale + (size - w*scale)/2
        sy = (proj_y - min_y) * scale + (size - h*scale)/2
        sy = size - sy # Flip Y

        img = np.zeros((size, size, 3), dtype=np.uint8)
        
        sx = sx.astype(int)
        sy = sy.astype(int)
        pts_cache = np.column_stack((sx, sy))

        for face in all_faces:
            pts = pts_cache[face]
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (100, 200, 255), 1)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_frames.append(Image.fromarray(img_rgb))

    return pil_frames
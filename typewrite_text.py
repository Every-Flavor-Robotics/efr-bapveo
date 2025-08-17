import bpy
import os
import sys
from bpy.app.handlers import persistent
from mathutils import Vector

# --- Configuration ---
IS_FAST_MODE = True # Set to True for faster rendering, False for detailed rendering
BLINK_SPEED_FRAMES = 10 # How many frames for each blink state (on or off)
PRE_ANIMATION_FRAMES = 24
POST_ANIMATION_FRAMES = 48
CURSOR_OFFSET_X = -.14  # Offset for the cursor position
CURSOR_OFFSET_Y = 0.29  # Offset for the cursor position
TEXT_MARGIN_FACTOR = 1.2  # How much extra space to leave around text (1.2 = 20% extra)

# --- Handler Function ---
@persistent
def typewriter_handler(scene, depsgraph):
    text_obj = None
    eval_text_obj = None
    for obj in scene.objects:
        if obj.type == 'FONT' and "full_text" in obj.data:
            text_obj = obj
            eval_text_obj = obj.evaluated_get(depsgraph)
            break
    if not text_obj:
        return

    # --- 1. Typewriter Text Logic ---
    full_text = text_obj.data["full_text"]
    chars_to_show = int(eval_text_obj.data["char_count"])
    visible_text = full_text[:chars_to_show]
    
    if text_obj.data.body != visible_text:
        text_obj.data.body = visible_text

    # --- 2. Cursor Logic (Blinking and Movement) ---
    cursor_obj = scene.objects.get("cursor")
    
    if cursor_obj:
        text_width = text_obj.dimensions.x
        
        # Get the cursor's own width from its bounding box
        cursor_width = cursor_obj.dimensions.x
        
        # Position the cursor at the end of the text, then shift it by half its own width.
        # This aligns the cursor's left edge with the end of the text.
        cursor_obj.location.x = text_obj.location.x + text_width + (cursor_width) + CURSOR_OFFSET_X
        cursor_obj.location.y = text_obj.location.y + CURSOR_OFFSET_Y
        
        # --- Cursor Blinking ---
        is_hidden = (scene.frame_current // BLINK_SPEED_FRAMES) % 2
        
        cursor_obj.hide_set(bool(is_hidden))
        cursor_obj.hide_render = bool(is_hidden)

def calculate_and_set_camera_position(text_object, cursor_object, camera_object, scene):
    """Use Blender's built-in camera framing functionality"""
    if not (text_object and camera_object):
        return
    
    # Temporarily set the text to full length to measure it
    original_text = text_object.data.body
    full_text = text_object.data["full_text"]
    text_object.data.body = full_text
    
    # Force update to get accurate dimensions
    scene.frame_set(scene.frame_current)
    bpy.context.view_layer.update()
    
    try:
        # Clear current selection and select objects to frame
        bpy.ops.object.select_all(action='DESELECT')
        text_object.select_set(True)
        if cursor_object:
            cursor_object.select_set(True)
        
        # Set text object as active
        bpy.context.view_layer.objects.active = text_object
        
        # Use Blender's built-in camera.view_selected operator
        # This is the same as "View > Frame Selected" in camera view
        bpy.context.view_layer.objects.active = camera_object
        
        # The key is to use the camera's view_selected operator
        bpy.ops.view3d.camera_to_view_selected()
        
        # Apply margin by moving camera back slightly
        import mathutils
        # Get camera's backward direction (positive local Z)
        camera_backward = camera_object.matrix_world.to_quaternion() @ mathutils.Vector((0.0, 0.0, 1.0))
        
        # Calculate margin distance based on object size
        object_size = max(text_object.dimensions.x, text_object.dimensions.y, text_object.dimensions.z)
        margin_distance = object_size * (TEXT_MARGIN_FACTOR - 1.0)
        
        # Move camera back for margin
        camera_object.location += camera_backward * margin_distance
    
    except Exception as e:
        print(f"Error using camera_to_view_selected: {e}")
        print("Falling back to manual calculation...")
        
        # Fallback: Use bounding box calculation
        # Get all vertices of the text object
        bbox = [text_object.matrix_world @ mathutils.Vector(corner) for corner in text_object.bound_box]
        if cursor_object:
            cursor_bbox = [cursor_object.matrix_world @ mathutils.Vector(corner) for corner in cursor_object.bound_box]
            bbox.extend(cursor_bbox)
        
        # Calculate bounding box center and size
        bbox_center = sum(bbox, mathutils.Vector()) / len(bbox)
        
        min_coords = mathutils.Vector([min(v[i] for v in bbox) for i in range(3)])
        max_coords = mathutils.Vector([max(v[i] for v in bbox) for i in range(3)])
        bbox_size = max_coords - min_coords
        
        # Position camera to look at center
        camera_object.location = bbox_center + mathutils.Vector((0, 0, max(bbox_size) * TEXT_MARGIN_FACTOR))
        
        # Point camera at the center
        direction = bbox_center - camera_object.location
        camera_object.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    finally:
        # Restore original text
        text_object.data.body = original_text
        
        # Clear selection
        bpy.ops.object.select_all(action='DESELECT')
    
    print(f"Camera positioned at: {camera_object.location}")
    print(f"Camera rotation: {camera_object.rotation_euler}")

# --- Main Script ---
# 1. Get the text string from the command line arguments
try:
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
    # Add a space at the end so the cursor can blink at the end:
    text_to_animate = argv[0] + " "
except IndexError:
    print("Error: Please provide a string of text to animate.")
    sys.exit(1)

# 2. Get the main objects from the scene
text_object = bpy.data.objects.get("Text")
if not text_object:
    print("Error: A text object named 'Text' was not found in the scene.")
    sys.exit(1)

cursor_object = bpy.data.objects.get("cursor")
if not cursor_object:
    print("Warning: An object named 'cursor' was not found. Skipping cursor animation.")

camera_object = bpy.data.objects.get("Camera")
if not camera_object:
    print("Warning: An object named 'Camera' was not found. Skipping camera positioning.")

print(f"Script found object: {text_object.name}")

# --- Remove any existing camera constraints to avoid conflicts ---
if camera_object:
    print("Removing existing camera constraints...")
    camera_object.constraints.clear()

# 3. Setup cursor and text initial state
if cursor_object:
    cursor_object.hide_set(False)
    cursor_object.hide_render = False
    cursor_object.location.y = text_object.location.y
    cursor_object.location.z = text_object.location.z

text_object.data["full_text"] = text_to_animate
text_object.data.body = ""

# 4. Calculate and set optimal camera position BEFORE animation starts
print("Calculating optimal camera position...")
calculate_and_set_camera_position(text_object, cursor_object, camera_object, bpy.context.scene)

# 5. Animate the text with padding
full_text_length = len(text_to_animate)
typing_speed_factor = 3
animation_start_frame = 1 + PRE_ANIMATION_FRAMES
typing_duration_frames = full_text_length * typing_speed_factor

if typing_duration_frames < 1:
    typing_duration_frames = 1

animation_end_frame = animation_start_frame + typing_duration_frames

bpy.context.scene.frame_current = animation_start_frame
text_object.data["char_count"] = 0
text_object.data.keyframe_insert(data_path='["char_count"]', frame=animation_start_frame)

bpy.context.scene.frame_current = animation_end_frame
text_object.data["char_count"] = full_text_length
text_object.data.keyframe_insert(data_path='["char_count"]', frame=animation_end_frame)

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = animation_end_frame + POST_ANIMATION_FRAMES

# 6. Register the handler function
bpy.app.handlers.frame_change_post.clear()
bpy.app.handlers.frame_change_post.append(typewriter_handler)

# --- Configure Render Settings ---
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'

# Set render quality based on the flag at the top of the file
if IS_FAST_MODE:
    print("--- Running in FAST TEST mode ---")
    bpy.context.scene.eevee.taa_render_samples = 8
    bpy.context.scene.render.resolution_percentage = 50
else:
    print("--- Running in HIGH QUALITY mode ---")
    bpy.context.scene.eevee.taa_render_samples = 128 # A good default for quality
    bpy.context.scene.render.resolution_percentage = 100

bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'
bpy.context.scene.render.ffmpeg.video_bitrate = 10000

output_dir = "renders"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

safe_filename = text_to_animate.replace(" ", "_").replace(":", "").replace("/", "")[:50]
bpy.context.scene.render.filepath = os.path.abspath(f"./{output_dir}/{safe_filename}.mp4")

# --- Render the animation ---
print(f"Rendering text animation for: '{text_to_animate}'...")
bpy.ops.render.render(animation=True)
print("Rendering complete.")

# --- Cleanup and Exit ---
bpy.app.handlers.frame_change_post.remove(typewriter_handler)
bpy.ops.wm.quit_blender()
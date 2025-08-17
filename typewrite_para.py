def calculate_cursor_position(text_obj, current_text):
    """Calculate the cursor position for multi-line text"""
    if not current_text:
        return text_obj.location.x, text_obj.location.y
    
    # Split text into lines
    lines = current_text.split('\n')
    
    # Get text object properties
    font_data = text_obj.data
    
    # Store original text to restore later
    original_text = font_data.body
    
    # Calculate line height - this is approximate since Blender doesn't expose exact line metrics
    # We'll use the text object's dimensions and estimate
    if len(lines) > 1:
        # Create temporary text to measure single line height
        font_data.body = "Ag"  # Use characters with ascenders and descenders
        bpy.context.view_layer.update()
        single_line_height = text_obj.dimensions.y
        
        line_height = single_line_height * font_data.space_line
    else:
        line_height = 0
    
    # Find which line the cursor should be on
    current_line_index = len(lines) - 1
    current_line_text = lines[-1]  # Last line (# Standard library imports - always available
import os
import sys
import subprocess
import multiprocessing
from pathlib import Path
import time

# Try to import Blender-specific modules
try:
    import bpy
    from bpy.app.handlers import persistent
    from mathutils import Vector
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False
    bpy = None
    persistent = lambda f: f  # Dummy decorator
    Vector = None

# --- Configuration ---
IS_FAST_MODE = True # Set to True for faster rendering, False for detailed rendering
BLINK_SPEED_FRAMES = 10 # How many frames for each blink state (on or off)
PRE_ANIMATION_FRAMES = 24
POST_ANIMATION_FRAMES = 48
CURSOR_OFFSET_X = -.14  # Offset for the cursor position
CURSOR_OFFSET_Y = 0.29  # Offset for the cursor position
TEXT_MARGIN_FACTOR = 1.2  # How much extra space to leave around text (1.2 = 20% extra)
PARALLEL_FRAME_THRESHOLD = 30  # If total frames exceed this, use parallel rendering
MAX_PARALLEL_PROCESSES = 4  # Maximum number of parallel Blender instances

# --- Handler Function ---
@persistent
def typewriter_handler(scene, depsgraph):
    text_obj = None
    eval_text_obj = None
    for obj in scene.objects:
        if obj.type == 'FONT' and "full_text" in obj.data:
            text_obj = obj
            # CRITICAL FIX: Get the evaluated version for animated properties
            eval_text_obj = obj.evaluated_get(depsgraph)
            break
    if not text_obj:
        return

    # --- 1. Typewriter Text Logic ---
    full_text = text_obj.data["full_text"]
    
    # CRITICAL FIX: Get char_count from the EVALUATED object, not the original
    if "char_count" in eval_text_obj.data:
        chars_to_show = int(eval_text_obj.data["char_count"])
    else:
        print(f"Warning: char_count property not found on frame {scene.frame_current}")
        chars_to_show = 0
    
    # Clamp chars_to_show to valid range
    chars_to_show = max(0, min(chars_to_show, len(full_text)))
    
    visible_text = full_text[:chars_to_show]
    
    # Debug output every 30 frames
    if scene.frame_current % 30 == 0:
        print(f"Frame {scene.frame_current}: showing {chars_to_show}/{len(full_text)} chars")
    
    if text_obj.data.body != visible_text:
        text_obj.data.body = visible_text

    # --- 2. Cursor Logic (Blinking and Movement) ---
    cursor_obj = scene.objects.get("cursor")
    
    if cursor_obj:
        # Calculate cursor position based on current text
        cursor_x, cursor_y = calculate_cursor_position(text_obj, visible_text)
        
        # Get the cursor's own width from its bounding box
        cursor_width = cursor_obj.dimensions.x
        
        # Position the cursor
        cursor_obj.location.x = cursor_x + cursor_width + CURSOR_OFFSET_X
        cursor_obj.location.y = cursor_y + CURSOR_OFFSET_Y
        
        # --- Cursor Blinking ---
        is_hidden = (scene.frame_current // BLINK_SPEED_FRAMES) % 2
        
        cursor_obj.hide_set(bool(is_hidden))
        cursor_obj.hide_render = bool(is_hidden)

def calculate_cursor_position(text_obj, current_text):
    """Calculate the cursor position for multi-line text"""
    if not current_text:
        return text_obj.location.x, text_obj.location.y
    
    # Split text into lines
    lines = current_text.split('\n')
    
    # Get text object properties
    font_data = text_obj.data
    
    # Use the actual dimensions of the currently visible text
    # Since text_obj.data.body already contains the visible text,
    # we can use its dimensions directly
    full_width = text_obj.dimensions.x
    full_height = text_obj.dimensions.y
    
    # For multi-line text, we need to figure out where the cursor should be
    current_line_index = len(lines) - 1
    current_line_text = lines[-1]  # Last line (where cursor is)
    
    # Estimate line height based on font settings
    line_height = font_data.size * font_data.space_line
    
    # Calculate Y position (line number * line height, going downward)
    cursor_y = text_obj.location.y - (current_line_index * line_height)
    
    # For X position, we need to estimate the width of the last line
    # If it's the only line, use the full width
    if len(lines) == 1:
        cursor_x = text_obj.location.x + full_width
    else:
        # For multi-line text, estimate based on character proportion
        # Get the proportion of characters on the last line vs total
        total_chars = len(current_text.replace('\n', ''))
        last_line_chars = len(current_line_text)
        
        if total_chars > 0:
            # Rough estimate: assume uniform character distribution
            estimated_width = (last_line_chars / total_chars) * full_width * len(lines)
            cursor_x = text_obj.location.x + estimated_width
        else:
            cursor_x = text_obj.location.x
    
    return cursor_x, cursor_y

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
    
    # For multi-line text, we need to ensure proper text formatting
    lines = full_text.split('\n')
    print(f"Text has {len(lines)} lines")
    
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
        # For multi-line text, consider both width and height
        object_size = max(text_object.dimensions.x, text_object.dimensions.y, text_object.dimensions.z)
        margin_distance = object_size * (TEXT_MARGIN_FACTOR - 1.0)
        
        # For multi-line text, add extra margin
        if len(lines) > 1:
            margin_distance *= 1.2  # 20% extra margin for multi-line
        
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
        camera_distance = max(bbox_size) * TEXT_MARGIN_FACTOR
        if len(lines) > 1:
            camera_distance *= 1.2  # Extra distance for multi-line
        
        camera_object.location = bbox_center + mathutils.Vector((0, 0, camera_distance))
        
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
    print(f"Text dimensions: {text_object.dimensions.x:.2f} x {text_object.dimensions.y:.2f} x {text_object.dimensions.z:.2f}")

# --- Main Script ---
# Only execute if we're in Blender
if IN_BLENDER:
    # Check if we're in a subprocess for chunk rendering
    is_chunk_render = "--chunk-render" in sys.argv
    chunk_start_frame = None
    chunk_end_frame = None
    chunk_id = None
    chunk_safe_filename = None

    if is_chunk_render:
        try:
            chunk_idx = sys.argv.index("--chunk-render")
            chunk_start_frame = int(sys.argv[chunk_idx + 1])
            chunk_end_frame = int(sys.argv[chunk_idx + 2])
            chunk_id = int(sys.argv[chunk_idx + 3])
            chunk_safe_filename = sys.argv[chunk_idx + 4]  # Get the safe filename from parent
            print(f"CHUNK RENDER MODE: Frames {chunk_start_frame}-{chunk_end_frame} (Chunk {chunk_id})")
        except (IndexError, ValueError):
            print("Error: Invalid chunk render arguments")
            sys.exit(1)

    # 1. Get the text string from the command line arguments
    try:
        argv = sys.argv
        argv = argv[argv.index("--") + 1:]
        
        # If we're in chunk render mode, stop before the --chunk-render flag
        if "--chunk-render" in argv:
            chunk_index = argv.index("--chunk-render")
            argv = argv[:chunk_index]  # Only take arguments before --chunk-render
        
        # Handle multiple arguments as separate lines or single argument with \n
        if len(argv) == 1:
            # Single argument - check if it contains \n for line breaks
            text_to_animate = argv[0]
            if "\\n" in text_to_animate:
                # Replace literal \n with actual newlines
                text_to_animate = text_to_animate.replace("\\n", "\n")
        else:
            # Multiple arguments - join with newlines
            text_to_animate = "\n".join(argv)
        
        # Add a space at the end so the cursor can blink at the end
        text_to_animate += " "
        
    except IndexError:
        print("Error: Please provide text to animate.")
        print("Usage examples:")
        print('  blender scene.blend --python script.py -- "Single line text"')
        print('  blender scene.blend --python script.py -- "First line\\nSecond line"')
        print('  blender scene.blend --python script.py -- "Line 1" "Line 2" "Line 3"')
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
    output_path = os.path.abspath(output_dir)

    # Create output directory if it doesn't exist
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"Created output directory: {output_path}")
    except Exception as e:
        print(f"Warning: Could not create output directory {output_path}: {e}")
        # Fallback to current directory
        output_path = os.path.abspath(".")
        print(f"Using current directory: {output_path}")

    # Create safe filename
    safe_filename = text_to_animate.replace(" ", "_").replace(":", "").replace("/", "").replace("\n", "_")[:50]

    # Determine if we should use parallel rendering
    total_frames = animation_end_frame + POST_ANIMATION_FRAMES
    use_parallel = total_frames > PARALLEL_FRAME_THRESHOLD and not is_chunk_render

    if use_parallel:
        print(f"\n=== PARALLEL RENDERING MODE ===")
        print(f"Total frames ({total_frames}) exceeds threshold ({PARALLEL_FRAME_THRESHOLD})")
        print(f"Splitting into multiple chunks for parallel rendering...")
        
        # Calculate chunk size and number of processes
        num_processes = min(MAX_PARALLEL_PROCESSES, multiprocessing.cpu_count())
        frames_per_chunk = total_frames // num_processes
        
        # Create temp directory for image sequences
        temp_dir = os.path.join(output_path, f"temp_{safe_filename}")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Prepare chunk ranges
        chunks = []
        for i in range(num_processes):
            start = 1 + (i * frames_per_chunk)
            if i == num_processes - 1:
                # Last chunk gets any remaining frames
                end = total_frames
            else:
                end = start + frames_per_chunk - 1
            chunks.append((start, end, i))
        
        print(f"Launching {num_processes} parallel Blender instances...")
        for start, end, chunk_id in chunks:
            print(f"  Chunk {chunk_id}: Frames {start}-{end}")
        
        # Launch parallel Blender processes
        processes = []
        for start, end, chunk_id in chunks:
            # Build command for subprocess
            blend_file = bpy.data.filepath
            script_file = os.path.abspath(__file__)
            
            cmd = [
                bpy.app.binary_path,  # Blender executable
                blend_file,
                "--background",
                "--python", script_file,
                "--",
                text_to_animate[:-1],  # Remove the trailing space we added
                "--chunk-render", str(start), str(end), str(chunk_id), safe_filename  # Pass safe filename
            ]
            
            print(f"Starting chunk {chunk_id}...")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append((process, chunk_id))
        
        # Wait for all processes to complete
        print("\nRendering chunks in parallel...")
        for process, chunk_id in processes:
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print(f"ERROR in chunk {chunk_id}:")
                print(stderr.decode())
            else:
                print(f"Chunk {chunk_id} completed successfully")
        
        # Combine image sequences with ffmpeg
        print("\nCombining chunks into final video...")
        output_file = os.path.join(output_path, f"{safe_filename}.mp4")
        
        # Create a list file for ffmpeg concat
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for _, _, chunk_id in chunks:
                chunk_video = os.path.join(temp_dir, f"chunk_{chunk_id}.mp4")
                f.write(f"file '{chunk_video}'\n")
        
        # Use ffmpeg to concatenate
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            "-y",  # Overwrite output
            output_file
        ]
        
        try:
            result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
            print(f"Successfully created: {output_file}")
            
            # Clean up temp files
            import shutil
            shutil.rmtree(temp_dir)
            print("Cleaned up temporary files")
            
        except subprocess.CalledProcessError as e:
            print(f"Error combining videos with ffmpeg: {e}")
            print(f"ffmpeg output: {e.stderr}")
            print(f"Chunk videos are preserved in: {temp_dir}")
        except FileNotFoundError:
            print("ERROR: ffmpeg not found. Please install ffmpeg to combine video chunks.")
            print(f"Individual chunks are saved in: {temp_dir}")
        
        # Exit after coordinating parallel render
        print("\n=== PARALLEL RENDERING COMPLETE ===")
        bpy.ops.wm.quit_blender()
        
    elif is_chunk_render:
        # We're rendering a specific chunk - use the safe filename passed from parent
        output_file = os.path.join(output_path, f"temp_{chunk_safe_filename}", f"chunk_{chunk_id}.mp4")
        
        # Ensure temp directory exists
        temp_dir = os.path.dirname(output_file)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        print(f"Chunk output file: {output_file}")
        bpy.context.scene.render.filepath = output_file
        
        # Set frame range for this chunk
        bpy.context.scene.frame_start = chunk_start_frame
        bpy.context.scene.frame_end = chunk_end_frame
        
        # --- Render the chunk ---
        print(f"Rendering chunk {chunk_id}: frames {chunk_start_frame}-{chunk_end_frame}...")
        bpy.ops.render.render(animation=True)
        print(f"Chunk {chunk_id} rendering complete.")
        
    else:
        # Normal single-process rendering
        output_file = os.path.join(output_path, f"{safe_filename}.mp4")
        print(f"Output file will be: {output_file}")
        bpy.context.scene.render.filepath = output_file
        
        # --- Render the animation ---
        print(f"Rendering text animation for: '{text_to_animate}'...")
        bpy.ops.render.render(animation=True)
        print("Rendering complete.")

    # --- Cleanup and Exit ---
    bpy.app.handlers.frame_change_post.remove(typewriter_handler)
    bpy.ops.wm.quit_blender()
import bpy
import os
import sys

# Get the path to the STL file from the command line arguments
# The script expects the file path to be the first argument after '--'
try:
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]  # get all args after "--"
    stl_filepath = argv[0]
except IndexError:
    print("Error: Please provide a path to an STL file.")
    sys.exit(1)

# Get the name of the STL file without the extension
stl_name = os.path.splitext(os.path.basename(stl_filepath))[0]

# --- Import and Scale the STL ---
print(f"Importing {stl_name}...")
bpy.ops.wm.stl_import(filepath=stl_filepath)

# Assuming the imported object is the only new mesh object
imported_object = bpy.context.selected_objects[0]

# Set the origin to the center of mass
bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

# Scale the object to fit a specific bounding box (e.g., a 2x2x2 unit box)
target_size = 2.0
max_dim = max(imported_object.dimensions)
if max_dim > 0:
    scale_factor = target_size / max_dim
    imported_object.scale = (scale_factor, scale_factor, scale_factor)

# Set the object's location to the origin
imported_object.location = (0, 0, 0)


# --- Configure Render Settings ---
# You can set these in your template file, but it's good to be explicit here
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'
bpy.context.scene.render.ffmpeg.video_bitrate = 10000

# Set the output path
output_dir = "renders"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
bpy.context.scene.render.filepath = os.path.abspath(f"./{output_dir}/{stl_name}.mp4")

# Set the frame range
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 240

# --- Render the animation ---
print(f"Rendering animation for {stl_name}...")
bpy.ops.render.render(animation=True)
print("Rendering complete.")

# To prevent the script from saving the file, you can add this line at the end
# to exit Blender without saving changes to the template.blend file.
bpy.ops.wm.quit_blender()
import pathlib

# Replace with your actual directory path (e.g., './my_folder')
directory_path = "C:/wamp64/technica_26/game_control_server/assets/Sprites"

# Loop through all items in the directory
for path in pathlib.Path(directory_path).iterdir():
    # Only rename files (skip folders)
    if path.is_file():
        print(path)
        new_path = path.with_name(path.name.lower())
        path.rename(new_path)

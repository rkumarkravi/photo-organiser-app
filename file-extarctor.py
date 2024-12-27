import shutil
import os

def copy_files_to_folder(input_file, destination_folder):
    # Read the file paths from the input file
    with open(input_file, "r") as f:
        file_paths = f.read().splitlines()  # Split the file paths by newline

    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    # Copy each file to the destination folder
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                # Determine which subfolder to use
                if "Day 1" in file_path:
                    subfolder = os.path.join(destination_folder, "Day 1")
                elif "Day 2" in file_path:
                    subfolder = os.path.join(destination_folder, "Day 2")
                elif "Day 3" in file_path:
                    subfolder = os.path.join(destination_folder, "Day 3")
                elif "Day 4" in file_path:
                    subfolder = os.path.join(destination_folder, "Day 4")
                else:
                    subfolder = os.path.join(destination_folder, "Others")  # Default subfolder

                # Ensure the subfolder exists
                os.makedirs(subfolder, exist_ok=True)

                # Get the file name and create the destination path
                base_name = os.path.basename(file_path)
                dest_path = os.path.join(subfolder, base_name)

                # Handle duplicate files by renaming (if necessary)
                if os.path.exists(dest_path):
                    file_name, file_ext = os.path.splitext(base_name)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(
                            subfolder, f"{file_name}_{counter}{file_ext}"
                        )
                        counter += 1

                # Copy the file to the destination path
                shutil.copy(file_path, dest_path)
                print(f"Copied: {file_path} -> {dest_path}")
            except Exception as e:
                print(f"Failed to copy {file_path}: {e}")
        else:
            print(f"File not found: {file_path}")

# Example usage
input_file = "D:\weeding-all-details\wedding pics selective\photofordrive.txt"  # Replace with your file containing the paths
destination_folder = "D:\weeding-all-details\wedding pics selective\photofordrive"  # Replace with your destination folder path

copy_files_to_folder(input_file, destination_folder)
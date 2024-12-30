import os
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pathlib
import threading
from datetime import datetime
import shutil

class PhotoOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Organizer")
        self.isFullScreen = True
        self.addedCount=0
        self.autoSaveAllowed=False
        self.running = True

        # Enable fullscreen mode
        self.root.attributes('-fullscreen', self.isFullScreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<F11>", self.toggle_fullscreen)
        
        # Override close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Bind the Left Arrow key to the previous_action function
        self.root.bind("<Left>", self.previous_image)
        # Bind the Right Arrow key to the next_action function
        self.root.bind("<Right>", self.next_image)
        self.root.bind("l", self.add_to_list)  # For lowercase "l"
        self.root.bind("L", self.add_to_list)  # For uppercase "L"
        self.root.bind("r", self.remove_from_list)  # For lowercase "l"
        self.root.bind("R", self.remove_from_list)  # For uppercase "L"
        self.root.bind(",", self.rotate_left)  # For uppercase ","
        self.root.bind(".", self.rotate_right)  # For uppercase "."

        self.folders = []  # List to store folders
        self.image_paths = []  # All image paths from the folders
        self.current_image_index = 0  # Index of the currently displayed image

        # Manage multiple lists of selected images
        self.image_lists = {"Default": []}  # A dictionary to hold lists of selected images
        self.current_list = "Default"  # The current active list
        self.fullScreenBtnText = "Exit Fullscreen"

        # State for zoom and rotation
        self.rotation_angle = 0  # Rotation angle in degrees
        self.zoom_level = 1  # Zoom level (1 = no zoom)
        
        # Define the path for the photo-organiser folder in Documents
        self.documents_folder = os.path.join(pathlib.Path.home(), "Documents", "photo-organiser")

        # Ensure the photo-organiser folder exists
        if not os.path.exists(self.documents_folder):
            os.makedirs(self.documents_folder)        
        
        # Load existing lists from the folder
        self.load_existing_lists()

        # Toolbar at the top
        self.toolbar = tk.Frame(root, bg="gray")
        self.toolbar.pack(side="top", fill="x")

       # Create the main menu
        self.menu_bar = tk.Menu(self.root)

        # Add "File" menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Add Images Folder", command=self.add_folder)
        file_menu.add_command(label="Export List", command=self.export_list_to_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)  # Add an exit option
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Add "Navigation" menu
        navigation_menu = tk.Menu(self.menu_bar, tearoff=0)
        navigation_menu.add_command(label="Previous Image", command=self.previous_image)
        navigation_menu.add_command(label="Next Image", command=self.next_image)
        self.menu_bar.add_cascade(label="Navigation", menu=navigation_menu)
        
        # Add "Image" menu
        image_menu = tk.Menu(self.menu_bar, tearoff=0)
        image_menu.add_command(label="Rotate Left :<", command=self.rotate_left)
        image_menu.add_command(label="Rotate Right :>", command=self.rotate_right)
        self.menu_bar.add_cascade(label="Image", menu=image_menu)

        # Add "List" menu
        list_menu = tk.Menu(self.menu_bar, tearoff=0)
        list_menu.add_command(label="Add to List (L)", command=self.add_to_list)
        list_menu.add_command(label="Remove from List (R)", command=self.remove_from_list)
        list_menu.add_command(label="Create New List", command=self.create_new_list)
        self.menu_bar.add_cascade(label="List", menu=list_menu)

        # Add "Options" menu
        options_menu = tk.Menu(self.menu_bar, tearoff=0)
        options_menu.add_command(label="Start/Stop Auto Save", command=self.start_auto_save)
        self.menu_bar.add_cascade(label="Options", menu=options_menu)

        # Add "Help" menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Photo Organizer App v1.0\nDeveloped by Ravi Kumar"))
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Configure the menu bar
        self.root.config(menu=self.menu_bar)

        # Dropdown for selecting lists
        self.list_label = tk.Label(self.toolbar, text="Custom List:", fg="blue", bg="gray")
        self.list_label.pack(side="left", padx=5)
        self.list_var = tk.StringVar(value=self.current_list)
        self.list_dropdown = ttk.Combobox(self.toolbar, textvariable=self.list_var, state="readonly")
        self.list_dropdown['values'] = list(self.image_lists.keys())
        self.list_dropdown.pack(side="left", padx=10, pady=10)
        self.list_dropdown.bind("<<ComboboxSelected>>", self.change_list)
        
        # Set the first list as the selected list (or None if no list exists)
        if self.image_lists:
            self.current_list = list(self.image_lists.keys())[0]
            self.list_var.set(self.current_list)  # Set default selected list
        else:
            self.list_var.set("No Lists")

        self.status_label = tk.Label(self.toolbar, text="No image loaded", fg="blue", bg="gray")
        self.status_label.pack(side="left", padx=5)
        
        self.added_label = tk.Label(self.toolbar, text=f"{self.current_list} : 0", fg="blue", bg="gray")
        self.added_label.pack(side="left", padx=5)
        
        self.auto_save_label = tk.Label(self.toolbar, text=f"AS: {self.autoSaveAllowed}", fg="blue", bg="gray")
        self.auto_save_label.pack(side="left", padx=5)

        # Image display area
        self.main_frame = tk.Frame(root, bg="black")
        self.main_frame.pack(expand=True, fill="both")

        self.image_label = tk.Label(self.main_frame, bg="black")
        self.image_label.pack(expand=True, fill="both")
        
        #schedule for auto save
        self.save_data_auto()

    def export_list_to_folder(self, event=None):
        """Export the list of files to the selected folder."""
        input_file = os.path.join(self.documents_folder, f"{self.current_list}.txt")

        # Check if the user selected a file
        if not os.path.exists(input_file):
            print("Input file not found. Exiting.")
            return

        # Prompt the user to select the destination folder
        destination_folder = filedialog.askdirectory(title="Select the Destination Folder")

        # Check if the user selected a folder
        if not destination_folder:
            print("No destination folder selected. Exiting.")
            return

        # Create a progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Copying Files")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)  # Makes the progress window appear above the main window
        progress_window.grab_set()  # Focus on this window

        progress_label = tk.Label(progress_window, text="Copying files...", font=("Arial", 12))
        progress_label.pack(pady=10)

        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(pady=10)

        copied_count = tk.StringVar(value="0/0")
        count_label = tk.Label(progress_window, textvariable=copied_count, font=("Arial", 10))
        count_label.pack()

        # Start copying files in a separate thread
        self.copy_files_to_folder(input_file, destination_folder, progress_bar,progress_label, copied_count, progress_window)


    def copy_files_to_folder(self, input_file, destination_folder, progress_bar,progress_label, copied_count, progress_window):
        """Copy files listed in the input file to the destination folder."""
        try:
            # Read the file paths from the input file
            with open(input_file, "r") as f:
                file_paths = f.read().splitlines()

            # Total number of files to copy
            total_files = len(file_paths)
            progress_bar["maximum"] = total_files

            # Ensure the destination folder exists
            os.makedirs(destination_folder, exist_ok=True)

            # Copy each file to the destination folder
            for i, file_path in enumerate(file_paths):
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

                # Update progress bar and count
                progress_bar["value"] = i + 1
                copied_count.set(f"Copied {i + 1}/{total_files}")
                progress_window.update_idletasks()  # Force UI update

            # Update the label once all files are copied
            copied_count.set(f"Completed: {total_files}/{total_files}")
            progress_label.config(text="Copying completed successfully!")
        except Exception as e:
            print(f"Error during file copying: {e}")
            progress_label.config(text="Error occurred during copying!")
        finally:
            # Allow the user to close the progress window
            progress_window.grab_release()
            #progress_window.destroy()

    def load_existing_lists(self):
        """Load all existing lists from the photo-organiser folder."""
        for file_name in os.listdir(self.documents_folder):
            if file_name.endswith(".txt"):
                list_name = file_name[:-4]  # Remove the ".txt" extension
                list_path = os.path.join(self.documents_folder, file_name)
                with open(list_path, "r") as file:
                    self.image_lists[list_name] = [line.strip() for line in file.readlines()]

    def start_auto_save(self):
        self.autoSaveAllowed=not self.autoSaveAllowed
        self.auto_save_label.config(text=f"AS: {self.autoSaveAllowed}")
    
    def save_data_auto(self):
        if self.running:  # Check if the app is still running
            if self.autoSaveAllowed and self.image_lists[self.current_list]:
                self.export_list()
                print("Data saved!")
                current_time = datetime.now().strftime("%H:%M:%S")
                self.auto_save_label.config(text=f"AS: {self.autoSaveAllowed} | {current_time}")
            threading.Timer(5, self.save_data_auto).start()
            
    def on_exit(self):
        """Handle cleanup when exiting the application."""
        self.running = False  # Stop the auto-save thread
        self.autoSaveAllowed = False
        self.root.destroy()  # Destroy the Tkinter window

    def add_folder(self):
        """Allow the user to select a folder and add its images."""
        folder = filedialog.askdirectory()
        if folder:
            self.folders.append(folder)
            self.load_images_from_folders()

    def load_images_from_folders(self):
        """Load all image paths from the selected folders."""
        self.image_paths = []
        for folder in self.folders:
            for file in os.listdir(folder):
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                    self.image_paths.append(os.path.join(folder, file))
        self.current_image_index = 0
        if self.image_paths:
            self.show_image()
        else:
            self.status_label.config(text="No images found in the selected folders.")

    def show_image(self):
        """Display the current image."""
        if self.image_paths:
            image_path = self.image_paths[self.current_image_index]
            image = Image.open(image_path)

            # Apply zoom
            width, height = image.size
            new_size = (int(width * self.zoom_level), int(height * self.zoom_level))
            image = image.resize(new_size)

            # Apply rotation
            image = image.rotate(self.rotation_angle)

            image.thumbnail((self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
            photo = ImageTk.PhotoImage(image)

            self.image_label.config(image=photo, bg="black")
            self.image_label.image = photo
            self.status_label.config(
                text=f"Viewing {self.current_image_index + 1}/{len(self.image_paths)}: {os.path.basename(image_path)}"
            )
        else:
            self.image_label.config(image=None, bg="black")
            self.image_label.image = None
            self.status_label.config(text="No image to display.")

    def previous_image(self, event=None):
        """Show the previous image."""
        if self.image_paths:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
            self.rotation_angle = 0
            self.show_image()

    def next_image(self, event=None):
        """Show the next image."""
        if self.image_paths:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            self.rotation_angle = 0
            self.show_image()

    def add_to_list(self, event=None):
        """Add the currently displayed image to the selected list."""
        if self.image_paths:
            current_image = self.image_paths[self.current_image_index]
            if current_image not in self.image_lists[self.current_list]:
                self.image_lists[self.current_list].append(current_image)
                self.addedCount+=1
                self.added_label.config(text=f"'{self.current_list}' : {self.addedCount}")
                #messagebox.showinfo("Added", f"Added {os.path.basename(current_image)} to list '{self.current_list}'.")
                print("Added", f"Added {os.path.basename(current_image)} to list '{self.current_list}'.")
            else:
                messagebox.showwarning("Duplicate Entry", "This image is already in the list.")

    def create_new_list(self):
        """Create a new list for selected images."""
        new_list_name = simpledialog.askstring("New List", "Enter the name of the new list:")
        if new_list_name:
            new_list_path = os.path.join(self.documents_folder, f"{new_list_name}.txt")
            if os.path.exists(new_list_path):
                messagebox.showwarning("Warning", "A list with this name already exists.")
            else:
                # Create the new list file
                open(new_list_path, "w").close()
                # Add the new list to the dropdown options
                self.image_lists[new_list_name] = []
                #self.list_dropdown["menu"].add_command(
                #    label=new_list_name, command=lambda: self.select_list(new_list_name)
                #)
                self.list_dropdown['values'] = list(self.image_lists.keys())
                self.list_var.set(new_list_name)
                self.current_list=new_list_name
                messagebox.showinfo("Success", f"New list '{new_list_name}' created.")

    def change_list(self, event):
        """Change the current list."""
        self.current_list = self.list_var.get()
        self.addedCount=self.count_lines_in_file()
        self.added_label.config(text=f" '{self.current_list}' : {self.addedCount}")

    def export_list(self):
        """Export the selected images to a text file."""
        if self.image_lists[self.current_list]:
            #file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            file_path = os.path.join(self.documents_folder, f"{self.current_list}.txt")
            if file_path:
                with open(file_path, "w") as file:
                    for image_path in self.image_lists[self.current_list]:
                        file.write(image_path + "\n")
                #messagebox.showinfo("Export Successful", f"List '{self.current_list}' exported to {file_path}.")
        else:
            messagebox.showwarning("No Images", f"No images in the list '{self.current_list}' to export.")

    def count_lines_in_file(self):
        try:
            file_path = os.path.join(self.documents_folder, f"{self.current_list}.txt")
            with open(file_path, 'r') as file:
                lines = file.readlines()
                return len(lines)
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
            return 0
        except Exception as e:
            print(f"An error occurred: {e}")
            return 0

    def rotate_left(self, event=None):
        """Rotate the image left by 90 degrees."""
        self.rotation_angle -= 90
        self.show_image()

    def rotate_right(self, event=None):
        """Rotate the image right by 90 degrees."""
        self.rotation_angle += 90
        self.show_image()

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode when the Escape key is pressed."""
        root.attributes('-fullscreen', False)

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode."""
        is_fullscreen = root.attributes('-fullscreen')  # Check if fullscreen is enabled
        root.attributes('-fullscreen', not is_fullscreen)  # Toggle fullscreen state
        
    def remove_from_list(self, event=None):
        """Remove the currently displayed image from the selected list."""
        if self.image_paths:
            current_image = self.image_paths[self.current_image_index]
            if current_image in self.image_lists[self.current_list]:
                self.image_lists[self.current_list].remove(current_image)
                self.addedCount -= 1
                self.added_label.config(text=f"'{self.current_list}' : {self.addedCount}")
                self.export_list()  # Save the updated list to the file
                messagebox.showinfo("Removed", f"Removed {os.path.basename(current_image)} from list '{self.current_list}'.")
                print(f"Removed {os.path.basename(current_image)} from list '{self.current_list}'.")
            else:
                messagebox.showwarning("Not Found", "This image is not in the list.")



if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoOrganizerApp(root)
    root.mainloop()

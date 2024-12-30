import os
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pathlib
import threading
from datetime import datetime

class PhotoOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Organizer")
        self.isFullScreen = True
        self.addedCount=0
        self.autoSaveAllowed=False

        # Enable fullscreen mode
        self.root.attributes('-fullscreen', self.isFullScreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<F11>", self.toggle_fullscreen)

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
        
        self.selected_images_file = os.path.join(self.documents_folder, "selected_images.txt")
        
        
        # Load existing lists from the folder
        self.load_existing_lists()

        # Toolbar at the top
        self.toolbar = tk.Frame(root, bg="gray")
        self.toolbar.pack(side="top", fill="x")

        
        tk.Button(self.toolbar, text="Add Folder", command=self.add_folder).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Previous", command=self.previous_image).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Next", command=self.next_image).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Add to List : L", command=self.add_to_list).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Remove from List : R", command=self.remove_from_list).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Export List", command=self.export_list).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Auto Save", command=self.start_auto_save).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="New List", command=self.create_new_list).pack(side="left", padx=10, pady=10)

        # Dropdown for selecting lists
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

        # Rotate buttons
        tk.Button(self.toolbar, text="Rotate Left :<", command=self.rotate_left).pack(side="left", padx=5, pady=10)
        tk.Button(self.toolbar, text="Rotate Right :>", command=self.rotate_right).pack(side="left", padx=5, pady=10)

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
        if self.autoSaveAllowed and self.image_lists[self.current_list]:
            self.export_list()
            print("Data saved!")
            current_time = datetime.now().strftime("%H:%M:%S")
            self.auto_save_label.config(text=f"AS: {self.autoSaveAllowed} | {current_time}")
        threading.Timer(5, self.save_data_auto).start()

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
            messagebox.showwarning("No Images ", f"No images in the list '{self.current_list}' to export.")

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

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pathlib

class PhotoOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Organizer")
        self.isFullScreen = True

        # Enable fullscreen mode
        self.root.attributes('-fullscreen', self.isFullScreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<F11>", self.toggle_fullscreen)
        
        # Bind the Left Arrow key to the previous_action function
        self.root.bind("<Left>", self.previous_image)
        # Bind the Right Arrow key to the next_action function
        self.root.bind("<Right>", self.next_image)

        self.folders = []  # List to store folders
        self.image_paths = []  # All image paths from the folders
        self.current_image_index = 0  # Index of the currently displayed image
        self.selected_images = []  # List of selected images
        self.fullScreenBtnText = "Exit Fullscreen"

        # State for zoom and rotation
        self.rotation_angle = 0  # Rotation angle in degrees
        self.zoom_level = 1  # Zoom level (1 = no zoom)

        # Define the path for the selected images file in Documents folder
        self.documents_folder = os.path.join(pathlib.Path.home(), "Documents")
        self.selected_images_file = os.path.join(self.documents_folder, "selected_images.txt")

        # Ensure the selected images file exists
        if not os.path.exists(self.documents_folder):
            os.makedirs(self.documents_folder)
        if not os.path.exists(self.selected_images_file):
            open(self.selected_images_file, "w").close()

        # Load previously selected images
        self.load_selected_images()

        # Toolbar at the top
        self.toolbar = tk.Frame(root, bg="gray")
        self.toolbar.pack(side="top", fill="x")

        tk.Button(self.toolbar, text="Add Folder", command=self.add_folder).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Previous", command=self.previous_image).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Next", command=self.next_image).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Add to List", command=self.add_to_list).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Show Added Images", command=self.show_added_images).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Show Selected Images", command=self.show_selected_images).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Export List", command=self.export_list).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text=self.fullScreenBtnText, command=self.exit_fullscreen).pack(side="right", padx=10, pady=10)
        
        # Rotate buttons
        tk.Button(self.toolbar, text="Rotate Left", command=self.rotate_left).pack(side="left", padx=10, pady=10)
        tk.Button(self.toolbar, text="Rotate Right", command=self.rotate_right).pack(side="left", padx=10, pady=10)

        self.status_label = tk.Label(self.toolbar, text="No image loaded", fg="blue", bg="gray")
        self.status_label.pack(side="left", padx=10)

        # Image display area
        self.main_frame = tk.Frame(root, bg="black")
        self.main_frame.pack(expand=True, fill="both")

        self.image_label = tk.Label(self.main_frame, bg="black")
        self.image_label.pack(expand=True, fill="both")


    def load_selected_images(self):
        """Load previously selected images from the default file."""
        if os.path.exists(self.selected_images_file):
            with open(self.selected_images_file, "r") as file:
                self.selected_images = [line.strip() for line in file if os.path.exists(line.strip())]
            print(f"Loaded {len(self.selected_images)} images from the previous session.")

    def save_selected_images(self):
        """Save the selected images to the default file."""
        with open(self.selected_images_file, "w") as file:
            for image_path in self.selected_images:
                file.write(image_path + "\n")

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

    def previous_image(self,event=None):
        """Show the previous image."""
        if self.image_paths:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
            self.rotation_angle = 0
            self.show_image()

    def next_image(self,event=None):
        """Show the next image."""
        if self.image_paths:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            self.rotation_angle = 0
            self.show_image()

    def add_to_list(self):
        """Add the currently displayed image to the selected list."""
        if self.image_paths:
            current_image = self.image_paths[self.current_image_index]
            if current_image not in self.selected_images:
                self.selected_images.append(current_image)
                self.save_selected_images()
                messagebox.showinfo("Added", f"Added {os.path.basename(current_image)} to the list.")
            else:
                messagebox.showwarning("Duplicate Entry", "This image is already in the list.")

    def show_added_images(self):
        """Show a list of all added images."""
        if self.selected_images:
            added_images_str = "\n".join([os.path.basename(img) for img in self.selected_images])
            messagebox.showinfo("Added Images", f"Added Images:\n\n{added_images_str}")
        else:
            messagebox.showinfo("No Images", "No images have been added to the list.")

    def show_selected_images(self):
        """Open a new window to show images from the selected list."""
        if not self.selected_images:
            messagebox.showinfo("No Images", "No images have been added to the list.")
            return

        selected_window = tk.Toplevel(self.root)
        selected_window.title("Selected Images")
        selected_window.attributes('-fullscreen', False)
        selected_window.bind("<Escape>", lambda e: selected_window.destroy())  # Exit on escape key

        current_image_index = 0

        def show_selected_image(index):
            """Show the selected image based on the given index."""
            if 0 <= index < len(self.selected_images):
                image_path = self.selected_images[index]
                image = Image.open(image_path)

                image.thumbnail((selected_window.winfo_screenwidth(), selected_window.winfo_screenheight()))
                photo = ImageTk.PhotoImage(image)

                image_label.config(image=photo, bg="black")
                image_label.image = photo
                status_label.config(text=f"Viewing {index + 1}/{len(self.selected_images)}: {os.path.basename(image_path)}")

        # Image display area in the new window
        image_label = tk.Label(selected_window, bg="black")
        image_label.pack(expand=True, fill="both")

        status_label = tk.Label(selected_window, text="No image loaded", fg="blue", bg="gray")
        status_label.pack(side="bottom", fill="x")

        def previous_image_selected():
            nonlocal current_image_index
            current_image_index = (current_image_index - 1) % len(self.selected_images)
            show_selected_image(current_image_index)

        def next_image_selected():
            nonlocal current_image_index
            current_image_index = (current_image_index + 1) % len(self.selected_images)
            show_selected_image(current_image_index)

        # Navigation buttons (without zoom or rotate options)
        navigation_frame = tk.Frame(selected_window, bg="gray")
        navigation_frame.pack(side="top", fill="x", padx=10, pady=5)

        tk.Button(navigation_frame, text="Previous", command=previous_image_selected).pack(side="left", padx=10, pady=5)
        tk.Button(navigation_frame, text="Next", command=next_image_selected).pack(side="left", padx=10, pady=5)

        # Show the first image initially
        show_selected_image(current_image_index)

    def export_list(self):
        """Export the selected images to a text file."""
        if self.selected_images:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text files", "*.txt")])
            if file_path:
                with open(file_path, "w") as file:
                    for image_path in self.selected_images:
                        file.write(image_path + "\n")
                messagebox.showinfo("Export Successful", f"List exported to {file_path}.")
        else:
            messagebox.showwarning("No Images", "No images selected to export.")

    def rotate_left(self):
        """Rotate the image left by 90 degrees."""
        self.rotation_angle -= 90
        self.show_image()

    def rotate_right(self):
        """Rotate the image right by 90 degrees."""
        self.rotation_angle += 90
        self.show_image()

    def exit_fullscreen(self,event=None):
        """Exit fullscreen mode when the Escape key is pressed."""
        root.attributes('-fullscreen', False)
        
    def toggle_fullscreen(self,event=None):
        """Toggle fullscreen mode."""
        is_fullscreen = root.attributes('-fullscreen')  # Check if fullscreen is enabled
        root.attributes('-fullscreen', not is_fullscreen)  # Toggle fullscreen state

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoOrganizerApp(root)
    root.mainloop()

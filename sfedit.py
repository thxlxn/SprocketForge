import os
import sys
import re

import customtkinter as ctk
from customtkinter import filedialog

from functions import generate_render_frames

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SFEDIT(ctk.CTk):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

        #-------------- Window setup --------------

        self.title("Sprocket FIle Editor")
        self.geometry("800x600")
        self.thickness_window = None
        self.render_window = None
        
        # Geometry fit to screen
        # height, width = self.winfo_screenheight(), self.winfo_screenwidth()
        # self.geometry("%dx%d+0+0" % (width, height))
        # self.wm_attributes('-fullscreen', True)


        # -------------- Buttons section --------------

        # > Thickness button
        self.thick_window_button = ctk.CTkButton(self, command=self.open_thickness_window, text="Thickness Editor",
                                                 width=200, height=50, font=("Arial", 14), 
                                                 fg_color="#C59102", hover_color="#DDB74F")
        self.thick_window_button.grid(row=0, column=0, padx=10, pady=10)

        # > Render button
        self.render_window_button = ctk.CTkButton(self, command=self.open_render_window, text="3D Visualizer",
                                                 width=200, height=50, font=("Arial", 14), 
                                                 fg_color="#C59102", hover_color="#DDB74F")
        self.render_window_button.grid(row=0, column=1, padx=10, pady=10)

        # > Exit button
        self.close_button = ctk.CTkButton(self, command=self.destroy, text="Exit", 
                                          width=200, height=50, font=("Arial", 14), 
                                          fg_color="#C59102", hover_color="#DDB74F")
        self.close_button.grid(row=0, column=2, padx=10, pady=10)
    
    def close_app(self):
        """
        Callback for exit button to close the app.
        """
        
        self.destroy()
    
    def open_thickness_window(self):
        """
        Open a new window for thickness selection.
        """
        
        if self.thickness_window is None or not self.thickness_window.winfo_exists():
            self.thickness_window = ThicknessWindow(self)
        else:
            self.thickness_window.focus()

    def open_render_window(self):
        """
        Open a new window for blueprint rendering.
        """

        if self.render_window is None or not self.render_window.winfo_exists():
            self.render_window = RenderWindow(self)
        else:
            self.render_window.focus()



class ThicknessWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # -------------- Window setup --------------

        self.geometry("600x400")
        
        # -------------- Buttons section --------------

        # > Back button
        self.back_button = ctk.CTkButton(self, command=self.destroy, text="<- Back",
                                         width=200, height=50, font=("Arial", 14),
                                         fg_color="#C59102", hover_color="#DDB74F")
        self.back_button.grid(row=0, column=1)
        # > Thickness button
        self.thickness_button = ctk.CTkButton(self, command=self.change_thickness, text="Change the thickness", 
                                              width=200, height=50, font=("Arial", 14),
                                              fg_color="#C59102", hover_color="#DDB74F")
        self.thickness_button.grid(row=0, column=0)
        # > Thickness selector slider
        self.thickval = 5
        self.thick_slider = ctk.CTkSlider(self, from_=1, to=100, command=self.set_thick, 
                                          fg_color="#DBC587", button_color="#C59102", button_hover_color="#DDB74F", progress_color="#C59102")
        self.thick_slider.grid(row=1, column=0, columnspan=2)
        self.thick_slider.set(self.thickval)

        # -------------- Labels section --------------

        self.thick_label = ctk.CTkLabel(self, text=f"{self.thickval} mm", font=("Arial", 14))
        self.thick_label.grid(row=2, column=0, columnspan=2, pady=(4,10))

    def set_thick(self, value):
        """
        Callback for thickness slider to set thickness value.
        """
        
        # Convert slider output to integer, store it and update label
        try:
            x = int(float(value))
        except Exception:
            x = 1
        self.thickval = x
        self.thick_label.configure(text=f"{self.thickval} mm")

    def change_thickness(self):
        """
        Callback for thickness button to change thickness in selected .blueprint file.
        """

        filepath = ctk.filedialog.askopenfilename(title="Select your .blueprint file", filetypes=[("Blueprint files", "*.blueprint")])
        if not filepath:
            return

        thickval = getattr(self, 'thickval', int(self.thick_slider.get() if hasattr(self, 'thick_slider') else 1))

        def new_thick(match):
            block = match.group(0)  # Get the "t" block
            return re.sub(r'\d+(?=\s*[,\]])', str(thickval), block)

        cur_thick = r'"t":\s*\[\s*(?:\d+\s*,\s*(?:\s*\n\s*)*)*\d+\s*\]'

        with open(filepath, "r", encoding="utf-8") as file:
            filedata = file.read()

        filedata = re.sub(cur_thick, new_thick, filedata, flags=re.DOTALL)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(filedata)



class RenderWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("3D Wireframe Renderer")
        self.geometry("700x750")
        
        # Memory / Animation State
        self.frames = []
        self.current_frame_idx = 0
        self.animation_id = None
        self.is_playing = False

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Controls Area
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.back_button = ctk.CTkButton(self.controls_frame, command=self.close_window, text="<- Back",
                                         fg_color="#C59102", hover_color="#DDB74F")
        self.back_button.pack(side="left", padx=5)

        self.load_button = ctk.CTkButton(self.controls_frame, command=self.load_and_render, text="Load Blueprint & Render",
                                         fg_color="#C59102", hover_color="#DDB74F")
        self.load_button.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(self.controls_frame, text="Select a file to begin.")
        self.status_label.pack(side="left", padx=10)

        # 2. Display Area
        self.display_frame = ctk.CTkFrame(self)
        self.display_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # We use a Label to display the Image
        self.image_label = ctk.CTkLabel(self.display_frame, text="")
        self.image_label.pack(expand=True, fill="both", padx=10, pady=10)

        # Override the default protocol for 'X' button
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def load_and_render(self):
        filepath = filedialog.askopenfilename(title="Select .blueprint", filetypes=[("Blueprint files", "*.blueprint")])
        if not filepath:
            return

        self.status_label.configure(text="Processing... (Window may freeze)")
        self.update_idletasks() # Force UI update before heavy calc

        # Stop existing animation if any
        self.stop_animation()

        # Run backend logic from the separate file
        try:
            # THIS IS THE CALL TO YOUR EXTERNAL FILE
            self.frames = generate_render_frames(filepath, size=600)
            
            if not self.frames:
                self.status_label.configure(text="Error: No geometry found.")
                return

            self.status_label.configure(text=f"Loaded: {os.path.basename(filepath)}")
            self.start_animation()
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            print(e)

    def start_animation(self):
        self.is_playing = True
        self.current_frame_idx = 0
        self.animate_loop()

    def animate_loop(self):
        if not self.is_playing or not self.frames:
            return

        # Get PIL Image
        pil_image = self.frames[self.current_frame_idx]
        
        # Convert to CTkImage
        # Note: We must specify size, or it defaults to 0x0
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(600, 600))
        
        # Update Label
        self.image_label.configure(image=ctk_img)
        
        # Next frame index
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)

        # Schedule next loop (50ms = ~20fps)
        self.animation_id = self.after(50, self.animate_loop)

    def stop_animation(self):
        self.is_playing = False
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None

    def close_window(self):
        """
        Clean up memory and destroy window
        """
        self.stop_animation()
        
        # Explicitly clear the list of images to help Garbage Collector
        if self.frames:
            self.frames.clear()
            self.frames = None
        
        self.destroy()


if __name__ == "__main__":
    root = SFEDIT()
    root.mainloop()
import os
import sys
import re

import customtkinter as ctk
from customtkinter import filedialog

from functions import generate_render_frames

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- Constants for Styling ---
COLOR_PRIMARY = "#C59102"
COLOR_HOVER = "#DDB74F"
COLOR_SLIDER_BG = "#DBC587"

class SFEDIT(ctk.CTk):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

        #-------------- Window setup --------------
        self.title("Sprocket File Editor")
        self.geometry("800x600")
        self.thickness_window = None
        self.render_window = None
        
        # Configure Grid for Centering
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        #-------------- Main Menu Frame --------------
        self.menu_frame = ctk.CTkFrame(self, corner_radius=15, width=400)
        self.menu_frame.grid(row=0, column=0, padx=20, pady=20)
        self.menu_frame.grid_columnconfigure(0, weight=1)

        # > Title
        self.title_label = ctk.CTkLabel(self.menu_frame, text="SPROCKET EDITOR", 
                                        font=("Arial", 28, "bold"), text_color=COLOR_PRIMARY)
        self.title_label.grid(row=0, column=0, padx=40, pady=(40, 20))

        # > Thickness button
        self.thick_window_button = ctk.CTkButton(self.menu_frame, command=self.open_thickness_window, 
                                                 text="Thickness Editor",
                                                 width=250, height=50, font=("Arial", 16), 
                                                 fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.thick_window_button.grid(row=1, column=0, padx=40, pady=15)

        # > Render button
        self.render_window_button = ctk.CTkButton(self.menu_frame, command=self.open_render_window, 
                                                  text="3D Visualizer",
                                                  width=250, height=50, font=("Arial", 16), 
                                                  fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.render_window_button.grid(row=2, column=0, padx=40, pady=15)

        # > Exit button
        self.close_button = ctk.CTkButton(self.menu_frame, command=self.destroy, text="Exit", 
                                          width=250, height=50, font=("Arial", 16), 
                                          fg_color="#555555", hover_color="#777777")
        self.close_button.grid(row=3, column=0, padx=40, pady=(15, 40))
        
        # > Footer info
        self.version_label = ctk.CTkLabel(self, text="v0.01 | SFEDIT", text_color="gray")
        self.version_label.place(relx=0.5, rely=0.95, anchor="center")

    def open_thickness_window(self):
        if self.thickness_window is None or not self.thickness_window.winfo_exists():
            self.thickness_window = ThicknessWindow(self)
        else:
            self.thickness_window.focus()

    def open_render_window(self):
        if self.render_window is None or not self.render_window.winfo_exists():
            self.render_window = RenderWindow(self)
        else:
            self.render_window.focus()


class ThicknessWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Thickness Editor")
        self.geometry("700x500")
        
        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Content row grows

        # 1. Top Controls Bar
        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.back_button = ctk.CTkButton(self.top_bar, command=self.destroy, text="<- Back",
                                         width=100, fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.back_button.pack(side="left", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(self.top_bar, text="Ready.")
        self.status_label.pack(side="left", padx=10)

        # 2. Main Content Area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Title in Content
        self.lbl_title = ctk.CTkLabel(self.content_frame, text="Adjust Armor Thickness", font=("Arial", 20, "bold"))
        self.lbl_title.pack(pady=(40, 20))

        # Value Label
        self.thickval = 5
        self.thick_label = ctk.CTkLabel(self.content_frame, text=f"{self.thickval} mm", font=("Arial", 40, "bold"), text_color=COLOR_PRIMARY)
        self.thick_label.pack(pady=10)

        # Slider
        self.thick_slider = ctk.CTkSlider(self.content_frame, from_=1, to=200, command=self.set_thick, width=400,
                                          fg_color=COLOR_SLIDER_BG, button_color=COLOR_PRIMARY, 
                                          button_hover_color=COLOR_HOVER, progress_color=COLOR_PRIMARY)
        self.thick_slider.pack(pady=20)
        self.thick_slider.set(self.thickval)

        # Apply Button
        self.apply_button = ctk.CTkButton(self.content_frame, command=self.change_thickness, 
                                          text="Select File & Apply",
                                          width=300, height=50, font=("Arial", 16),
                                          fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.apply_button.pack(pady=40)

    def set_thick(self, value):
        try:
            x = int(float(value))
        except Exception:
            x = 1
        self.thickval = x
        self.thick_label.configure(text=f"{self.thickval} mm")

    def change_thickness(self):
        filepath = ctk.filedialog.askopenfilename(title="Select your .blueprint file", filetypes=[("Blueprint files", "*.blueprint")])
        if not filepath:
            self.status_label.configure(text="Cancelled.")
            return

        thickval = self.thickval

        def new_thick(match):
            block = match.group(0)  # Get the "t" block
            return re.sub(r'\d+(?=\s*[,\]])', str(thickval), block)

        cur_thick = r'"t":\s*\[\s*(?:\d+\s*,\s*(?:\s*\n\s*)*)*\d+\s*\]'

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                filedata = file.read()

            filedata = re.sub(cur_thick, new_thick, filedata, flags=re.DOTALL)

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(filedata)
            
            self.status_label.configure(text=f"Success! Set to {thickval}mm for {os.path.basename(filepath)}")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")


class RenderWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("3D Wireframe Renderer")
        self.geometry("700x850") 
        
        # Memory / Animation State
        self.frames = []
        self.current_frame_idx = 0
        self.animation_id = None
        self.is_playing = False

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Top Controls Area
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.back_button = ctk.CTkButton(self.controls_frame, command=self.close_window, text="<- Back",
                                         fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, width=100)
        self.back_button.pack(side="left", padx=5)

        self.load_button = ctk.CTkButton(self.controls_frame, command=self.load_and_render, text="Load Blueprint",
                                         fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.load_button.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(self.controls_frame, text="Select a file to begin.")
        self.status_label.pack(side="left", padx=10)

        # 2. Display Area
        self.display_frame = ctk.CTkFrame(self)
        self.display_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.image_label = ctk.CTkLabel(self.display_frame, text="")
        self.image_label.pack(expand=True, fill="both", padx=10, pady=10)

        # 3. Bottom Controls (Slider & Switch)
        self.playback_frame = ctk.CTkFrame(self)
        self.playback_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Auto Spin Switch
        self.auto_spin_var = ctk.BooleanVar(value=True)
        self.spin_switch = ctk.CTkSwitch(self.playback_frame, text="Auto Spin", 
                                         command=self.toggle_spin, variable=self.auto_spin_var,
                                         progress_color=COLOR_PRIMARY, fg_color="#555555")
        self.spin_switch.pack(side="left", padx=20, pady=10)

        # Manual Rotation Slider
        self.frame_slider = ctk.CTkSlider(self.playback_frame, from_=0, to=1, number_of_steps=1,
                                          command=self.on_slider_drag,
                                          fg_color=COLOR_SLIDER_BG, button_color=COLOR_PRIMARY, 
                                          button_hover_color=COLOR_HOVER, progress_color=COLOR_PRIMARY)
        self.frame_slider.pack(side="left", fill="x", expand=True, padx=20, pady=10)
        self.frame_slider.set(0)

        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def load_and_render(self):
        filepath = filedialog.askopenfilename(title="Select .blueprint", filetypes=[("Blueprint files", "*.blueprint")])
        if not filepath:
            return

        self.status_label.configure(text="Processing... (Window may freeze)")
        self.update_idletasks() 

        self.stop_animation()

        try:
            # Generate 60 frames for a full rotation
            self.frames = generate_render_frames(filepath, size=600, frames_count=60)
            
            if not self.frames:
                self.status_label.configure(text="Error: No geometry found.")
                return

            self.status_label.configure(text=f"Loaded: {os.path.basename(filepath)}")
            
            # Update Slider limits to match frame count
            count = len(self.frames)
            self.frame_slider.configure(to=count - 1, number_of_steps=count - 1)
            self.frame_slider.set(0)

            # Start
            self.start_animation()
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            print(e)

    def start_animation(self):
        if self.auto_spin_var.get():
            self.is_playing = True
            self.animate_loop()
        else:
            self.is_playing = False
            self.show_current_frame()

    def toggle_spin(self):
        if self.auto_spin_var.get():
            if not self.frames: return
            self.is_playing = True
            self.animate_loop()
        else:
            self.is_playing = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
                self.animation_id = None

    def on_slider_drag(self, value):
        if not self.frames: return
        idx = int(value)
        self.current_frame_idx = idx
        self.show_current_frame()

    def show_current_frame(self):
        if not self.frames: return
        pil_image = self.frames[self.current_frame_idx]
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(600, 600))
        self.image_label.configure(image=ctk_img)

    def animate_loop(self):
        if not self.is_playing or not self.frames:
            return

        self.show_current_frame()
        self.frame_slider.set(self.current_frame_idx)
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)
        self.animation_id = self.after(50, self.animate_loop)

    def stop_animation(self):
        self.is_playing = False
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None

    def close_window(self):
        self.stop_animation()
        if self.frames:
            self.frames.clear()
            self.frames = None
        self.destroy()

if __name__ == "__main__":
    root = SFEDIT()
    root.mainloop()
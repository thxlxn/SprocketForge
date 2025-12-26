import os
import customtkinter as ctk
from customtkinter import filedialog
from importlib.metadata import version, PackageNotFoundError
from .functions import generate_render_frames, edit_blueprint_file, pack_blueprint_for_sharing, generate_era_files

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- Styling ---
COLOR_PRIMARY = "#C59102"
COLOR_HOVER = "#DDB74F"
COLOR_SLIDER_BG = "#DBC587"

class Core(ctk.CTk):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

        # main window setup
        self.title("SprocketForge")
        self.geometry("800x600")

        # container setup
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}

        # pages init
        for F in (MainMenu, FileEditPage, RenderPage, PackPage, EraPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            # stack
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainMenu")
        self.add_footer()

    def show_frame(self, page_name):
        for frame in self.frames.values():
            if hasattr(frame, "on_leave"):
                frame.on_leave()
                
        frame = self.frames[page_name]
        frame.tkraise()
    
    def add_footer(self):
        try:
            current_version = version("sprocketforge")
        except PackageNotFoundError:
            current_version = "dev"
        self.version_label = ctk.CTkLabel(self.container, text=f"{current_version} | SprocketForge", text_color="gray", fg_color="transparent", padx = 10)
        self.version_label.place(relx=0.5, rely=0.98, anchor="center")

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)

        # menu container
        self.menu_frame = ctk.CTkFrame(self, corner_radius=15, width=400)
        self.menu_frame.grid(row=0, column=0, padx=20, pady=20)
        self.menu_frame.grid_columnconfigure(0, weight=1)

        # title
        self.title_label = ctk.CTkLabel(self.menu_frame, text="SPROCKET FORGE", 
                                        font=("Arial", 28, "bold"), text_color=COLOR_PRIMARY)
        self.title_label.grid(row=0, column=0, padx=40, pady=(40, 20))

        # buttons
        self.thick_window_button = ctk.CTkButton(self.menu_frame, command=lambda: controller.show_frame("FileEditPage"), 
                                                 text="File Editor",
                                                 width=250, height=50, font=("Arial", 16), 
                                                 fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)

        self.pack_window_button = ctk.CTkButton(self.menu_frame, command=lambda: controller.show_frame("PackPage"), 
                                                text="Blueprint Packager",
                                                width=250, height=50, font=("Arial", 16), 
                                                fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        
        self.era_creator_button = ctk.CTkButton(self.menu_frame, command=lambda: controller.show_frame("EraPage"),
                                                text="Era Creator",
                                                width=250, height=50, font=("Arial", 16),
                                                fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)

        self.render_window_button = ctk.CTkButton(self.menu_frame, command=lambda: controller.show_frame("RenderPage"), 
                                                  text="3D Visualizer",
                                                  width=250, height=50, font=("Arial", 16), 
                                                  fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)

        self.close_button = ctk.CTkButton(self.menu_frame, command=controller.destroy, text="Exit", 
                                          width=250, height=50, font=("Arial", 16), 
                                          fg_color="#555555", hover_color="#777777")
        
        # buttons grid
        self.thick_window_button.grid(row=1, column=0, padx=40, pady=15)
        self.pack_window_button.grid(row=2, column=0, padx=40, pady=15)
        self.render_window_button.grid(row=3, column=0, padx=40, pady=15)
        self.era_creator_button.grid(row=4, column=0, padx=40, pady=15)
        self.close_button.grid(row=5, column=0, padx=40, pady=(15, 40))

class FileEditPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Top Nav ---
        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.back_button = ctk.CTkButton(self.top_bar, command=lambda: self.controller.show_frame("MainMenu"), text="<- Back",
                                         width=100, fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.back_button.pack(side="left", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(self.top_bar, text="Select options to edit.")
        self.status_label.pack(side="left", padx=10)

        # --- Scrollable Options List ---
        # using a scrollable frame so i can add more stuff later
        self.options_frame = ctk.CTkScrollableFrame(self, label_text="Modification Options")
        self.options_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.options_frame.grid_columnconfigure(0, weight=1)

        # ==================================================
        # OPTION 1: ARMOR THICKNESS
        # ==================================================
        self.thick_frame = ctk.CTkFrame(self.options_frame)
        self.thick_frame.pack(fill="x", padx=10, pady=10)

        self.use_thickness_var = ctk.BooleanVar(value=False)
        self.thick_check = ctk.CTkCheckBox(self.thick_frame, text="Overwrite Armor Thickness", 
                                           variable=self.use_thickness_var, command=self.toggle_thickness_ui,
                                           font=("Arial", 14, "bold"), fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.thick_check.pack(anchor="w", padx=10, pady=10)

        self.thick_content = ctk.CTkFrame(self.thick_frame, fg_color="transparent")
        self.thick_content.pack(fill="x", padx=20, pady=(0, 10))

        self.thickval = 5
        self.thick_label = ctk.CTkLabel(self.thick_content, text=f"{self.thickval} mm", font=("Arial", 30, "bold"))
        self.thick_label.pack()

        self.thick_slider = ctk.CTkSlider(self.thick_content, from_=1, to=200, command=self.set_thick, width=350)
        self.thick_slider.pack(pady=10)
        self.thick_slider.set(self.thickval)

        # init state
        self.toggle_thickness_ui()

        # ==================================================
        # OPTION 2: TRACKS
        # ==================================================
        self.tracks_frame = ctk.CTkFrame(self.options_frame)
        self.tracks_frame.pack(fill="x", padx=10, pady=10)

        # master switch for tracks
        self.use_tracks_var = ctk.BooleanVar(value=False)
        self.tracks_check = ctk.CTkCheckBox(self.tracks_frame, text="Track Modifications", 
                                            variable=self.use_tracks_var, command=self.toggle_tracks_ui,
                                            font=("Arial", 14, "bold"), fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.tracks_check.pack(anchor="w", padx=10, pady=10)

        self.tracks_content = ctk.CTkFrame(self.tracks_frame, fg_color="transparent")
        self.tracks_content.pack(fill="x", padx=20, pady=(0, 10))

        # Box 1: Invisible Tracks (guid swap)
        self.opt_inv_tracks_var = ctk.BooleanVar(value=False)
        self.opt_inv_tracks = ctk.CTkCheckBox(self.tracks_content, text="Invisible Tracks", variable=self.opt_inv_tracks_var)
        self.opt_inv_tracks.pack(anchor="w", pady=5)

        # placeholder for next feature
        # self.opt_xyz = ctk.BooleanVar(value=False)
        # self.opt_xyz = ctk.CTkCheckBox(self.tracks_content, text="xyz", variable=self.opt_xyz)
        # self.opt_xyz.pack(anchor="w", pady=5)

        self.toggle_tracks_ui()

        # --- Apply Button ---
        self.footer_frame = ctk.CTkFrame(self)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)

        self.apply_button = ctk.CTkButton(self.footer_frame, command=self.apply_changes, 
                                          text="Select File & Apply Selected Changes",
                                          height=50, font=("Arial", 16),
                                          fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.apply_button.pack(fill="x", padx=10, pady=10)

    # --- UI Helpers ---

    def toggle_thickness_ui(self):
        # handle visual state (greyed out vs normal)
        if self.use_thickness_var.get():
            self.thick_label.configure(text_color=COLOR_PRIMARY)
            self.thick_slider.configure(state="normal", button_color=COLOR_PRIMARY, progress_color=COLOR_PRIMARY)
        else:
            grey = "#555555"
            dark_grey = "#333333"
            self.thick_label.configure(text_color=grey)
            self.thick_slider.configure(state="disabled", button_color=grey, progress_color=dark_grey)

    def toggle_tracks_ui(self):
        state = "normal" if self.use_tracks_var.get() else "disabled"
        self.opt_inv_tracks.configure(state=state)

    def set_thick(self, value):
        try:
            x = int(float(value))
        except Exception:
            x = 1
        self.thickval = x
        self.thick_label.configure(text=f"{self.thickval} mm")

    def apply_changes(self):
        # sanity check
        if not (self.use_thickness_var.get() or self.use_tracks_var.get()):
            self.status_label.configure(text="No options selected. Nothing to do.")
            return

        filepath = ctk.filedialog.askopenfilename(title="Select .blueprint", filetypes=[("Blueprint files", "*.blueprint")])
        if not filepath:
            self.status_label.configure(text="Cancelled.")
            return

        # bundle up the settings
        settings = {
            "use_thickness": self.use_thickness_var.get(),
            "thickness_val": self.thickval,
            
            "use_tracks": self.use_tracks_var.get(),
            "invisible_tracks": self.opt_inv_tracks_var.get()
        }

        # do the heavy lifting in functions.py
        success, msg = edit_blueprint_file(filepath, settings)
        self.status_label.configure(text=msg)


class RenderPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # anim state
        self.frames = []
        self.current_frame_idx = 0
        self.animation_id = None
        self.is_playing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.back_button = ctk.CTkButton(self.controls_frame, command=lambda: self.controller.show_frame("MainMenu"), text="<- Back",
                                         fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, width=100)
        self.back_button.pack(side="left", padx=5)

        self.load_button = ctk.CTkButton(self.controls_frame, command=self.load_and_render, text="Load Blueprint",
                                         fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.load_button.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(self.controls_frame, text="Select a file to begin.")
        self.status_label.pack(side="left", padx=10)

        # 2. image display
        self.display_frame = ctk.CTkFrame(self)
        self.display_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.image_label = ctk.CTkLabel(self.display_frame, text="")
        self.image_label.pack(expand=True, fill="both", padx=10, pady=10)

        # 3. playback controls
        self.playback_frame = ctk.CTkFrame(self)
        self.playback_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.auto_spin_var = ctk.BooleanVar(value=True)
        self.spin_switch = ctk.CTkSwitch(self.playback_frame, text="Auto Spin", 
                                         command=self.toggle_spin, variable=self.auto_spin_var,
                                         progress_color=COLOR_PRIMARY, fg_color="#555555")
        self.spin_switch.pack(side="left", padx=20, pady=10)

        self.frame_slider = ctk.CTkSlider(self.playback_frame, from_=0, to=1, number_of_steps=1,
                                          command=self.on_slider_drag,
                                          fg_color=COLOR_SLIDER_BG, button_color=COLOR_PRIMARY, 
                                          button_hover_color=COLOR_HOVER, progress_color=COLOR_PRIMARY)
        self.frame_slider.pack(side="left", fill="x", expand=True, padx=20, pady=10)
        self.frame_slider.set(0)

    def load_and_render(self):
        filepath = filedialog.askopenfilename(title="Select .blueprint", filetypes=[("Blueprint files", "*.blueprint")])
        if not filepath:
            return

        self.status_label.configure(text="Processing... (Window may freeze)")
        self.update_idletasks() 

        self.stop_animation()

        try:
            # generating frames takes a sec
            self.frames = generate_render_frames(filepath, size=800, frames_count=60)
            
            if not self.frames:
                self.status_label.configure(text="Error: No geometry found.")
                return

            self.status_label.configure(text=f"Loaded: {os.path.basename(filepath)}")
            
            # fix slider limits
            count = len(self.frames)
            self.frame_slider.configure(to=count - 1, number_of_steps=count - 1)
            self.frame_slider.set(0)

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
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(800, 800))
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

    def on_leave(self):
        self.stop_animation()
        if self.frames:
            self.frames.clear()
            self.frames = []

class PackPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Top Nav ---
        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.back_button = ctk.CTkButton(self.top_bar, command=lambda: self.controller.show_frame("MainMenu"), text="<- Back",
                                         width=100, fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)
        self.back_button.pack(side="left", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(self.top_bar, text="Prepare blueprint for sharing.")
        self.status_label.pack(side="left", padx=10)

        # --- Main Content Frame ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Header inside the frame
        self.header_label = ctk.CTkLabel(self.main_frame, text="ZIP PACKAGER", 
                                         font=("Arial", 22, "bold"), text_color=COLOR_PRIMARY)
        self.header_label.pack(pady=(30, 10))

        self.info_label = ctk.CTkLabel(self.main_frame, 
                                       text="This will pack your blueprint and all local decals\ninto a ready-to-share ZIP file.", 
                                       font=("Arial", 14))
        self.info_label.pack(pady=10)

        # --- Directory Selection Section ---
        self.dir_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.dir_container.pack(fill="x", padx=60, pady=20)

        self.sprocket_path = ""
        self.dir_status = ctk.CTkLabel(self.dir_container, text="Sprocket folder not selected", 
                                       text_color="gray", font=("Arial", 12, "italic"))
        self.dir_status.pack(pady=5)

        self.dir_button = ctk.CTkButton(self.dir_container, text="Set Sprocket Directory", 
                                        command=self.select_sprocket_dir,
                                        fg_color="#555555", hover_color="#777777")
        self.dir_button.pack(pady=5)

        # --- Action Button ---
        self.pack_button = ctk.CTkButton(self.main_frame, text="Select Blueprint & Pack ZIP", 
                                         command=self.run_packer,
                                         height=55, width=320, font=("Arial", 16, "bold"),
                                         fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER,
                                         state="disabled") 
        self.pack_button.pack(pady=(20, 10))

        self.status_msg = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 13))
        self.status_msg.pack(pady=10)

    def select_sprocket_dir(self):
        path = filedialog.askdirectory(title="Select your Sprocket Game Folder")
        if path:
            self.sprocket_path = path
            # Show the end of the path so it's readable
            display_path = path if len(path) < 40 else f"...{path[-37:]}"
            self.dir_status.configure(text=f"Path: {display_path}", text_color="white")
            self.pack_button.configure(state="normal")

    def run_packer(self):
        blueprint_path = filedialog.askopenfilename(title="Select Blueprint to Pack", 
                                                   filetypes=[("Blueprint files", "*.blueprint")])
        if not blueprint_path:
            return

        self.status_msg.configure(text="Packing... please wait", text_color="white")
        self.update_idletasks()
        
        success, msg = pack_blueprint_for_sharing(blueprint_path, self.sprocket_path)
        
        if success:
            self.status_msg.configure(text=msg, text_color="#00FF00")
        else:
            self.status_msg.configure(text=msg, text_color="#FF4444")

class EraPage(ctk.CTkFrame):
    import json
import customtkinter as ctk

class EraPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.entries = {}
        self.sprocket_path = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Top Navigation ---
        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkButton(self.top_bar, text="<- Back", width=100, 
                      command=lambda: self.controller.show_frame("MainMenu"),
                      fg_color="#C59102", hover_color="#DDB74F").pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(self.top_bar, text="Configure your Era then select the Game Folder.")
        self.status_label.pack(side="left", padx=10)

        # --- Main Scroll Area ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Custom Era Settings")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # DIRECTORY SELECTION
        self.dir_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2B2B2B")
        self.dir_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.dir_frame, text="GAME DIRECTORY SETTING", font=("Arial", 12, "bold"), text_color="#C59102").pack(pady=(5,0))
        ctk.CTkLabel(self.dir_frame, text="Tip: Select the 'Sprocket' folder in steamapps/common.\nDo NOT use the folder in 'My Games'.", 
                     font=("Arial", 11, "italic"), text_color="gray").pack(pady=5)
        
        self.path_label = ctk.CTkLabel(self.dir_frame, text="No folder selected", text_color="white")
        self.path_label.pack(pady=2)
        
        ctk.CTkButton(self.dir_frame, text="Select Sprocket Folder", command=self.select_folder,
                      fg_color="#555555", hover_color="#777777").pack(pady=10)

        # Section Definitions
        self.create_section("Basic Era Info", [
            ("era_name", "Era Name", "Coldwar"),
            ("start_date", "Start Date", "1945.09.03"),
            ("med_mass", "Medium Mass", "18000"),
            ("heavy_mass", "Heavy Mass", "36000")
        ], "era")

        self.create_section("Engine", [
            ("torque_coeff", "Torque Coeff", "0.85"),
            ("tech_factor", "Tech Factor", "0.8")
        ], "engine")

        self.create_section("Cannon", [
            ("pressure", "Pressure", "40000"),
            ("penetrator", "Penetrator", "1900"),
            ("calibre", "Max Calibre", "100"),
            ("propellant", "Max Propellant", "360"),
            ("max_seg", "Max Segments", "20"),
            ("min_seg", "Min Segments", "1")
        ], "cannon")

        self.create_section("Traverse Motor", [
            ("resistance", "Resistance", "0.5"),
            ("max_torque", "Max Torque", "1500"),
            ("run_torque", "Running Torque", "800")
        ], "traverse")

        self.create_section("Misc Components", [
            ("track_res", "Track Resistance", "1.25"),
            ("max_gears", "Max Gears", "24")
        ], "misc")

        # --- Footer Save Button ---
        self.save_button = ctk.CTkButton(self, text="Generate Era Files", 
                                         height=50, command=self.save_all_files,
                                         fg_color="#C59102", hover_color="#DDB74F",
                                         state="disabled") # Disabled until path is chosen
        self.save_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def create_section(self, title, fields, section_key):
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.pack(fill="x", padx=10, pady=10)
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text=title.upper(), font=("Arial", 14, "bold"), text_color="#C59102").grid(row=0, column=0, columnspan=2, pady=5)
        
        for i, (key, label_text, default) in enumerate(fields, start=1):
            ctk.CTkLabel(frame, text=label_text).grid(row=i, column=0, padx=10, pady=2, sticky="w")
            entry = ctk.CTkEntry(frame, placeholder_text=default)
            entry.grid(row=i, column=1, padx=10, pady=2, sticky="ew")
            self.entries[key] = (entry, default)

    def select_folder(self):
        path = filedialog.askdirectory(title="Select your Sprocket Steam Folder")
        if path:
            self.sprocket_path = path
            display_path = path if len(path) < 50 else f"...{path[-47:]}"
            self.path_label.configure(text=display_path)
            self.save_button.configure(state="normal") # Enable saving

    def save_all_files(self):
        if not self.sprocket_path:
            self.status_label.configure(text="Error: Select game folder first!", text_color="#FF4444")
            return

        data_package = {}
        for key, (entry, default) in self.entries.items():
            val = entry.get()
            data_package[key] = val if val else default

        success, msg = generate_era_files(data_package, self.sprocket_path)
        
        color = "#00FF00" if success else "#FF4444"
        self.status_label.configure(text=msg, text_color=color)

if __name__ == "__main__":
    root = Core()
    root.mainloop()
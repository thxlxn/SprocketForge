import os
import sys
import re

import customtkinter as ctk
from customtkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class SFEDIT(ctk.CTk):
    def __init__(self): 
        super().__init__()
        self.title("Sprocket FIle Editor")
        self.geometry("400x300")
        
        # Geometry fit to screen
        # height, width = self.winfo_screenheight(), self.winfo_screenwidth()
        # self.geometry("%dx%d+0+0" % (width, height))
        # self.wm_attributes('-fullscreen', True)


        # -------------- Buttons section --------------

        # > Exit button
        self.close_button = ctk.CTkButton(self, command=self.close_app, text="Exit", width=200, height=50, font=("Arial", 14))
        self.close_button.grid(row=0, column=1)
        # > Thickness button
        self.thickness_button = ctk.CTkButton(self, command=self.change_thickness, text="Change the thickness", width=200, height=50, font=("Arial", 14))
        self.thickness_button.grid(row=0, column=0)
        # > Thickness selector slider
        self.thickval = 5
        self.thick_slider = ctk.CTkSlider(self, from_=1, to=100, command=self.set_thick)
        self.thick_slider.grid(row=1, column=0, columnspan=2)
        self.thick_slider.set(self.thickval)

        # -------------- Labels section --------------

        self.thick_label = ctk.CTkLabel(self, text=f"{self.thickval} mm", font=("Arial", 14))
        self.thick_label.grid(row=2, column=0, columnspan=2, pady=(4,10))
    
    def close_app(self):
        """
        Callback for exit button to close the app.
        """
        
        self.destroy()
    
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
        

root = SFEDIT()
root.mainloop()
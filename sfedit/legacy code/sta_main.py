import os
import sys
import re

import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
from tkinter.filedialog import askopenfilename

root = tk.Tk()
root.geometry("900x400")
root.title("Sprocket File Editing Tool")

def change_thickness():
    filepath = askopenfilename(title="Select your .blueprint file")
    if filepath:
        
        thickval = simpledialog.askinteger("Input", "Enter the new thickness value:", minvalue=1, maxvalue=500)

        def new_thick(match):
            block = match.group(0) # Get the "t" block
            return re.sub(r'\d+(?=\s*[,\]])', str(thickval), block)
        
        cur_thick = r'"t":\s*\[\s*(?:\d+\s*,\s*(?:\s*\n\s*)*)*\d+\s*\]'
        
        with open(filepath, "r") as file:
            filedata = file.read()

        filedata = re.sub(cur_thick, new_thick, filedata, flags=re.DOTALL)

        with open(filepath, "w") as file:
            file.write(filedata)

        messagebox.showinfo("Success", f"Changed the thickness to {thickval} mm in {os.path.basename(filepath)}")
        
    else:
        pass

thickness_btn = tk.Button(root, text="Change the thickness", command=change_thickness, width=30, font=("Arial", 14))
thickness_btn.grid(row=1, column=1)
exit_btn = tk.Button(root, text="Exit", command=lambda: root.destroy(), width=30, font=("Arial", 14))
exit_btn.grid(row=1, column=2)

root.mainloop()
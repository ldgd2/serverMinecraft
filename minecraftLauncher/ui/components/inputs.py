import customtkinter as ctk
from typing import Callable, Any
import tkinter.filedialog as fd
import os
from PIL import Image
from core.paths import get_resource_path

class StyledInputRow(ctk.CTkFrame):
    def __init__(self, master, label_text: str, description: str, default_value: Any, input_type: str = "string", command: Callable = None, browse_type: str = None, **kwargs):
        """
        A reusable row containing a label, description, and an input field.
        input_type can be 'string' or 'int'.
        browse_type can be 'file' or 'directory'.
        """
        super().__init__(master, fg_color="#1E1E1E", corner_radius=10, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text=label_text, font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF")
        self.title_label.grid(row=0, column=0, padx=15, pady=(15, 0), sticky="w")
        
        self.desc_label = ctk.CTkLabel(self, text=description, font=ctk.CTkFont(size=12), text_color="#AAAAAA")
        self.desc_label.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")
        
        self.command = command
        self.input_type = input_type
        
        self.entry = ctk.CTkEntry(
            self, 
            width=300 if input_type == "string" else 100,
            height=40,
            fg_color="#333333", 
            border_color="#444444",
            border_width=1,
            text_color="white",
            corner_radius=8
        )
        self.entry.insert(0, str(default_value))
        self.entry.grid(row=0, column=1, rowspan=2, padx=15, pady=15, sticky="e")
        
        if self.command:
            self.entry.bind("<KeyRelease>", self._on_change)

        if browse_type:
            icon_path = get_resource_path(os.path.join("ui", "assets", "icons", "folder.png"))
            self.folder_icon = ctk.CTkImage(Image.open(icon_path), size=(20, 20)) if os.path.exists(icon_path) else None

            self.entry.grid(row=0, column=1, rowspan=2, padx=(15, 5), pady=15, sticky="e")
            self.browse_button = ctk.CTkButton(
                self, 
                text="", 
                image=self.folder_icon,
                width=40,
                height=40,
                fg_color="#00A859",
                hover_color="#008044",
                corner_radius=8,
                command=lambda: self._on_browse(browse_type)
            )
            self.browse_button.grid(row=0, column=2, rowspan=2, padx=(5, 15), pady=15, sticky="e")

    def _on_browse(self, b_type):
        if b_type == "directory":
            path = fd.askdirectory()
        else:
            path = fd.askopenfilename()
            
        if path:
            path = os.path.normpath(path)
            self.set(path)
            if self.command:
                self.command(path)

    def _on_change(self, event):
        if self.command:
            self.command(self.get())

    def get(self):
        val = self.entry.get()
        if self.input_type == "int":
            try:
                return int(val)
            except ValueError:
                return 0
        return val

    def set(self, value):
        self.entry.delete(0, 'end')
        self.entry.insert(0, str(value))

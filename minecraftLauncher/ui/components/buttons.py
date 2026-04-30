import customtkinter as ctk

class PremiumButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, variant="primary", **kwargs):
        """
        Reusable animated button for consistent styling.
        Variants: primary, secondary, danger, success
        """
        
        self.colors = {
            "primary": {"fg": "#0078D7", "hover": "#005A9E", "text": "white"},
            "secondary": {"fg": "#333333", "hover": "#444444", "text": "white"},
            "danger": {"fg": "#E81123", "hover": "#B00A1A", "text": "white"},
            "success": {"fg": "#00A859", "hover": "#008044", "text": "white"}
        }
        
        self.variant = variant
        if variant not in self.colors:
            self.variant = "primary"
            
        height = kwargs.pop("height", 45)
        corner_radius = kwargs.pop("corner_radius", 8)
        
        super().__init__(
            master, 
            text=text, 
            command=command,
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            height=height,
            corner_radius=corner_radius,
            fg_color=self.colors[self.variant]["fg"],
            hover_color=self.colors[self.variant]["hover"],
            text_color=self.colors[self.variant]["text"],
            **kwargs
        )

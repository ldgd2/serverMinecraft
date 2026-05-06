"""
Minecraft Launcher - Shared Widget Library
All widgets use real Minecraft GUI sprites and the Minecraft TTF font.
"""
import tkinter as tk
import os
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageFont
from ui.theme import Colors, Assets, mc_font


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftDirtBackground(tk.Canvas):
    """
    A resizable canvas that tiles a dirt background image (e.g. menu_background.png).
    """
    def __init__(self, master, image_path=Assets.MENU_BG, **kwargs):
        super().__init__(master, highlightthickness=0, bd=0, **kwargs)
        self._bg_img = _load_img(image_path, pixelated=True)
        self._bg_tk = None
        self._bg_images = [] # keep references
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        if not self._bg_img:
            return
            
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return

        self.delete("bg")
        
        tw, th = self._bg_img.size
        # Create a single repeated background image to avoid GDI handle leaks (crash fix)
        new_bg = Image.new("RGBA", (w, h))
        for x in range(0, w, tw):
            for y in range(0, h, th):
                new_bg.paste(self._bg_img, (x, y))
                
        self._bg_tk = ImageTk.PhotoImage(new_bg)
        self.create_image(0, 0, anchor="nw", image=self._bg_tk, tags="bg")

def _load_img(path, size=None, pixelated=True):
    """Load a PIL image; optionally resize with nearest-neighbor (pixel art)."""
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    if size:
        method = Image.NEAREST if pixelated else Image.LANCZOS
        img = img.resize(size, method)
    return img


def _make_shadow(text: str, font, fill="#ffffff", shadow="#3f3f3f", offset=(2, 2)):
    """Draw text with a drop shadow onto a transparent RGBA image using PIL."""
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    try:
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
    except Exception:
        bbox = (0, 0, len(text) * 8, 16)
    w = bbox[2] - bbox[0] + abs(offset[0]) + 4
    h = bbox[3] - bbox[1] + abs(offset[1]) + 4
    img = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((2 + offset[0], 2 + offset[1]), text, font=font, fill=shadow)
    draw.text((2, 2), text, font=font, fill=fill)
    return img


def _pil_font(size=12):
    """Return a PIL ImageFont object from the Minecraft TTF."""
    try:
        return ImageFont.truetype(Assets.FONT_MC, size)
    except Exception:
        return ImageFont.load_default()


def _load_svg_as_pil(svg_path, size=(24, 24)):
    """
    Load an SVG file as a PIL RGBA image of the given size.
    Uses cairosvg if available; falls back to a white placeholder square.
    """
    if not os.path.exists(svg_path):
        img = Image.new("RGBA", size, (255, 255, 255, 180))
        return img
    try:
        import cairosvg
        png_data = cairosvg.svg2png(url=svg_path,
                                    output_width=size[0],
                                    output_height=size[1])
        from io import BytesIO
        img = Image.open(BytesIO(png_data)).convert("RGBA")
        return img.resize(size, Image.LANCZOS)
    except Exception:
        # Fallback: white square placeholder
        img = Image.new("RGBA", size, (255, 255, 255, 200))
        return img


# ─────────────────────────────────────────────────────────────────────────────
#  9-slice button helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_button_img(sprite_path, width, height, border=2):
    """
    Build a 9-slice scaled button image from a 200x20 Minecraft button sprite.
    Maintains pixel art sharpness by pre-scaling before slicing.
    """
    if not os.path.exists(sprite_path):
        return Image.new("RGBA", (width, height), "#8b8b8b")

    raw = Image.open(sprite_path).convert("RGBA")
    sw, sh = raw.size
    
    # Base scale factor (Minecraft buttons are 20px high)
    scale = max(1, height // 20)
    raw = raw.resize((sw * scale, sh * scale), Image.NEAREST)
    
    # 9-slice setup
    # Real minecraft buttons have a 2px bevel/border. We scale that.
    b = border * scale
    sw2, sh2 = raw.size

    # corners
    tl = raw.crop((0, 0, b, b))
    tr = raw.crop((sw2 - b, 0, sw2, b))
    bl = raw.crop((0, sh2 - b, b, sh2))
    br = raw.crop((sw2 - b, sh2 - b, sw2, sh2))
    # edges
    top  = raw.crop((b, 0, sw2 - b, b))
    bot  = raw.crop((b, sh2 - b, sw2 - b, sh2))
    lft  = raw.crop((0, b, b, sh2 - b))
    rgt  = raw.crop((sw2 - b, b, sw2, sh2 - b))
    # center
    ctr  = raw.crop((b, b, sw2 - b, sh2 - b))

    out = Image.new("RGBA", (width, height))
    cw = width - 2 * b
    ch = height - 2 * b

    # paste corners
    out.paste(tl, (0, 0))
    out.paste(tr, (width - b, 0))
    out.paste(bl, (0, height - b))
    out.paste(br, (width - b, height - b))
    
    # paste edges scaled
    if cw > 0:
        out.paste(top.resize((cw, b), Image.NEAREST), (b, 0))
        out.paste(bot.resize((cw, b), Image.NEAREST), (b, height - b))
    if ch > 0:
        out.paste(lft.resize((b, ch), Image.NEAREST), (0, b))
        out.paste(rgt.resize((b, ch), Image.NEAREST), (width - b, b))
    
    # paste center scaled
    if cw > 0 and ch > 0:
        out.paste(ctr.resize((cw, ch), Image.NEAREST), (b, b))

    return out


# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftButton
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftButton(tk.Canvas):
    """
    A Minecraft-style button widget that uses real button.png sprites.
    Hover turns text yellow; pressed darkens; disabled grays out.
    Supports an optional left-side icon (PIL Image).
    """

    def __init__(self, master, text="Button", command=None, width=200, height=40,
                 font_size=14, disabled=False, icon_img=None, **kwargs):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0,
                         cursor="hand2" if not disabled else "arrow",
                         **kwargs)

        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.font_size = font_size
        self._disabled = disabled
        self._hover = False
        self._pressed = False
        self._icon_img = icon_img      # PIL RGBA image or None
        self._tk_icon  = None

        # Pre-render icon if given
        if icon_img:
            ico = icon_img.copy()
            ico_h = max(int(height * 0.55), 16)
            ico = ico.resize((ico_h, ico_h), Image.LANCZOS)
            self._tk_icon = ImageTk.PhotoImage(ico)
            self._icon_w  = ico_h
        else:
            self._icon_w = 0

        # Pre-render button images
        self._img_normal   = self._render(Assets.BTN)
        self._img_hover    = self._render(Assets.BTN_HOV)
        self._img_disabled = self._render(Assets.BTN_DIS)

        self._tk_normal   = ImageTk.PhotoImage(self._img_normal)   if self._img_normal   else None
        self._tk_hover    = ImageTk.PhotoImage(self._img_hover)    if self._img_hover    else None
        self._tk_disabled = ImageTk.PhotoImage(self._img_disabled) if self._img_disabled else None

        self._pil_font = _pil_font(font_size)
        self._draw()

        if not disabled:
            self.bind("<Enter>",         self._on_enter)
            self.bind("<Leave>",         self._on_leave)
            self.bind("<ButtonPress-1>", self._on_press)
            self.bind("<ButtonRelease-1>", self._on_release)

    def _render(self, path):
        return _build_button_img(path, self.width, self.height)

    def _draw(self):
        self.delete("all")
        if self._disabled:
            bg = self._tk_disabled
        elif self._hover:
            bg = self._tk_hover
        else:
            bg = self._tk_normal

        if bg:
            self.create_image(0, 0, anchor="nw", image=bg)
        else:
            color = Colors.BTN_DISABLED if self._disabled else (Colors.BTN_HOVER_TOP if self._hover else Colors.PANEL)
            self.create_rectangle(0, 0, self.width, self.height, fill=color, outline=Colors.PANEL_BORDER)

        text_color = Colors.GRAY_TEXT if self._disabled else (Colors.YELLOW if self._hover else Colors.WHITE)
        shadow_color = Colors.SHADOW

        # icon + text layout
        icon_gap = 6 if self._tk_icon else 0
        content_w = self._icon_w + icon_gap

        txt_img = _make_shadow(self.text, self._pil_font, fill=text_color, shadow=shadow_color)
        tw, th = txt_img.size
        content_w += tw

        x_start = (self.width - content_w) // 2
        cy = self.height // 2

        if self._tk_icon:
            ico_y = cy - self._icon_w // 2
            self.create_image(x_start, ico_y, anchor="nw", image=self._tk_icon)
            x_start += self._icon_w + icon_gap

        y_off = (self.height - th) // 2
        self._tk_txt = ImageTk.PhotoImage(txt_img)
        self.create_image(x_start, y_off, anchor="nw", image=self._tk_txt)

    def _on_enter(self, e):
        self._hover = True
        self._draw()

    def _on_leave(self, e):
        self._hover = False
        self._pressed = False
        self._draw()

    def _on_press(self, e):
        self._pressed = True
        self._draw()

    def _on_release(self, e):
        was_pressed = self._pressed and self._hover
        self._pressed = False
        
        if self.winfo_exists():
            self._draw()
            
        if was_pressed and self.command:
            self.command()

    def configure_state(self, disabled: bool):
        self._disabled = disabled
        self.config(cursor="arrow" if disabled else "hand2")
        self._draw()

    def set_text(self, text: str):
        self.text = text
        self._draw()

    def set_command(self, command):
        self.command = command


# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftLabel (with pixel drop shadow)
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftLabel(tk.Label):
    """Simple tk.Label pre-styled with Minecraft font tuple."""

    def __init__(self, master, text="", size=14, color=Colors.WHITE,
                 shadow=True, bg=None, **kwargs):
        # We do shadow via PIL and use a Label with image
        self._pil_f = _pil_font(size)
        self._shadow = shadow
        self._color = color
        self._text = text
        self._bg_color = bg

        self._render_img(text, color)
        super().__init__(master, image=self._tk_img, text="",
                         bg=bg or Colors.DARK, bd=0,
                         highlightthickness=0, **kwargs)

    def _render_img(self, text, color):
        img = _make_shadow(text or " ", self._pil_f, fill=color,
                           shadow=Colors.SHADOW if self._shadow else color)
        self._tk_img = ImageTk.PhotoImage(img)

    def set_text(self, text, color=None):
        self._text = text
        self._color = color or self._color
        self._render_img(text, self._color)
        self.config(image=self._tk_img)


# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftInput
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftInput(tk.Frame):
    """
    A styled text input field resembling Minecraft's text_field.png.
    Contains an inner tk.Entry.
    """

    def __init__(self, master, placeholder="", width=200, height=32,
                 show=None, font_size=12, **kwargs):
        super().__init__(master, width=width, height=height,
                         bg=Colors.PANEL_DARK,
                         highlightthickness=2,
                         highlightbackground=Colors.PANEL_BORDER,
                         highlightcolor=Colors.WHITE,
                         **kwargs)
        self.pack_propagate(False)

        self._placeholder = placeholder
        self._show = show
        self._has_placeholder = True

        self.entry = tk.Entry(
            self,
            bg="#000000",
            fg=Colors.GRAY_TEXT,
            insertbackground=Colors.WHITE,
            bd=0,
            relief="flat",
            font=mc_font(font_size),
            show=show or "",
        )
        self.entry.pack(fill="both", expand=True, padx=6, pady=4)

        if placeholder:
            self._set_placeholder()
            self.entry.bind("<FocusIn>",  self._clear_placeholder)
            self.entry.bind("<FocusOut>", self._restore_placeholder)

    def _set_placeholder(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, self._placeholder)
        self.entry.config(fg=Colors.GRAY_TEXT, show="")
        self._has_placeholder = True

    def _clear_placeholder(self, e=None):
        if self._has_placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=Colors.WHITE, show=self._show or "")
            self._has_placeholder = False

    def _restore_placeholder(self, e=None):
        if not self.entry.get():
            self._set_placeholder()

    def get(self):
        if self._has_placeholder:
            return ""
        return self.entry.get()

    def set(self, value):
        self._has_placeholder = False
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        self.entry.config(fg=Colors.WHITE, show=self._show or "")


# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftPanel  (raised stone panel)
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftPanel(tk.Frame):
    """A panel that looks like Minecraft's menu background (dark stone)."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("bg", Colors.PANEL_DARK)
        kwargs.setdefault("highlightthickness", 2)
        kwargs.setdefault("highlightbackground", Colors.PANEL_BORDER)
        super().__init__(master, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftCheckbox
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftCheckbox(tk.Frame):
    """A Minecraft-styled checkbox using checkbox.png sprites."""

    def __init__(self, master, text="", initial=False, command=None,
                 font_size=12, bg=None, **kwargs):
        _bg = bg or Colors.PANEL_DARK
        super().__init__(master, bg=_bg, **kwargs)

        self._value = tk.BooleanVar(value=initial)
        self._command = command
        self._bg = _bg
        self._font_size = font_size

        box_size = 20
        self._img_off  = self._load_sprite(Assets.CHECKBOX,     box_size)
        self._img_on   = self._load_sprite(Assets.CHECKBOX_SEL, box_size)

        self._canvas = tk.Canvas(self, width=box_size, height=box_size,
                                 bg=_bg, highlightthickness=0, bd=0,
                                 cursor="hand2")
        self._canvas.pack(side="left", padx=(0, 6))

        self._label = tk.Label(self, text=text, bg=_bg,
                               fg=Colors.WHITE, font=mc_font(font_size))
        self._label.pack(side="left")

        self._draw()
        self._canvas.bind("<Button-1>", self._toggle)
        self._label.bind("<Button-1>",  self._toggle)

    def _load_sprite(self, path, size):
        if not os.path.exists(path):
            return None
        img = Image.open(path).convert("RGBA").resize((size, size), Image.NEAREST)
        return ImageTk.PhotoImage(img)

    def _draw(self):
        self._canvas.delete("all")
        img = self._img_on if self._value.get() else self._img_off
        if img:
            self._canvas.create_image(0, 0, anchor="nw", image=img)
        else:
            color = Colors.WHITE if self._value.get() else Colors.PANEL_DARK
            self._canvas.create_rectangle(2, 2, 18, 18, fill=color,
                                          outline=Colors.WHITE)

    def _toggle(self, e=None):
        self._value.set(not self._value.get())
        self._draw()
        if self._command:
            self._command(self._value.get())

    def get(self):
        return self._value.get()

    def set(self, val):
        self._value.set(val)
        self._draw()


# ─────────────────────────────────────────────────────────────────────────────
#  PanoramaBackground  — FIXED: no per-frame LANCZOS rescaling
# ─────────────────────────────────────────────────────────────────────────────

class PanoramaBackground(tk.Canvas):
    """
    Slowly pans across the Minecraft panorama images to create the animated
    main menu background effect.
    
    Performance fixes vs original:
    - Strip is pre-scaled only on resize (not every frame)
    - Resize uses BILINEAR (fast, acceptable quality)  
    - Overlay pre-composited once; only the crop + paste changes per frame
    - Target: 20 fps (50ms interval) — smooth without hogging the CPU
    - Correct seamless wrap (no repeated frames / seams)
    """

    INTERVAL_MS = 50   # 20fps — smooth & light
    SPEED       = 0.8  # px/frame at native resolution (slow gentle pan)

    def __init__(self, master, width=1100, height=700, overlay_alpha=120, **kwargs):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, **kwargs)
        self._width  = width
        self._height = height
        self._overlay_alpha = overlay_alpha
        self._tk_img = None
        self._offset = 0.0

        # Scaled/prepped strip (rebuilt on resize)
        self._scaled_strip  = None
        self._cached_size   = (-1, -1)
        self._anim_id       = None

        self._load_panoramas()
        self.bind("<Configure>", self._on_resize)
        self._animate()

    def _load_panoramas(self):
        """
        Load all 6 panorama frames and stitch into one wide horizontal strip.
        Only frames 0-3 form the 360° loop; 4-5 are extras (sky/ground).
        We use 0-3 and duplicate frame 0 at the end for a seamless wrap.
        """
        images = []
        for i in range(6):
            path = Assets.PANORAMAS[i] if i < len(Assets.PANORAMAS) else None
            if path and os.path.exists(path):
                images.append(Image.open(path).convert("RGB"))

        if not images:
            self._master_strip = None
            return

        # Use first 4 (360° faces); fallback to however many we have
        loop_imgs = images[:4] if len(images) >= 4 else images
        w, h = loop_imgs[0].size

        # Stitch + duplicate first frame at end for seamless wrap
        strip_w = w * (len(loop_imgs) + 1)
        self._master_strip = Image.new("RGB", (strip_w, h))
        for i, img in enumerate(loop_imgs):
            if img.size != (w, h):
                img = img.resize((w, h), Image.BILINEAR)
            self._master_strip.paste(img, (i * w, 0))
        # duplicate first frame at end
        self._master_strip.paste(loop_imgs[0], (len(loop_imgs) * w, 0))

    def _build_scaled_strip(self, w, h):
        """Rescale the master strip to fill height h. Called only when size changes."""
        if not self._master_strip:
            return
        ratio     = h / self._master_strip.height
        new_strip_w = max(int(self._master_strip.width * ratio), 1)
        self._scaled_strip = self._master_strip.resize(
            (new_strip_w, h), Image.BILINEAR
        )
        self._cached_size = (w, h)
        # Reset offset so it never exceeds new strip width
        loop_w = (new_strip_w * 4) // 5   # 4/5 of strip = loopable section
        self._offset = self._offset % loop_w

    def _on_resize(self, event):
        new_size = (event.width, event.height)
        if new_size != self._cached_size:
            self._build_scaled_strip(event.width, event.height)
        self._width  = event.width
        self._height = event.height

    def _animate(self):
        if not self._master_strip:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1: w = self._width
        if h <= 1: h = self._height
        if w <= 0 or h <= 0:
            self._anim_id = self.after(self.INTERVAL_MS, self._animate)
            return

        # Rebuild scaled strip if size changed (lazy)
        if (w, h) != self._cached_size:
            self._build_scaled_strip(w, h)

        if not self._scaled_strip:
            self._anim_id = self.after(self.INTERVAL_MS, self._animate)
            return

        try:
            strip  = self._scaled_strip
            sw     = strip.width
            # Only the first 4/5 of strip is the loop (last 1/5 = copy of frame 0)
            loop_w = (sw * 4) // 5 if sw > 0 else sw
            if loop_w < 1:
                loop_w = sw

            self._offset = (self._offset + self.SPEED) % loop_w
            ox = int(self._offset)

            # Crop visible window — may span wrap point
            if ox + w <= sw:
                visible = strip.crop((ox, 0, ox + w, h))
            else:
                part1 = strip.crop((ox, 0, sw, h))
                need  = w - (sw - ox)
                part2 = strip.crop((0, 0, min(need, sw), h))
                visible = Image.new("RGB", (w, h))
                visible.paste(part1, (0, 0))
                visible.paste(part2, (sw - ox, 0))

            # Dark overlay — composite in one pass (no extra RGBA conversion)
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, self._overlay_alpha))
            visible_rgba = visible.convert("RGBA")
            Image.alpha_composite(visible_rgba, overlay, dest=(0, 0))
            visible_rgba.paste(overlay, (0, 0), overlay)

            self._tk_img = ImageTk.PhotoImage(visible_rgba)
            self.delete("all")
            self.create_image(0, 0, anchor="nw", image=self._tk_img)

        except Exception:
            pass

        self._anim_id = self.after(self.INTERVAL_MS, self._animate)

    def stop(self):
        """Stop the animation loop (call when view is hidden)."""
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None


# ─────────────────────────────────────────────────────────────────────────────
#  SkinHead  (extracts & scales the 8×8 face from a skin PNG)
# ─────────────────────────────────────────────────────────────────────────────

class SkinHead(tk.Label):
    """
    Shows the player's skin head (face) extracted from a 64×64 skin texture.
    Falls back to a Steve head if no skin is available.
    """

    def __init__(self, master, size=48, bg=Colors.PANEL_DARK, **kwargs):
        self._size = size
        self._bg   = bg
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self._tk_img = None
        self.set_skin(None)

    def set_skin(self, skin_path: str | None):
        """Load a skin PNG, extract the 8×8 face pixels, and display them."""
        img = self._extract_face(skin_path)
        img = img.resize((self._size, self._size), Image.NEAREST)
        self._tk_img = ImageTk.PhotoImage(img)
        self.config(image=self._tk_img)

    def _extract_face(self, path):
        # Default Steve face (gray)
        default = Image.new("RGBA", (8, 8), "#7a6c60")
        if not path or not os.path.exists(path):
            return default
        try:
            skin = Image.open(path).convert("RGBA")
            if skin.width < 64 or skin.height < 32:
                return default
            # Face is at (8, 8, 16, 16) in the skin layout
            face = skin.crop((8, 8, 16, 16))
            # Hat layer overlay at (40, 8, 48, 16)
            if skin.width >= 48 and skin.height >= 16:
                hat = skin.crop((40, 8, 48, 16))
                face.paste(hat, (0, 0), hat)
            return face
        except Exception:
            return default


# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftSlider
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftSlider(tk.Frame):
    """
    A Minecraft-style horizontal slider using slider.png and slider_handle.png.
    """

    def __init__(self, master, from_=0, to=100, initial=50, label_format="{:.0f}",
                 command=None, width=300, height=20, bg=None, **kwargs):
        _bg = bg or Colors.PANEL_DARK
        super().__init__(master, bg=_bg, **kwargs)

        self._from = from_
        self._to   = to
        self._value = initial
        self._fmt   = label_format
        self._command = command
        self._width  = width
        self._track_h = height

        tvar = tk.DoubleVar(value=initial)
        self._var = tvar

        self._scale = tk.Scale(
            self,
            from_=from_,
            to=to,
            orient="horizontal",
            variable=tvar,
            length=width,
            showvalue=False,
            bg=_bg,
            fg=Colors.WHITE,
            troughcolor=Colors.PANEL_BORDER,
            activebackground=Colors.YELLOW,
            highlightthickness=0,
            sliderlength=20,
            bd=0,
            command=self._on_change,
        )
        self._scale.pack(side="left")

        self._lbl = tk.Label(self, text=self._format(), bg=_bg,
                             fg=Colors.WHITE, font=mc_font(11), width=6)
        self._lbl.pack(side="left", padx=4)

    def _format(self):
        try:
            return self._fmt.format(self._var.get())
        except Exception:
            return str(int(self._var.get()))

    def _on_change(self, val):
        self._lbl.config(text=self._format())
        if self._command:
            self._command(float(val))

    def get(self):
        return self._var.get()

    def set(self, val):
        self._var.set(val)
        self._lbl.config(text=self._format())


# ─────────────────────────────────────────────────────────────────────────────
#  Section Header
# ─────────────────────────────────────────────────────────────────────────────

class SectionHeader(tk.Label):
    """A Minecraft-font section header with a gray separator line below it."""

    def __init__(self, master, text="", size=13, bg=Colors.PANEL_DARK, **kwargs):
        super().__init__(master, text=text, bg=bg,
                         fg=Colors.WHITE, font=mc_font(size),
                         anchor="w", **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftDatePicker
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftDatePicker(tk.Frame):
    """
    A Minecraft-styled date picker using +/- buttons to select Day and Month.
    """
    def __init__(self, master, bg=Colors.PANEL_DARK, **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        
        self.day = tk.IntVar(value=1)
        self.month = tk.IntVar(value=1)

        # Labels
        tk.Label(self, text="Dia", bg=bg, fg=Colors.GRAY_TEXT, font=mc_font(9)).grid(row=0, column=1)
        tk.Label(self, text="Mes", bg=bg, fg=Colors.GRAY_TEXT, font=mc_font(9)).grid(row=0, column=4)

        # Day
        MinecraftButton(self, text="-", width=30, height=30, font_size=14, command=lambda: self._adj_day(-1)).grid(row=1, column=0, padx=(0,4))
        self.lbl_day = tk.Label(self, text="01", bg=bg, fg=Colors.WHITE, font=mc_font(12), width=3)
        self.lbl_day.grid(row=1, column=1)
        MinecraftButton(self, text="+", width=30, height=30, font_size=14, command=lambda: self._adj_day(1)).grid(row=1, column=2, padx=(4,15))

        # Month
        MinecraftButton(self, text="-", width=30, height=30, font_size=14, command=lambda: self._adj_month(-1)).grid(row=1, column=3, padx=(0,4))
        self.lbl_month = tk.Label(self, text="01", bg=bg, fg=Colors.WHITE, font=mc_font(12), width=3)
        self.lbl_month.grid(row=1, column=4)
        MinecraftButton(self, text="+", width=30, height=30, font_size=14, command=lambda: self._adj_month(1)).grid(row=1, column=5, padx=(4,0))

    def _adj_day(self, delta):
        max_days = self._get_max_days(self.month.get())
        new_val = self.day.get() + delta
        if new_val < 1: new_val = max_days
        if new_val > max_days: new_val = 1
        self.day.set(new_val)
        self.lbl_day.config(text=f"{new_val:02d}")

    def _adj_month(self, delta):
        new_val = self.month.get() + delta
        if new_val < 1: new_val = 12
        if new_val > 12: new_val = 1
        self.month.set(new_val)
        self.lbl_month.config(text=f"{new_val:02d}")
        # Adjust day if it exceeds max for new month
        max_days = self._get_max_days(new_val)
        if self.day.get() > max_days:
            self.day.set(max_days)
            self.lbl_day.config(text=f"{max_days:02d}")

    def _get_max_days(self, month):
        if month in [4, 6, 9, 11]: return 30
        if month == 2: return 29 # Allow 29th for birthdays
        return 31

    def get(self):
        """Return birthday in MM-DD format."""
        return f"{self.month.get():02d}-{self.day.get():02d}"

# ─────────────────────────────────────────────────────────────────────────────
#  MinecraftToast
# ─────────────────────────────────────────────────────────────────────────────

class MinecraftToast(tk.Frame):
    """
    A floating notification bar with Minecraft aesthetics.
    """
    def __init__(self, master, text="", subtext="", action_text="Actualizar", 
                 on_action=None, on_close=None, **kwargs):
        super().__init__(master, bg="#1a1a1a", highlightthickness=2, 
                         highlightbackground=Colors.PANEL_BORDER, **kwargs)
        
        self._on_action = on_action
        self._on_close = on_close

        # Content Container
        inner = tk.Frame(self, bg="#1a1a1a", padx=15, pady=10)
        inner.pack(fill="both", expand=True)

        # Icon (Warning icon)
        from PIL import Image, ImageTk
        ico_path = Assets.ICON_WARN
        if os.path.exists(ico_path):
            img = Image.open(ico_path).convert("RGBA").resize((32, 32), Image.NEAREST)
            self._tk_ico = ImageTk.PhotoImage(img)
            tk.Label(inner, image=self._tk_ico, bg="#1a1a1a").pack(side="left", padx=(0, 15))

        # Text Block
        txt_frame = tk.Frame(inner, bg="#1a1a1a")
        txt_frame.pack(side="left", fill="both", expand=True)

        tk.Label(txt_frame, text=text, fg=Colors.YELLOW, bg="#1a1a1a", 
                 font=mc_font(11, bold=True), anchor="w").pack(fill="x")
        if subtext:
            tk.Label(txt_frame, text=subtext, fg=Colors.GRAY_TEXT, bg="#1a1a1a", 
                     font=mc_font(9), anchor="w").pack(fill="x")

        # Buttons
        if on_action:
            MinecraftButton(inner, text=action_text, width=120, height=30, 
                             font_size=10, command=on_action).pack(side="left", padx=10)

        # Close Button (X)
        MinecraftButton(inner, text="X", width=30, height=30, 
                         font_size=10, command=on_close).pack(side="left")

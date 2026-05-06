"""
Minecraft Launcher - Skins View
Shows skin head (real Mojang skin for premium, local skin for no-premium).
Allows upload to Mojang (premium) or local save (no-premium).
"""
import tkinter as tk
import threading
import os
from tkinter import filedialog
from PIL import Image, ImageTk

from ui.theme import Colors, mc_font
from ui.widgets import MinecraftButton, MinecraftPanel, SkinHead, SectionHeader
from config.manager import config
from core.security import decrypt_data


class SkinsView(tk.Frame):

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        self._variant = "classic"
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=Colors.PANEL_DARK,
                          highlightthickness=1,
                          highlightbackground=Colors.PANEL_BORDER,
                          height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        MinecraftButton(header, text="< Volver", width=120, height=34,
                         font_size=10, command=self._go_home).pack(side="left", padx=10, pady=7)
        tk.Label(header, text="Gestor de Skins", fg=Colors.WHITE, bg=Colors.PANEL_DARK,
                 font=mc_font(14)).pack(side="left", padx=20)

        body = tk.Frame(self, bg=Colors.DARK)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        # ── Left: preview ─────────────────────────────────────────────────────
        left = MinecraftPanel(body, width=220)
        left.pack(side="left", fill="y", padx=(0, 20))
        left.pack_propagate(False)

        SectionHeader(left, text="Vista previa", size=11, bg=Colors.PANEL_DARK).pack(
            anchor="w", padx=10, pady=(10, 4))

        self._skin_head = SkinHead(left, size=96, bg=Colors.PANEL_DARK)
        self._skin_head.pack(pady=10)

        self._skin_label_var = tk.StringVar(value="Sin skin")
        tk.Label(left, textvariable=self._skin_label_var,
                 fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(8),
                 wraplength=200, justify="center").pack(padx=6, pady=(0, 6))

        self._full_preview_lbl = tk.Label(left, bg="#111111",
                                           text="Sin skin", fg=Colors.GRAY_TEXT,
                                           font=mc_font(8),
                                           highlightthickness=1,
                                           highlightbackground=Colors.PANEL_BORDER)
        self._full_preview_lbl.pack(padx=10, pady=4)

        # Refresh skin info on open
        self._refresh_preview()

        # ── Right: controls ───────────────────────────────────────────────────
        right = MinecraftPanel(body)
        right.pack(side="left", fill="both", expand=True)

        auth_type = config.get("auth_type") or "nopremium"
        is_premium = auth_type == "premium"

        # ── Section: Skin Gallery ─────────────────────────────────────────────
        SectionHeader(right, text="Galería de Skins", size=11, bg=Colors.PANEL_DARK).pack(
            anchor="w", padx=14, pady=(10, 4))

        gallery_row = tk.Frame(right, bg=Colors.PANEL_DARK)
        gallery_row.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # Scrollbar and Canvas for custom list
        self._gallery_canvas = tk.Canvas(gallery_row, bg=Colors.DARK, highlightthickness=1, highlightbackground=Colors.PANEL_BORDER)
        scroll = tk.Scrollbar(gallery_row, orient="vertical", command=self._gallery_canvas.yview)
        
        self._gallery_inner = tk.Frame(self._gallery_canvas, bg=Colors.DARK)
        self._gallery_canvas.create_window((0, 0), window=self._gallery_inner, anchor="nw", width=self._gallery_canvas.winfo_width())
        self._gallery_canvas.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side="right", fill="y")
        self._gallery_canvas.pack(side="left", fill="both", expand=True)

        def _on_inner_resize(e):
            self._gallery_canvas.configure(scrollregion=self._gallery_canvas.bbox("all"))
        def _on_canvas_resize(e):
            self._gallery_canvas.itemconfig(1, width=e.width) # Update inner frame width

        self._gallery_inner.bind("<Configure>", _on_inner_resize)
        self._gallery_canvas.bind("<Configure>", _on_canvas_resize)
        
        self._gallery_items = []

        # Gallery Buttons
        btn_col = tk.Frame(gallery_row, bg=Colors.PANEL_DARK)
        btn_col.pack(side="left", fill="y", padx=(10, 0))

        MinecraftButton(btn_col, text="+ Agregar", width=110, height=30,
                         font_size=9, command=self._pick_skin_file).pack(pady=(0, 6))
        MinecraftButton(btn_col, text="- Eliminar", width=110, height=30,
                         font_size=9, command=self._remove_selected_skin).pack(pady=(0, 6))

        # Options
        var_row = tk.Frame(right, bg=Colors.PANEL_DARK)
        var_row.pack(padx=14, pady=2, anchor="w")
        tk.Label(var_row, text="Modelo:", fg=Colors.GRAY_TEXT,
                 bg=Colors.PANEL_DARK, font=mc_font(10)).pack(side="left")
        MinecraftButton(var_row, text="Classic", width=100, height=26,
                         font_size=9,
                         command=lambda: self._set_variant("classic")).pack(side="left", padx=4)
        MinecraftButton(var_row, text="Slim (Alex)", width=120, height=26,
                         font_size=9,
                         command=lambda: self._set_variant("slim")).pack(side="left", padx=4)

        if is_premium:
            hint = "Premium: Seleccionar una skin la sincronizará automáticamente con Mojang."
            # Also keep manual fetch button
            MinecraftButton(var_row, text="Sync Mojang", width=130, height=26,
                             font_size=9, command=self._fetch_premium_skin).pack(side="left", padx=10)
        else:
            hint = "No-Premium: Seleccionar una skin la activará localmente para tu perfil."

        tk.Label(right, text=hint, fg=Colors.GRAY_TEXT,
                 bg=Colors.PANEL_DARK, font=mc_font(9),
                 wraplength=400, justify="left").pack(anchor="w", padx=14, pady=(6, 6))

        self._status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(right, textvariable=self._status_var,
                                     fg=Colors.PREMIUM_GREEN, bg=Colors.PANEL_DARK,
                                     font=mc_font(10), wraplength=420)
        self._status_lbl.pack(padx=14, pady=4)

        # ── Setup explicit equip button ───────────────────────────────────────
        act_row = tk.Frame(right, bg=Colors.PANEL_DARK)
        act_row.pack(padx=14, pady=(0, 6))

        btn_text = "Equipar y Subir a Mojang" if is_premium else "Equipar y Sincronizar"
        MinecraftButton(act_row, text=btn_text, width=240, height=36, font_size=10,
                        command=self._equip_selected).pack(side="left")

        # ── Section: 3D Viewer ────────────────────────────────────────────────
        SectionHeader(right, text="Visor 3D", size=11, bg=Colors.PANEL_DARK).pack(
            anchor="w", padx=14, pady=(10, 4))

        MinecraftButton(right, text="Abrir Visor 3D de Skin",
                         width=260, height=40, font_size=12,
                         command=self._open_3d_viewer).pack(padx=14, pady=(0, 10))

        # Initialize Gallery
        self._load_gallery()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _load_gallery(self):
        for widget in self._gallery_inner.winfo_children():
            widget.destroy()

        self._gallery_items = []
        saved = config.get("saved_skins") or []
        for path in saved:
            row = tk.Frame(self._gallery_inner, bg=Colors.DARK, cursor="hand2", padx=4, pady=4)
            row.pack(fill="x", pady=1)
            
            # Head thumbnail
            head = SkinHead(row, size=32, bg=Colors.DARK)
            head.pack(side="left", padx=(4, 10))
            head.set_skin(path)
            
            name = os.path.basename(path)
            lbl = tk.Label(row, text=name, bg=Colors.DARK, fg=Colors.WHITE, font=mc_font(9), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            
            # Bind clicks (single click to preview/select, double to equip/sync)
            def on_single_click(e, p=path):
                self._on_gallery_single_click(p)
            
            def on_double_click(e, p=path):
                self._on_gallery_single_click(p)
                self._equip_selected()
                
            for w in (row, head, lbl):
                w.bind("<Button-1>", on_single_click)
                w.bind("<Double-Button-1>", on_double_click)
                
            self._gallery_items.append((path, row, head, lbl))
            
        self._highlight_selected()

    def _highlight_selected(self):
        current = config.get("skin_path")
        for path, row, head, lbl in self._gallery_items:
            color = Colors.ACCENT if path == current else Colors.DARK
            row.config(bg=color)
            head.config(bg=color)
            lbl.config(bg=color)

    def _on_gallery_single_click(self, path):
        config.set("skin_path", path)
        self._highlight_selected()
        self._refresh_preview()
        
        # Para No-Premium, intentamos sincronizar al seleccionar para que sea más intuitivo
        auth_type = config.get("auth_type")
        if auth_type != "premium":
            self._equip_selected()
        else:
            self._status("Skin seleccionada. Presiona 'Equipar' para subir a Mojang.", Colors.GRAY_TEXT)

    def _equip_selected(self):
        path = config.get("skin_path")
        if not path or not os.path.exists(path):
            self._status("Primero selecciona una skin de la coleccion.", Colors.NOPREMIUM_RED)
            return

        auth_type = config.get("auth_type")
        if auth_type == "premium":
            self._upload_skin_path(path)
        else:
            # No-Premium: Equip local and ALSO upload to Backend
            self._status("Equipando y sincronizando con el servidor...", Colors.GRAY_TEXT)
            
            def do_upload():
                import base64
                try:
                    with open(path, "rb") as f:
                        b64_data = base64.b64encode(f.read()).decode("utf-8")
                    
                    # We need the player token (JWT)
                    token = config.get("player_token")
                    if not token:
                        self.after(0, lambda: self._status("Inicia sesion en 'Servidor' para sincronizar skin.", Colors.NOPREMIUM_RED))
                        return
                    
                    from core.auth import AuthController
                    auth = AuthController()
                    res = auth.update_skin_no_premium(token, skin_base64=b64_data)
                    
                    if res["status"] == "OK":
                        self.after(0, lambda: self._status("Skin sincronizada con éxito!", Colors.PREMIUM_GREEN))
                    else:
                        self.after(0, lambda: self._status(f"Error sincronizando: {res['message']}", Colors.NOPREMIUM_RED))
                except Exception as e:
                    self.after(0, lambda: self._status(f"Error: {e}", Colors.NOPREMIUM_RED))

            threading.Thread(target=do_upload, daemon=True).start()

    def _pick_skin_file(self):
        path = filedialog.askopenfilename(
            title="Selecciona tu skin (.png)",
            filetypes=[("PNG", "*.png"), ("Todos", "*")]
        )
        if not path:
            return
        saved = config.get("saved_skins") or []
        if path not in saved:
            saved.append(path)
            config.set("saved_skins", saved)
        
        self._load_gallery()
        
        # Select and preview it
        self._on_gallery_single_click(path)

    def _set_variant(self, v):
        self._variant = v
        self._status(f"Modelo seleccionado: {v}", Colors.GRAY_TEXT)

    def _remove_selected_skin(self):
        current = config.get("skin_path")
        saved = config.get("saved_skins") or []
        if current in saved:
            saved.remove(current)
            config.set("saved_skins", saved)
            config.set("skin_path", "")
            self._load_gallery()
            self._refresh_preview()
            self._status("Skin eliminada.", Colors.GRAY_TEXT)
        else:
            self._status("Selecciona una skin con un clic primero para eliminarla.", Colors.NOPREMIUM_RED)

    def _upload_skin_path(self, skin_path):
        if not skin_path or not os.path.exists(skin_path):
            self._status("Archivo de skin no encontrado.", Colors.NOPREMIUM_RED)
            return

        encrypted = config.get("auth_token") or ""
        access_token = decrypt_data(encrypted) if encrypted else ""
        if not access_token:
            self._status("Token de acceso inválido. Vuelve a iniciar sesión (Premium).", Colors.NOPREMIUM_RED)
            return

        self._status("Sincronizando skin de la galería con Mojang...", Colors.GRAY_TEXT)

        def do_upload():
            from core.skin_fetch import upload_skin_to_mojang
            result = upload_skin_to_mojang(skin_path, access_token, self._variant)
            color = Colors.PREMIUM_GREEN if result["status"] == "OK" else Colors.NOPREMIUM_RED
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self._status(result["message"], color))
                    if result["status"] == "OK":
                        self.after(2000, lambda: self._fetch_premium_skin(force=True))
            except Exception:
                pass

        threading.Thread(target=do_upload, daemon=True).start()

    def _fetch_premium_skin(self, force=False):
        """Fetch the current Mojang skin for this premium account into local cache."""
        uuid = config.get("uuid") or ""
        if not uuid:
            self._status("No hay UUID registrado. Re-inicia sesión.", Colors.NOPREMIUM_RED)
            return

        self._status("Descargando skin actual de Mojang...", Colors.GRAY_TEXT)

        def on_done(path):
            if path:
                config.set("skin_path", path)
                self.after(0, lambda: self._refresh_preview())
                self.after(0, lambda: self._status("Skin sincronizada desde Mojang.", Colors.PREMIUM_GREEN))
            else:
                self.after(0, lambda: self._status("No se pudo obtener skin de Mojang.", Colors.NOPREMIUM_RED))

        from core.skin_fetch import fetch_skin_from_mojang
        fetch_skin_from_mojang(uuid, on_done, force=force)

    def _open_3d_viewer(self):
        try:
            from core.skin_viewer_app import SkinViewer3DApp
            viewer = SkinViewer3DApp()
            viewer.run_in_window(self)
        except Exception as e:
            self._status(f"Error al abrir visor 3D: {e}", Colors.NOPREMIUM_RED)

    def _refresh_preview(self):
        skin_path = config.get("skin_path") or ""
        if os.path.exists(skin_path):
            self._skin_head.set_skin(skin_path)
            self._skin_label_var.set(os.path.basename(skin_path))
            try:
                img = Image.open(skin_path).convert("RGBA")
                w = min(int(img.width * 3), 192)
                h = int(img.height * 3)
                if w > 192:
                    ratio = 192 / w
                    w, h = 192, int(h * ratio)
                self._tk_skin_preview = ImageTk.PhotoImage(img.resize((w, h), Image.NEAREST))
                self._full_preview_lbl.config(image=self._tk_skin_preview, text="")
            except Exception:
                self._full_preview_lbl.config(image="", text="Error")
        else:
            self._skin_head.set_skin(None)
            self._skin_label_var.set("Sin skin")
            self._full_preview_lbl.config(image="", text="Sin skin")

    def _status(self, msg, color=Colors.PREMIUM_GREEN):
        self._status_var.set(msg)
        self._status_lbl.config(fg=color)

    def _go_home(self):
        if self.app:
            self.app.show_home_view()

    def on_show(self):
        """Called when the view becomes visible — auto-refresh."""
        self._refresh_preview()
        self._load_gallery()
        
        # Auto-sync on open if premium and hasn't synced yet
        if config.get("auth_type") == "premium":
            if not getattr(self, "_has_synced_mojang", False):
                self._fetch_premium_skin()
                self._has_synced_mojang = True

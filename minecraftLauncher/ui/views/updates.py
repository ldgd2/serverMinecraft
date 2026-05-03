"""
Vista de Actualizaciones del Launcher.
Muestra la versión actual, permite buscar actualizaciones manualmente
y presenta una barra de progreso animada durante la descarga.
"""
import tkinter as tk
from tkinter import ttk
import threading

from config.manager import config
from ui.theme import Colors, mc_font
from ui.widgets import PanoramaBackground, MinecraftButton, MinecraftLabel, MinecraftPanel
from core.info import VERSION, APP_NAME


class UpdatesView(tk.Frame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        self._checking = False

        # Background
        self.bg = PanoramaBackground(self, overlay_alpha=210, bg=Colors.DARK)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        MinecraftLabel(self.bg, text="Actualizaciones", size=24, color=Colors.WHITE, shadow=True).place(
            relx=0.5, y=30, anchor="n"
        )

        # Main panel
        panel = MinecraftPanel(self.bg)
        panel.place(relx=0.15, rely=0.14, relwidth=0.7, relheight=0.72)

        # ── Version card ──────────────────────────────────────────────────────
        card = tk.Frame(panel, bg=Colors.PANEL_BORDER, bd=0)
        card.pack(fill="x", padx=30, pady=(30, 0))

        inner = tk.Frame(card, bg=Colors.PANEL_DARK)
        inner.pack(fill="x", padx=2, pady=2)

        tk.Label(inner, text="Versión instalada", font=mc_font(9),
                 fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK).pack(pady=(14, 0))
        tk.Label(inner, text=f"v{VERSION}", font=mc_font(22, bold=True),
                 fg=Colors.PREMIUM_GREEN, bg=Colors.PANEL_DARK).pack()
        tk.Label(inner, text=APP_NAME, font=mc_font(10),
                 fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK).pack(pady=(0, 14))

        # ── Status label ─────────────────────────────────────────────────────
        self.status_lbl = tk.Label(
            panel,
            text="Haz clic en 'Buscar actualizaciones' para verificar.",
            font=mc_font(10), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK,
            wraplength=500, justify="center"
        )
        self.status_lbl.pack(pady=(20, 6))

        # ── Progress bar (hidden until download) ─────────────────────────────
        prog_frame = tk.Frame(panel, bg=Colors.PANEL_DARK)
        prog_frame.pack(fill="x", padx=50)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("MC.Horizontal.TProgressbar",
                        troughcolor=Colors.PANEL_BORDER,
                        background=Colors.PREMIUM_GREEN,
                        thickness=14)

        self.progress = ttk.Progressbar(
            prog_frame, style="MC.Horizontal.TProgressbar",
            orient="horizontal", mode="determinate"
        )
        # Hidden by default — shown when downloading
        self._progress_frame = prog_frame

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_frame = tk.Frame(panel, bg=Colors.PANEL_DARK)
        btn_frame.pack(pady=24)

        self.check_btn = MinecraftButton(
            btn_frame,
            text="🔍  Buscar actualizaciones",
            width=240, height=42, font_size=12,
            command=self._do_check
        )
        self.check_btn.pack(side="left", padx=8)

        MinecraftButton(
            btn_frame,
            text="← Volver",
            width=140, height=42, font_size=12,
            command=self._go_back
        ).pack(side="left", padx=8)

        # ── Changelog area ────────────────────────────────────────────────────
        tk.Label(panel, text="Historial", font=mc_font(11, bold=True),
                 fg=Colors.WHITE, bg=Colors.PANEL_DARK).pack(anchor="w", padx=30, pady=(10, 4))

        self.changelog_text = tk.Text(
            panel,
            height=5, bg=Colors.DARK, fg=Colors.GRAY_TEXT,
            font=mc_font(9), relief="flat",
            padx=12, pady=10, state="disabled", wrap="word"
        )
        self.changelog_text.pack(fill="x", padx=30, pady=(0, 10))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, text: str, color=None):
        self.status_lbl.config(text=text, fg=color or Colors.GRAY_TEXT)

    def _set_changelog(self, text: str):
        self.changelog_text.config(state="normal")
        self.changelog_text.delete("1.0", "end")
        self.changelog_text.insert("end", text or "Sin novedades.")
        self.changelog_text.config(state="disabled")

    def _show_progress(self):
        self.progress.pack(fill="x", pady=(4, 0))

    def _hide_progress(self):
        self.progress.pack_forget()
        self.progress["value"] = 0

    def _set_progress(self, value: int):
        self.progress["value"] = value
        self.update_idletasks()

    # ── Check for updates ─────────────────────────────────────────────────────

    def _do_check(self):
        if self._checking:
            return
        self._checking = True
        self.check_btn.set_text("Verificando...")
        self._set_status("Consultando servidor de actualizaciones...", Colors.YELLOW)
        self._hide_progress()
        threading.Thread(target=self._check_worker, daemon=True).start()

    def _check_worker(self):
        try:
            from core.updater import check_for_update, LAUNCHER_VERSION
            info = check_for_update(silent=False)
        except Exception as e:
            self.after(0, lambda: self._on_check_error(str(e)))
            return

        self.after(0, lambda: self._on_check_done(info))

    def _on_check_error(self, err: str):
        self._checking = False
        self.check_btn.set_text("Buscar actualizaciones")
        self._set_status(f"No se pudo conectar al servidor.\n{err}", Colors.RED if hasattr(Colors, 'RED') else "#e05252")

    def _on_check_done(self, info):
        self._checking = False
        self.check_btn.set_text("Buscar actualizaciones")

        if not info:
            self._set_status("✓  ¡Ya tienes la última versión!", Colors.PREMIUM_GREEN)
            self._set_changelog("Tu launcher está completamente actualizado.")
            return

        latest  = info.get("latest_version", "?")
        url     = info.get("download_url", "")

        self._set_status(
            f"Nueva versión disponible: v{latest}\n"
            f"Tu versión actual: v{info.get('current_version', VERSION)}",
            Colors.YELLOW
        )
        self._set_changelog(f"Versión {latest} lista para descargar.")

        if url:
            # Show download button
            self._show_download_option(latest, url)

    def _show_download_option(self, latest: str, url: str):
        """Muestra el botón de descarga y la barra de progreso."""
        # Reemplaza el texto del check button temporalmente
        self.check_btn.set_text(f"⬇  Descargar v{latest}")
        self.check_btn.config(command=lambda: self._do_download(url))

    def _do_download(self, url: str):
        self.check_btn.set_text("Descargando...")
        self.check_btn.config(state="disabled")
        self._show_progress()
        self._set_status("Descargando actualización...", Colors.YELLOW)
        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    def _download_worker(self, url: str):
        try:
            from core.updater import _UpdateWindow
            # Reutilizamos la ventana animada del updater
            root = self.winfo_toplevel()
            self.after(0, lambda: _UpdateWindow(
                root,
                latest_version="?",
                download_url=url,
                on_complete=None,
                on_cancel=lambda: self.after(0, self._reset_btn)
            ))
        except Exception as e:
            self.after(0, lambda: self._on_check_error(str(e)))

    def _reset_btn(self):
        self.check_btn.set_text("Buscar actualizaciones")
        self.check_btn.config(state="normal", command=self._do_check)
        self._hide_progress()

    def _go_back(self):
        if self.app:
            self.app.show_home_view()

    def on_show(self):
        pass

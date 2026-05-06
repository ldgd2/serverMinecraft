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
        self._progress_frame = prog_frame

        # Barra de progreso custom (Contenedor con borde)
        self.prog_container = tk.Frame(prog_frame, bg=Colors.PANEL_BORDER, height=24)
        self.prog_container.pack_propagate(False)
        
        # El fondo de la barra (Negro Minecraft)
        self.prog_bg = tk.Frame(self.prog_container, bg="#000000")
        self.prog_bg.pack(fill="both", expand=True, padx=2, pady=2)
        self.prog_bg.pack_propagate(False)

        # La barra verde
        self.prog_bar = tk.Frame(self.prog_bg, bg=Colors.PREMIUM_GREEN)
        self.prog_bar.place(relx=0, rely=0, relwidth=0, relheight=1)
        
        # Alias para compatibilidad
        self.progress = self.prog_container
        self._progress_bar_internal = self.prog_bar

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
        self._progress_bar_internal.config(width=0)

    def _set_progress(self, value: int):
        # Usamos relwidth para que sea independiente del ancho en píxeles
        pct = value / 100.0
        self._progress_bar_internal.place(relx=0, rely=0, relwidth=pct, relheight=1)
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
            from core.updater import check_for_update, check_for_mod_update, LAUNCHER_VERSION
            l_info = check_for_update(silent=False)
            m_info = check_for_mod_update(silent=False)
        except Exception as e:
            self.after(0, lambda: self._on_check_error(str(e)))
            return

        self.after(0, lambda: self._on_check_done(l_info, m_info))

    def _on_check_error(self, err: str):
        self._checking = False
        self.check_btn.set_text("Buscar actualizaciones")
        self._set_status(f"No se pudo conectar al servidor.\n{err}", Colors.NOPREMIUM_RED)

    def _on_check_done(self, l_info, m_info):
        self._checking = False
        self.check_btn.set_text("Buscar actualizaciones")

        if not l_info and not m_info:
            self._set_status("✓  ¡Todo está actualizado!", Colors.PREMIUM_GREEN)
            self._set_changelog("Tu launcher y mods están en la última versión.")
            return

        status_text = ""
        changelog_text = ""
        download_data = {}

        if l_info:
            latest = l_info.get("latest_version", "?")
            status_text += f"Launcher: v{VERSION} → v{latest}\n"
            changelog_text += f"• Launcher v{latest} disponible.\n"
            download_data["launcher"] = l_info

        if m_info:
            latest = m_info.get("latest_version", "?")
            current = config.get("minebridge_mod_version", "0.0.0")
            status_text += f"Mods: v{current} → v{latest}\n"
            changelog_text += f"• Mods v{latest} disponibles.\n"
            download_data["mods"] = m_info

        self._set_status(status_text.strip(), Colors.YELLOW)
        self._set_changelog(changelog_text.strip())

        if download_data:
            self._show_download_option(download_data)

    def _show_download_option(self, download_data: dict):
        """Muestra el botón de descarga para lo que esté pendiente."""
        txt = "⬇  Descargar todo" if len(download_data) > 1 else f"⬇  Descargar {'Launcher' if 'launcher' in download_data else 'Mods'}"
        self.check_btn.set_text(txt)
        self.check_btn.set_command(lambda: self._do_download_all(download_data))

    def _do_download_all(self, download_data: dict):
        self.check_btn.set_text("Descargando...")
        self.check_btn.configure_state(True)
        self._show_progress()
        self._set_status("Iniciando descargas...", Colors.YELLOW)
        
        threading.Thread(target=self._download_all_worker, args=(download_data,), daemon=True).start()

    def _download_all_worker(self, download_data: dict):
        try:
            import requests
            from core.updater import download_and_install_launcher, install_mod_update
            
            def _update_prog(pct):
                self.after(0, lambda: self._set_progress(pct))
                
            def _update_status(txt):
                self.after(0, lambda: self._set_status(txt, Colors.YELLOW))

            # 1. Preparar lista de tareas con tamaños para ordenar
            tasks = []
            for key, info in download_data.items():
                url = info.get("download_url")
                if not url: continue
                
                # Intentar obtener tamaño real
                size = info.get("size_bytes")
                if not size:
                    try:
                        r = requests.head(url, timeout=5, allow_redirects=True)
                        size = int(r.headers.get("content-length", 0))
                    except: size = 999999999 # Fallback pesado si falla el head
                
                tasks.append({
                    "type": key,
                    "url": url,
                    "version": info.get("latest_version", "?"),
                    "size": size
                })

            # 2. Ordenar: Mods primero (prioridad 0), Launcher al final (prioridad 1)
            # Dentro de la misma categoría, el más liviano primero.
            def _sort_key(x):
                priority = 0 if x["type"] == "mods" else 1
                return (priority, x["size"])
            
            tasks.sort(key=_sort_key)

            # 3. Ejecutar en orden
            for task in tasks:
                self.after(0, self._hide_progress) # Reset bar
                self.after(100, self._show_progress)
                
                # Extraer nombre de archivo limpio de la URL
                filename = task["url"].split("/")[-1].split("?")[0]
                if not filename: filename = "archivo_descarga"
                
                # Función para formatear el estado: "$nombre           $descargado/$total"
                def _update_formatted_status(mb_txt):
                    # Usamos padding para empujar el tamaño a la derecha
                    combined = f"{filename:<30} {mb_txt}"
                    # Forzamos fuente Courier para alineación perfecta durante descarga
                    self.after(0, lambda: self.status_lbl.config(font=("Courier", 10)))
                    self.after(0, lambda: self._set_status(combined, Colors.YELLOW))

                if task["type"] == "mods":
                    _update_formatted_status("Conectando...")
                    success = install_mod_update(
                        task["url"], task["version"],
                        progress_callback=_update_prog,
                        status_callback=_update_formatted_status
                    )
                    if not success:
                        raise Exception("Error durante la instalación de los mods.")
                
                elif task["type"] == "launcher":
                    _update_formatted_status("Conectando...")
                    success = download_and_install_launcher(
                        task["url"],
                        progress_callback=_update_prog,
                        status_callback=_update_formatted_status
                    )
                    if not success:
                        raise Exception("Error durante la actualización del Launcher.")
                    
                    # Asegurar que la barra se vea llena al 100% mientras se prepara el cierre
                    self.after(0, lambda: self._set_progress(100))
                    self.after(0, self._show_progress)
                
            self.after(0, lambda: self._set_status("✓ ¡Todo completado con éxito!", Colors.PREMIUM_GREEN))
            self.after(0, lambda: self.check_btn.set_text("✓ Finalizado"))

        except Exception as e:
            err_msg = f"Error: {str(e)}"
            self.after(0, lambda: self._set_status(err_msg, Colors.NOPREMIUM_RED))
            self.after(0, lambda: self.check_btn.set_text("Reintentar"))
            self.after(0, lambda: self.check_btn.configure_state(False))
            print(f"[Updates] Worker error: {e}")
            self.after(0, lambda: self.check_btn.set_text("Cerrar"))
            self.after(0, lambda: self.check_btn.configure_state(False))
            self.after(0, self._hide_progress)

        except Exception as e:
            self.after(0, lambda: self._on_check_error(str(e)))

    def _on_download_failed(self):
        self.check_btn.configure_state(False)
        self.check_btn.set_text("Reintentar descarga")
        self._set_status("Error al descargar la actualización.", Colors.RED if hasattr(Colors, 'RED') else "#e05252")

    def _reset_btn(self):
        self.check_btn.set_text("Buscar actualizaciones")
        self.check_btn.config(state="normal", command=self._do_check)
        self._hide_progress()

    def _go_back(self):
        if self.app:
            self.app.show_home_view()

    def trigger_auto_update(self, latest, url):
        """Inicia la descarga automáticamente al detectar un update crítico del launcher."""
        data = {
            "launcher": {
                "latest_version": latest,
                "download_url": url
            }
        }
        self._set_status(f"Nueva versión v{latest} detectada.", Colors.YELLOW)
        self.after(1000, lambda: self._do_download_all(data))

    def trigger_mod_update(self, latest, url):
        """Inicia la descarga de mods automáticamente al aceptar el aviso."""
        data = {
            "mods": {
                "latest_version": latest,
                "download_url": url
            }
        }
        self._set_status(f"Nuevos mods v{latest} detectados.", Colors.YELLOW)
        self.after(1000, lambda: self._do_download_all(data))

    def on_show(self):
        # Al mostrar, podemos limpiar estados previos si se desea
        pass

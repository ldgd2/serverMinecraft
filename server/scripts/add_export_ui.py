import os

settings_path = 'minecraftLauncher/ui/views/settings.py'
with open(settings_path, 'r', encoding='utf-8') as f:
    content = f.read()

download_logic = """
    def _download_world_backup(self):
        import requests
        import threading
        from tkinter import filedialog, messagebox

        server_name = config.get("server_name", "Lider Server")
        api_url = config.get("api_url", "").rstrip("/")
        
        if not api_url:
            messagebox.showerror("Error", "URL API Skins no configurada. No se puede conectar al servidor.")
            return
            
        # The backend API might be structured as base_url/servers/{server_name}/world/export
        # Let's adjust to the standard base
        # If api_url is http://192.168.1.5/api/v1
        base_url = api_url.split("/api")[0] + "/api/v1"
        url = f"{base_url}/servers/{server_name}/world/export"
        
        save_path = filedialog.asksaveasfilename(
            title="Guardar Backup del Mundo",
            initialfile=f"{server_name}_world.zip",
            defaultextension=".zip",
            filetypes=[("Archivos ZIP", "*.zip")]
        )
        
        if not save_path:
            return
            
        def do_download():
            try:
                self.after(0, lambda: self.save_btn.set_text("Descargando..."))
                
                # Fetch token if auth_type is premium/server to authenticate request
                headers = {}
                token = config.get("player_token", "")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    
                response = requests.get(url, stream=True, timeout=30, headers=headers)
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.after(0, lambda: messagebox.showinfo("Éxito", f"Mundo descargado en: {save_path}"))
                self.after(0, lambda: self.save_btn.set_text("Guardar Cambios"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Fallo al descargar: {e}"))
                self.after(0, lambda: self.save_btn.set_text("Guardar Cambios"))

        threading.Thread(target=do_download, daemon=True).start()
"""

button_code = """
            btn_download = MinecraftButton(frame, text="Descargar Mundo del Servidor", width=340, height=36, font_size=11, command=self._download_world_backup)
            btn_download.pack(anchor="w", pady=(10, 5))
"""

if "_download_world_backup" not in content:
    content = content.replace("    def _build_avanzado_tab(self):", download_logic.lstrip() + "\n    def _build_avanzado_tab(self):")
    content = content.replace('self.inputs["auth_api_url"].pack(fill="x", pady=5)', 'self.inputs["auth_api_url"].pack(fill="x", pady=5)\n' + button_code)
    
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added download logic to settings.py')
else:
    print('Logic already exists in settings.py')

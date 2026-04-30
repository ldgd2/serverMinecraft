import webview
import sys
import os
import base64

from config.manager import config
from core.paths import get_resource_path

class SkinViewer3DApp:
    def __init__(self):
        self.window = None
        
    def run_in_window(self, parent_view=None):
        skin_path = config.get("skin_path")
        variant = config.get("skin_variant", "classic")
        
        if not skin_path or not os.path.exists(skin_path):
            if parent_view and hasattr(parent_view, "_status"):
                parent_view._status("Primero selecciona una skin.", "#F44336")
            else:
                print("No skin path configured.")
            return
            
        # Load local skinview3d js safely
        js_path = get_resource_path(os.path.join("core", "skinview3d.bundle.js"))
        js_content = ""
        if os.path.exists(js_path):
            with open(js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
                
        # Convert local skin to Base64
        with open(skin_path, "rb") as f:
            skin_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode('utf-8')
        
        html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Visualizador 3D - {os.path.basename(skin_path)}</title>
        <style>
            body {{ 
                margin: 0; padding: 0; 
                background: #1a1a1a; 
                overflow: hidden; 
            }}
            #canvas {{ width: 100vw; height: 100vh; }}
            
            #controls {{ 
                position: absolute; top: 10px; left: 10px; z-index: 10; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                display: flex; flex-direction: column; gap: 8px; 
                background: rgba(30, 30, 30, 0.7); padding: 12px; 
                border-radius: 2px; border: 2px solid #555;
                box-shadow: inset -2px -2px 0px rgba(0,0,0,0.5), inset 2px 2px 0px rgba(255,255,255,0.2);
            }}
            
            .row {{ display: flex; gap: 5px; justify-content: space-between; }}
            .control-group {{ display: flex; align-items: center; gap: 8px; color: #eee; font-size: 13px; font-weight: bold; margin-top: 5px; text-shadow: 1px 1px 0 #000; }}
            
            button {{ 
                background: #3c3f41; color: #fff; border: 2px solid #555; 
                border-bottom-color: #111; border-right-color: #111;
                border-top-color: #777; border-left-color: #777;
                padding: 8px 12px; cursor: pointer; 
                font-weight: bold; font-size: 12px; text-shadow: 1px 1px 0 #000;
                flex: 1;
            }}
            button:hover {{ background: #4a4d4f; border-bottom-color: #222; border-right-color: #222; }}
            button:active {{ 
                border-top-color: #111; border-left-color: #111; 
                border-bottom-color: #777; border-right-color: #777; 
            }}

            input[type="range"] {{ cursor: pointer; opacity: 0.9; width: 100%; }}
            input[type="checkbox"] {{ cursor: pointer; transform: scale(1.2); }}
        </style>
        
        <script>{js_content}</script>
    </head>
    <body>
        <div id="controls">
            <div class="row">
                <button onclick="setAnimation('walk')">Caminar</button>
                <button onclick="setAnimation('run')">Correr</button>
                <button onclick="setAnimation('idle')">Parado</button>
            </div>
            
            <div class="control-group">
                <label style="min-width: 65px;">Velocidad:</label>
                <input type="range" id="speed" min="0.1" max="3" step="0.1" value="1" oninput="updateSpeed(this.value)">
                <span id="speed_val" style="min-width: 25px;">1.0x</span>
            </div>

            <div class="control-group">
                <input type="checkbox" id="autorotate" checked onchange="toggleAutoRotate(this.checked)">
                <label for="autorotate">Auto-Rotar Cámara</label>
            </div>
        </div>
        
        <canvas id="canvas"></canvas>

        <script>
            const skinViewer = new skinview3d.SkinViewer({{
                canvas: document.getElementById("canvas"),
                width: window.innerWidth,
                height: window.innerHeight,
                skin: "{skin_b64}",
                alpha: true
            }});

            skinViewer.controls.enableRotate = true;
            skinViewer.controls.enableZoom = true;
            skinViewer.controls.autoRotate = true;
            skinViewer.controls.autoRotateSpeed = 0.5;
            
            let currentAnimObject = null; 

            function resetPlayerPose(player) {{
                if (!player) return;
                try {{
                    if (player.rightArm) player.rightArm.rotation.set(0, 0, 0);
                    if (player.leftArm) player.leftArm.rotation.set(0, 0, 0);
                    if (player.rightLeg) player.rightLeg.rotation.set(0, 0, 0);
                    if (player.leftLeg) player.leftLeg.rotation.set(0, 0, 0);
                    if (player.head) player.head.rotation.set(0, 0, 0);
                    if (player.body) player.body.rotation.set(0, 0, 0);
                    if (player.position) player.position.set(0, 0, 0);
                }} catch(e) {{ }}
            }}

            function applyAnimation(AnimInput) {{
                if (skinViewer.animations && typeof skinViewer.animations.add === 'function') {{
                    return skinViewer.animations.add(AnimInput);
                }} else {{
                    let animInstance = typeof AnimInput === 'function' ? new AnimInput() : AnimInput;
                    skinViewer.animation = animInstance;
                    return animInstance;
                }}
            }}

            function clearAnimations() {{
                if (skinViewer.animations) {{
                    if (typeof skinViewer.animations.removeAll === 'function') skinViewer.animations.removeAll();
                    else if (typeof skinViewer.animations.clear === 'function') skinViewer.animations.clear();
                }}
                skinViewer.animation = null;
            }}

            function setAnimation(type) {{
                try {{ clearAnimations(); }} catch(e) {{}}
                resetPlayerPose(skinViewer.playerObject);

                if (type === 'walk') {{
                    currentAnimObject = applyAnimation(skinview3d.WalkingAnimation);
                }} else if (type === 'run') {{
                    currentAnimObject = applyAnimation(skinview3d.RunningAnimation);
                }} else if (type === 'idle') {{
                    currentAnimObject = null;
                }}

                updateSpeed(document.getElementById('speed').value);
            }}

            function updateSpeed(val) {{
                document.getElementById('speed_val').innerText = parseFloat(val).toFixed(1) + 'x';
                if (currentAnimObject && typeof currentAnimObject.speed !== 'undefined') {{
                    currentAnimObject.speed = parseFloat(val);
                }}
            }}

            function toggleAutoRotate(checked) {{
                if (skinViewer.controls) skinViewer.controls.autoRotate = checked;
            }}

            function animate() {{
                requestAnimationFrame(animate);
                if (typeof skinViewer.render === 'function') skinViewer.render();
            }}
            animate();
            
            setAnimation('walk');

            window.addEventListener('resize', () => {{
                skinViewer.width = window.innerWidth;
                skinViewer.height = window.innerHeight;
            }});
        </script>
    </body>
    </html>
    """
    
        # Enable borderless/overlay style if requested
        self.window = webview.create_window('Skin 3D Viewer', html=html_content, width=450, height=450)
        
        def on_loaded():
            try:
                hwnd = self.window.native.Handle.ToInt32()
                with open("tmp_3d_hwnd.txt", "w") as f:
                    f.write(str(hwnd))
            except Exception:
               if "tmp_3d_hwnd.txt" in os.listdir(): os.remove("tmp_3d_hwnd.txt")
        self.window.events.loaded += on_loaded
        webview.start()

if __name__ == "__main__":
    app = SkinViewer3DApp()
    app.run_in_window()
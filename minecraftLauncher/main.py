import ctypes
import sys
from ui.app import LauncherApp

def main():
    # Fix blurry UI on High DPI Windows screens
    if sys.platform == "win32":
        try:
            # SetProcessDpiAwareness(1) -> PROCESS_SYSTEM_DPI_AWARE
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    # Initialize main application
    app = LauncherApp()
    
    # Run the event loop
    app.mainloop()

if __name__ == "__main__":
    main()

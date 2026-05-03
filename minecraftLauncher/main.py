import ctypes
import sys
from ui.app import LauncherApp

def main():
    # Fix blurry UI on High DPI Windows screens
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    # Initialize main application first (needed for tkinter root before dialog)
    app = LauncherApp()

    # Check for updates in background (shows dialog if update available)
    try:
        from core.updater import check_and_prompt
        check_and_prompt(root_window=app)
    except Exception:
        pass  # Never block startup due to updater errors

    # Run the event loop
    app.mainloop()

if __name__ == "__main__":
    main()

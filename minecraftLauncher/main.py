import sys
import os
from ui.app import LauncherApp

def main():
    # Prevent crash on sys.stdout.flush() when running without console (PyInstaller)
    if sys.stdout is None: sys.stdout = open(os.devnull, "w")
    if sys.stderr is None: sys.stderr = open(os.devnull, "w")

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

    # Check for updates in background (shows toast if update available)
    try:
        from core.updater import check_and_prompt
        check_and_prompt(app)
    except Exception:
        pass  # Never block startup due to updater errors

    # Run the event loop
    app.mainloop()

if __name__ == "__main__":
    main()

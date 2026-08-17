"""Run script for Perchance AI Studio Web Application."""

import os
import sys
import platform
import threading
import time
import webbrowser
import uvicorn

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

def open_browser():
    time.sleep(1.5)
    # Only open browser if not running on a headless VPS
    if platform.system() != "Linux" or os.environ.get("DISPLAY"):
        target_url = f"http://127.0.0.1:{PORT}" if HOST == "0.0.0.0" else f"http://{HOST}:{PORT}"
        print(f"\n--> Opening Perchance AI Studio in default browser: {target_url}\n")
        try:
            webbrowser.open(target_url)
        except Exception:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("  PERCHANCE AI IMAGE STUDIO — WEB APPLICATION (v2.0)")
    print("=" * 60)
    print(f"  Bind Address: http://{HOST}:{PORT}")
    print("  Engine      : Perchance High-Performance Diffusion Engine")
    print("  Gallery Dir : static/outputs/")
    print("=" * 60)

    # Launch browser thread only on desktop systems
    if platform.system() != "Linux" or os.environ.get("DISPLAY"):
        threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI server
    uvicorn.run("app:app", host=HOST, port=PORT, log_level="info")

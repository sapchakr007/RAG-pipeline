#!/usr/bin/env python3
import subprocess, os, sys, time, threading
from pathlib import Path

# SETTINGS
B_PORT = "8000"
F_PORT = "3000"
root = Path(__file__).parent.absolute()

def start_backend():
    print(f"📡 Backend starting on {B_PORT}...")
    # Force Flask to use B_PORT
    env = {**os.environ, "FLASK_APP": "app.py", "FLASK_RUN_PORT": B_PORT}
    subprocess.Popen([sys.executable, "-m", "flask", "run", "--port", B_PORT], cwd=str(root), env=env)

def start_frontend():
    print(f"⚛️  Frontend starting on {F_PORT}...")
    # Force React to use F_PORT and ignore browser auto-open
    f_env = {**os.environ, "PORT": F_PORT, "BROWSER": "none"}
    subprocess.Popen(["npm", "start"], cwd=str(root / "frontend"), env=f_env)

if __name__ == "__main__":
    start_backend()
    time.sleep(2) # Give backend a headstart
    start_frontend()
    
    print(f"\n🚀 SYSTEM ONLINE")
    print(f"UI: http://localhost:{F_PORT}")
    print(f"API: http://localhost:{B_PORT}")
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
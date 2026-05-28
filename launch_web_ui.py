import os
import subprocess
import sys
import time
from pathlib import Path

def main():
    root = Path("/Users/sapchakrab/documents/github/RAG-pipeline")
    print(f"Project root: {root}")
    
    # 1. Start Flask backend on 5001
    print("📡 Starting Flask backend on port 5001...")
    backend_env = {**os.environ, "FLASK_APP": "app.py", "FLASK_RUN_PORT": "5001"}
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "flask", "run", "--port", "5001"],
        cwd=str(root),
        env=backend_env
    )
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # 2. Start React frontend on 3000
    print("⚛️ Starting React frontend on port 3000...")
    frontend_env = {**os.environ, "PORT": "3000", "BROWSER": "none"}
    frontend_proc = subprocess.Popen(
        ["npm", "start"],
        cwd=str(root / "frontend"),
        env=frontend_env
    )
    
    print("\n🚀 BOTH SERVERS ONLINE")
    print("Backend API: http://localhost:5001")
    print("Frontend UI: http://localhost:3000")
    
    # Keep script alive to keep subprocesses running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    main()

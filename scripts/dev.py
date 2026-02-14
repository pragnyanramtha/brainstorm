"""
Dev script — starts backend + frontend dev servers.
"""
import os
import sys
import subprocess
import webbrowser
import time
import signal
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

BACKEND_PORT = 3847
FRONTEND_PORT = 5173


def get_python():
    """Get the venv Python path."""
    venv_path = PROJECT_ROOT / ".venv"
    if os.name == "nt":
        return str(venv_path / "Scripts" / "python.exe")
    return str(venv_path / "bin" / "python")


def main():
    print("=" * 50)
    print("  Brainstorm AI — Dev Server")
    print("=" * 50)
    print()

    python = get_python()
    if not Path(python).exists():
        print("❌ Virtual environment not found. Run 'python scripts/setup.py' first.")
        sys.exit(1)

    processes = []

    try:
        # Start backend
        print(f"Starting backend on port {BACKEND_PORT}...")
        backend_proc = subprocess.Popen(
            [
                python, "-m", "uvicorn",
                "backend.main:app",
                "--host", "0.0.0.0",
                "--port", str(BACKEND_PORT),
                "--reload",
                "--reload-dir", str(BACKEND_DIR),
            ],
            cwd=str(PROJECT_ROOT),
        )
        processes.append(backend_proc)

        # Start frontend dev server
        print(f"Starting frontend on port {FRONTEND_PORT}...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(FRONTEND_DIR),
            shell=True,
        )
        processes.append(frontend_proc)

        # Wait a bit, then open browser
        time.sleep(2)
        url = f"http://localhost:{FRONTEND_PORT}"
        print(f"\n  🌐 Open: {url}")
        print(f"  📡 API:  http://localhost:{BACKEND_PORT}")
        print(f"\n  Press Ctrl+C to stop\n")

        try:
            webbrowser.open(url)
        except Exception:
            pass

        # Wait for processes
        for proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        print("\n\nShutting down...")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        print("Done.")


if __name__ == "__main__":
    main()

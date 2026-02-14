"""
Setup script — checks dependencies, creates venv, installs everything, seeds DB.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"


def check_python():
    """Check Python 3.11+ is installed."""
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 11):
        print(f"❌ Python 3.11+ required. You have {sys.version}")
        print("\nInstall Python 3.11+:")
        print("  Windows: https://www.python.org/downloads/")
        print("  macOS:   brew install python@3.12")
        print("  Linux:   sudo apt install python3.12")
        sys.exit(1)
    print(f"✓ Python {major}.{minor} detected")


def check_node():
    """Check Node.js 18+ is installed."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        version = result.stdout.strip().lstrip("v")
        major = int(version.split(".")[0])
        if major < 18:
            print(f"❌ Node.js 18+ required. You have v{version}")
            print("\nInstall Node.js 18+:")
            print("  https://nodejs.org/en/download/")
            sys.exit(1)
        print(f"✓ Node.js v{version} detected")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ Node.js not found")
        print("\nInstall Node.js 18+:")
        print("  https://nodejs.org/en/download/")
        sys.exit(1)


def create_venv():
    """Create virtual environment."""
    venv_path = PROJECT_ROOT / ".venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment exists")
    return venv_path


def get_pip(venv_path):
    """Get pip executable path."""
    if os.name == "nt":
        return str(venv_path / "Scripts" / "pip.exe")
    return str(venv_path / "bin" / "pip")


def install_python_deps(venv_path):
    """Install Python dependencies."""
    pip = get_pip(venv_path)
    print("Installing Python dependencies...")
    subprocess.run(
        [pip, "install", "-r", str(PROJECT_ROOT / "requirements.txt")],
        check=True,
    )
    print("✓ Python dependencies installed")


def install_frontend_deps():
    """Install frontend dependencies."""
    print("Installing frontend dependencies...")
    subprocess.run(
        ["pnpm", "install"],
        cwd=str(FRONTEND_DIR),
        check=True,
        shell=True,
    )
    print("✓ Frontend dependencies installed")


def create_workspace():
    """Create workspace directory."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    print("✓ Workspace directory ready")


def init_database(venv_path):
    """Initialize the SQLite database and seed data."""
    if os.name == "nt":
        python = str(venv_path / "Scripts" / "python.exe")
    else:
        python = str(venv_path / "bin" / "python")

    print("Initializing database...")
    subprocess.run(
        [python, "-c", (
            "import asyncio; "
            "from backend.database import init_db; "
            "from backend.database import async_session_factory; "
            "from backend.skills.seed_skills import seed_skills; "
            "from backend.mcps.seed_mcps import seed_mcps; "
            "async def run(): "
            "    await init_db(); "
            "    async with async_session_factory() as s: "
            "        await seed_skills(s); "
            "        await seed_mcps(s); "
            "    print('✓ Database initialized and seeded'); "
            "asyncio.run(run())"
        )],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


def build_frontend():
    """Build the frontend."""
    print("Building frontend...")
    subprocess.run(
        ["pnpm", "run", "build"],
        cwd=str(FRONTEND_DIR),
        check=True,
        shell=True,
    )
    print("✓ Frontend built")


def main():
    print("=" * 50)
    print("  Brainstorm AI — Setup")
    print("=" * 50)
    print()

    check_python()
    check_node()

    venv_path = create_venv()
    install_python_deps(venv_path)
    install_frontend_deps()
    create_workspace()
    init_database(venv_path)
    build_frontend()

    print()
    print("=" * 50)
    print("  ✅ Setup complete!")
    print(f"  Run: python scripts/dev.py")
    print("=" * 50)


if __name__ == "__main__":
    main()

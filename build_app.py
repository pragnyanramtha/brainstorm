#!/usr/bin/env python3
"""
Build script to bundle Middle Manager AI into a standalone executable.
Uses PyInstaller to create a single executable file.
"""
import os
import sys
import subprocess
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("✓ PyInstaller already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """Build the standalone executable."""
    print("🔨 Building standalone executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create single executable
        "--name", "MiddleManagerAI",
        "--add-data", ".env.example;.",  # Include env template
        "--add-data", "backend;backend",  # Include backend module
        "--add-data", "scripts;scripts",  # Include scripts
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "aiosqlite",
        "--hidden-import", "pydantic",
        "--hidden-import", "google.genai",
        "--hidden-import", "anthropic",
        "--hidden-import", "rich",
        "--hidden-import", "duckduckgo_search",
        "main.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ Build completed successfully!")
        print(f"📦 Executable created: {Path('dist/MiddleManagerAI.exe').absolute()}")
        print("\nTo run the app:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Run: dist/MiddleManagerAI.exe")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

def main():
    """Main build process."""
    print("🚀 Middle Manager AI - App Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found. Please run this script from the project root.")
        return
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Build executable
    if build_executable():
        print("\n🎉 App bundling complete!")
    else:
        print("\n💥 App bundling failed!")

if __name__ == "__main__":
    main()

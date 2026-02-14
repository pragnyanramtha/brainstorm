"""
Project scaffolder — creates real project directories, writes files,
runs install commands, and starts dev servers.

Instead of dumping code in chat, this module:
1. Parses the AI response for file blocks
2. Creates the project directory at ~/dev/<project_name>
3. Writes all files to disk
4. Runs setup commands (npm install, pip install, etc.)
5. Starts the dev server and returns the localhost URL
"""
import asyncio
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()

# Where projects live: ~/dev/
DEV_DIR = Path.home() / "dev"
DEV_DIR.mkdir(parents=True, exist_ok=True)


def get_project_dir(project_name: str) -> Path:
    """Get or create a project directory under ~/dev/."""
    # Clean up the name for a directory
    slug = re.sub(r'[^\w\-]', '-', project_name.lower().strip())
    slug = re.sub(r'-+', '-', slug).strip('-')
    if not slug:
        slug = "untitled-project"
    return DEV_DIR / slug


def extract_files_from_response(content: str) -> list[dict]:
    """
    Extract file blocks from AI response. Supports multiple patterns:
    - ```language:path/to/file.ext
    - File: path/to/file.ext  followed by ```
    - <!-- create:path/to/file.ext -->  followed by ```
    """
    files = []
    seen_paths = set()

    # Pattern 1: ```language:filepath or ``` filepath
    # e.g. ```typescript:src/app/page.tsx  or  ```tsx:src/components/Hero.tsx
    pattern1 = re.compile(
        r'```\w*[:\s]+([^\n`]+\.\w+)\s*\n(.*?)```',
        re.DOTALL
    )
    for match in pattern1.finditer(content):
        filepath = match.group(1).strip().strip('`"\'')
        code = match.group(2)
        if filepath and code and filepath not in seen_paths and not filepath.startswith('http'):
            files.append({"path": filepath, "content": code})
            seen_paths.add(filepath)

    # Pattern 2: File: path or Filename: path, followed by code block
    pattern2 = re.compile(
        r'(?:^|\n)(?:#+ )?(?:File|file|Filename|filename)[:\s]+([^\n]+\.\w+)\s*\n'
        r'```[\w]*\n(.*?)```',
        re.DOTALL
    )
    for match in pattern2.finditer(content):
        filepath = match.group(1).strip().strip('`"\'')
        code = match.group(2)
        if filepath and code and filepath not in seen_paths and not filepath.startswith('http'):
            files.append({"path": filepath, "content": code})
            seen_paths.add(filepath)

    # Pattern 3: <!-- create:path/to/file.ext -->
    pattern3 = re.compile(
        r'<!-- create:([^\n]+) -->\s*\n```[\w]*\n(.*?)```',
        re.DOTALL
    )
    for match in pattern3.finditer(content):
        filepath = match.group(1).strip()
        code = match.group(2)
        if filepath and code and filepath not in seen_paths:
            files.append({"path": filepath, "content": code})
            seen_paths.add(filepath)

    return files


def detect_project_type(files: list[dict]) -> str:
    """Detect project type from file list."""
    paths = {f["path"] for f in files}
    contents = " ".join(f.get("content", "") for f in files)

    if any("package.json" in p for p in paths) or "next" in contents.lower():
        if "next" in contents.lower():
            return "nextjs"
        if "vite" in contents.lower():
            return "vite"
        return "node"
    if any("requirements.txt" in p or "pyproject.toml" in p for p in paths):
        return "python"
    if any(p.endswith(".html") for p in paths):
        return "static"
    return "unknown"


def write_files_to_disk(project_dir: Path, files: list[dict]) -> list[str]:
    """Write extracted files to the project directory."""
    project_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for f in files:
        filepath = f["path"]
        content = f["content"]

        # Security: prevent path traversal
        normalized = os.path.normpath(filepath)
        if normalized.startswith("..") or os.path.isabs(normalized):
            console.print(f"[yellow]Skipping suspicious path: {filepath}[/yellow]")
            continue

        target = project_dir / normalized
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(filepath)
        console.print(f"[green]  📄 {filepath}[/green]")

    return written


async def run_command(cmd: list[str], cwd: Path, timeout: int = 120) -> dict:
    """Run a shell command asynchronously with timeout."""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )
        return {
            "success": process.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace")[-2000:],  # Last 2000 chars
            "stderr": stderr.decode("utf-8", errors="replace")[-2000:],
            "returncode": process.returncode,
        }
    except asyncio.TimeoutError:
        try:
            process.kill()
        except Exception:
            pass
        return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except FileNotFoundError:
        return {"success": False, "stdout": "", "stderr": f"Command not found: {cmd[0]}", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


async def install_dependencies(project_dir: Path, project_type: str) -> dict:
    """Install project dependencies based on project type."""
    if project_type in ("nextjs", "vite", "node"):
        # Try pnpm first, then npm
        for pkg_manager in ["pnpm", "npm"]:
            result = await run_command([pkg_manager, "--version"], project_dir, timeout=10)
            if result["success"]:
                return await run_command([pkg_manager, "install"], project_dir, timeout=180)
        return {"success": False, "stderr": "Neither pnpm nor npm found"}

    elif project_type == "python":
        if (project_dir / "requirements.txt").exists():
            return await run_command(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                project_dir, timeout=180
            )
        return {"success": True, "stdout": "No requirements.txt found", "stderr": ""}

    return {"success": True, "stdout": "No dependencies to install", "stderr": ""}


async def start_dev_server(project_dir: Path, project_type: str) -> dict:
    """Start a dev server and return the localhost URL."""
    cmd = None
    port = None

    if project_type == "nextjs":
        # Check for pnpm or npm
        for pkg in ["pnpm", "npm"]:
            result = await run_command([pkg, "--version"], project_dir, timeout=10)
            if result["success"]:
                cmd = [pkg, "run", "dev"]
                port = 3000
                break
    elif project_type == "vite":
        for pkg in ["pnpm", "npm"]:
            result = await run_command([pkg, "--version"], project_dir, timeout=10)
            if result["success"]:
                cmd = [pkg, "run", "dev"]
                port = 5173
                break
    elif project_type == "python":
        if (project_dir / "manage.py").exists():
            cmd = [sys.executable, "manage.py", "runserver"]
            port = 8000
        elif (project_dir / "app.py").exists() or (project_dir / "main.py").exists():
            entry = "app.py" if (project_dir / "app.py").exists() else "main.py"
            cmd = [sys.executable, entry]
            port = 8000
    elif project_type == "static":
        # Use python's built-in HTTP server
        cmd = [sys.executable, "-m", "http.server", "8080"]
        port = 8080

    if not cmd:
        return {"running": False, "url": None, "error": "Don't know how to start this project type"}

    try:
        # Start as background process
        if sys.platform == "win32":
            process = subprocess.Popen(
                cmd,
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            process = subprocess.Popen(
                cmd,
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

        # Wait a bit to see if it crashes immediately
        await asyncio.sleep(3)
        if process.poll() is not None:
            stdout = process.stdout.read().decode("utf-8", errors="replace")[-500:]
            stderr = process.stderr.read().decode("utf-8", errors="replace")[-500:]
            return {"running": False, "url": None, "error": f"Server exited immediately: {stderr or stdout}", "pid": None}

        url = f"http://localhost:{port}"
        return {"running": True, "url": url, "pid": process.pid, "error": None}

    except Exception as e:
        return {"running": False, "url": None, "error": str(e), "pid": None}


async def scaffold_project(
    project_name: str,
    ai_response: str,
    status_callback=None,
) -> dict:
    """
    Full project scaffolding pipeline:
    1. Extract files from AI response
    2. Create project dir at ~/dev/<name>
    3. Write files
    4. Install deps
    5. Start dev server
    6. Return result with URL

    status_callback: async callable(state, detail) for progress updates
    """
    async def emit(state: str, detail: str):
        if status_callback:
            await status_callback(state, detail)

    # 1. Extract files
    await emit("scaffolding", "Extracting files from response...")
    files = extract_files_from_response(ai_response)

    if not files:
        return {
            "scaffolded": False,
            "reason": "no_files_found",
            "project_dir": None,
            "files_created": [],
            "dev_server": None,
        }

    # 2. Create project dir
    project_dir = get_project_dir(project_name)
    await emit("scaffolding", f"Creating project at {project_dir}...")

    # 3. Write files
    await emit("scaffolding", f"Writing {len(files)} files...")
    written = write_files_to_disk(project_dir, files)

    # 4. Detect project type and install deps
    project_type = detect_project_type(files)
    await emit("scaffolding", f"Detected {project_type} project, installing dependencies...")

    install_result = await install_dependencies(project_dir, project_type)
    install_success = install_result.get("success", False)

    if not install_success:
        console.print(f"[yellow]Install warning: {install_result.get('stderr', '')}[/yellow]")

    # 5. Start dev server
    dev_server = {"running": False, "url": None}
    if install_success and project_type != "unknown":
        await emit("scaffolding", "Starting dev server...")
        dev_server = await start_dev_server(project_dir, project_type)

    return {
        "scaffolded": True,
        "project_dir": str(project_dir),
        "project_type": project_type,
        "files_created": written,
        "install_success": install_success,
        "install_output": install_result.get("stderr", "") or install_result.get("stdout", ""),
        "dev_server": dev_server,
    }

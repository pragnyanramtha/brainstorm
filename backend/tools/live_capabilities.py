from pathlib import Path
import subprocess
import os

def create_file(path: str, content: str) -> str:
    """Create a new file with the given content."""
    try:
        p = Path(path)
        if not p.is_absolute():
            # Consider enforcing relative to project root if context is available
            # For now, simplistic relative
            p = Path.cwd() / path
            
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"File created at {path}"
    except Exception as e:
        return f"Error creating file: {e}"

def read_file(path: str) -> str:
    """Read the content of a file."""
    try:
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / path
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

def list_files(path: str = ".") -> str:
    """List files in a directory."""
    try:
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / path
            
        files = []
        if not p.exists():
             return f"Path {path} does not exist"
             
        for entry in p.iterdir():
            files.append(f"{entry.name}{'/' if entry.is_dir() else ''}")
        return "\n".join(files) if files else "Directory is empty"
    except Exception as e:
        return f"Error listing files: {e}"

def run_command(command: str) -> str:
    """Run a shell command."""
    try:
        # Basic check to avoid interactive commands that block
        if "npm start" in command or "python server.py" in command:
             return "Please run long-running servers in a separate terminal. I can only run quick commands."
             
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=False
        )
        output = result.stdout
        if result.stderr:
            output += f"\nError Output: {result.stderr}"
        return output
    except Exception as e:
        return f"Error running command: {e}"

LIVE_TOOLS = [create_file, read_file, list_files, run_command]

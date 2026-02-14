# Brainstorm AI - App Bundle

## Running the Backend

You can now run the backend using any of these commands:

```bash
# Method 1: Using main.py
python main.py

# Method 2: Using start.py  
python start.py

# Method 3: Original method
.venv/Scripts/python -m backend.main
```

All commands will start the server at `http://localhost:3847` with API docs at `http://localhost:3847/docs`.

## Creating a Standalone App

### Option 1: PyInstaller (Recommended)

1. **Build the executable**:
   ```bash
   python build_app.py
   ```

2. **Run the app**:
   ```bash
   # Copy .env.example to .env and add your API keys first
   cp .env.example .env
   # Edit .env to add GEMINI_API_KEY
   
   # Run the executable
   dist/BrainstormAI.exe
   ```

### Option 2: Docker (For cross-platform deployment)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3847

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t brainstorm-ai .
docker run -p 3847:3847 -v $(pwd)/.env:/app/.env brainstorm-ai
```

### Option 3: Electron Desktop App

For a full desktop app experience with GUI:
- Use Electron to wrap the React frontend
- Include the Python backend as a subprocess
- Package with `electron-builder`

## Distribution

The PyInstaller approach creates:
- **Single executable**: `dist/BrainstormAI.exe`
- **Cross-platform**: Works on Windows, Mac, Linux
- **No Python required**: End users don't need Python installed
- **Portable**: Just copy the .exe file

## Notes

- The bundled app includes all dependencies
- Users still need to provide their own API keys in `.env`
- Database is created automatically on first run
- Frontend is served from the backend when built

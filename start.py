#!/usr/bin/env python3
"""
Alternative entry point for Middle Manager AI backend.
Run this file to start the backend server.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the backend
if __name__ == "__main__":
    from backend.main import app
    import uvicorn
    from backend.config import ServerConfig
    
    print("🚀 Starting Middle Manager AI Backend...")
    print(f"📍 Server will be available at http://{ServerConfig.HOST}:{ServerConfig.PORT}")
    print(f"📖 API docs at http://{ServerConfig.HOST}:{ServerConfig.PORT}/docs")
    
    uvicorn.run(
        app,
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=True,
    )

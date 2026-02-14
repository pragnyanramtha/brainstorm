# Brainstorm AI

A local-first, intelligent middleware between you and AI models.

## Project Status

- **Backend**: ✅ Complete (Core Engine, API, DB)
- **Frontend**: 🚧 In Progress (Structure built, dependencies pending)

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- API Keys: Google Gemini (Required), Anthropic Claude (Optional)

## Quick Start (Backend)

1. **Setup Environment**:
   ```bash
   python scripts/setup.py
   ```

2. **Configure API Keys**:
   Copy `.env.example` to `.env` and add your keys:
   ```bash
   cp .env.example .env
   # Edit .env and add GEMINI_API_KEY
   ```

3. **Run Backend Server**:
   ```bash
   .venv/Scripts/python -m backend.main
   ```
   Server will start at `http://localhost:3847`.
   API Documentation: `http://localhost:3847/docs`

## Architecture

- **Core Engine**:
  - `Intake`: Analyzes intent using Gemini Flash.
  - `Clarifier`: Asks smart questions when ambiguous.
  - `Optimizer`: Builds perfect single-shot prompts.
  - `Executor`: Routes to best model (Gemini/Claude) and handles tools.
  - `Memory`: Stores user profile and context in SQLite.
  - `Skills`: Auto-selects best prompt engineering techniques.
  - `MCP`: Connects to local tools via Model Context Protocol.

- **Tech Stack**:
  - FastAPI, SQLAlchmey, SQLite
  - React, Vite, Tailwind CSS (Frontend)

## Development

To run both backend and frontend (once frontend is fixed):
```bash
python scripts/dev.py
```

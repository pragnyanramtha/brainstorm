# Middle Manager AI

A local desktop app that acts as an intelligent middleware between humans and AI models. One chat = one project. Everything runs locally. No cloud. No accounts. No telemetry.

## Features

- **Smart Intent Parsing** — Understands what you *actually* need, not just what you typed
- **Clarifying Questions** — Asks smart questions when your request is ambiguous
- **Skill System** — 25+ prompt engineering skills automatically applied
- **Multi-Model Routing** — Uses the best model for the job (Gemini for general, Claude for code)
- **Core Memory** — Remembers you across sessions
- **MCP Integration** — Extensible via Model Context Protocol servers
- **Full Transparency** — See the optimized prompt that was actually sent

## Quick Start

```bash
# 1. Install dependencies
python scripts/setup.py

# 2. Start dev server
python scripts/dev.py

# 3. Open browser to http://localhost:3847
```

## Architecture

```
User Message
  → Intake (intent parsing, complexity scoring)
  → Clarifier (if ambiguous)
  → Skill Engine (select prompt engineering skills)
  → MCP Selector (pick relevant tools)
  → Model Router (choose best AI model)
  → Optimizer (build perfect single-shot prompt)
  → Executor (send to model, handle tool calls)
  → Response + Memory Extraction
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLite, SQLAlchemy
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS
- **AI**: Google Gemini, Anthropic Claude
- **Tools**: MCP (Model Context Protocol)

## API Keys

You'll need at least a Gemini API key (free). Claude API key is optional but recommended for code tasks.

- [Get Gemini API Key](https://aistudio.google.com/app/apikey)
- [Get Claude API Key](https://console.anthropic.com/)

## License

MIT

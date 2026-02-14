# TestAIAgent - Everlasting Cabinetry Sales Assistant

AI-powered sales assistant for Everlasting Cabinetry LLC, with NotebookLM integration for accurate, source-grounded responses.

## Features

- 🤖 **Dual LLM Support**: OpenAI (primary) with DeepSeek fallback
- 📚 **NotebookLM Integration**: Query company documentation with source citations
- 🌐 **Web Interface**: Modern React-based chat UI
- 🔧 **MCP Support**: Extensible tool system via Model Context Protocol
- 💬 **Streaming Responses**: Real-time message streaming with tool call visibility

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm or yarn

### 1. Clone Repository

```bash
git clone <repository-url>
cd TestAIAgent
```

### 2. Configure API Keys

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` and add your API keys:

```yaml
openai:
  api_key: sk-your-openai-key
  model: gpt-4o-mini

deepseek:
  api_key: sk-your-deepseek-key
  model: deepseek-chat
```

### 3. Install Backend Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[web]"
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Start Services

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
uvicorn web.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 6. Access Application

Open your browser and navigate to:
- **Web Interface**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs

## Project Structure

```
TestAIAgent/
├── agent/                  # Core agent logic
│   ├── core/              # Agent, LLM client, context management
│   ├── tools/             # Built-in tools and MCP integration
│   └── storage/           # History persistence
├── web/                   # FastAPI backend
│   ├── main.py           # Application entry point
│   ├── routes.py         # REST API endpoints
│   ├── websocket.py      # WebSocket chat handler
│   └── schemas.py        # Pydantic models
├── frontend/              # React frontend
│   └── src/
│       ├── components/   # UI components
│       ├── hooks/        # Custom React hooks
│       └── styles/       # CSS styles
├── skills/               # Skills directory
│   └── notebooklm-skill/ # NotebookLM integration
└── data/                 # Runtime data (history, etc.)
```

## Configuration

### API Keys

Configure in `config.yaml`:

```yaml
openai:
  api_key: sk-xxx
  model: gpt-4o-mini
  base_url: null  # Optional proxy

deepseek:
  api_key: sk-xxx
  model: deepseek-chat
```

### Skills

Skills are loaded from the `skills_dir` directory. Each skill is defined in a `SKILL.md` file with YAML frontmatter.

## API Endpoints

### REST API

- `GET /api/health` - Health check
- `GET /api/tools` - List available tools
- `GET /api/skills` - List loaded skills
- `DELETE /api/history` - Clear conversation history

### WebSocket

- `ws://localhost:8000/ws/chat` - Chat WebSocket endpoint

## Slash Commands

Use these commands in the chat interface:

- `/tools` - List available tools
- `/skills` - List loaded skills
- `/clear` - Clear conversation history
- `/help` - Show help message

## License

MIT

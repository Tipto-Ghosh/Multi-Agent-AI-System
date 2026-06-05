# 🤖 Production-Grade Multi-Agent AI System

> A fully local, four-agent AI system built with LangGraph, MCP, and A2A — no API keys, no cloud, no ongoing cost.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.0-FF6B35?style=flat)](https://langchain-ai.github.io/langgraph/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=flat)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

This project is the companion code for the freeCodeCamp handbook: **How to Build a Local Multi-Agent AI System with LangGraph, MCP, and A2A**.

The **Learning Accelerator** is a four-agent system that plans a study curriculum, explains topics from your own notes, quizzes you, and adapts based on your results. The use case is the teaching vehicle — the architecture is the real subject.

```
Goal: "Learn Python closures and decorators"
  │
  ▼
Curriculum Planner  ──►  Structured study roadmap
  │
  ▼ (you approve the plan)
Explainer           ──►  Reads your notes via MCP, explains each topic
  │
  ▼
Quiz Generator      ──►  Tests understanding, grades answers with LLM-as-judge
  │
  ▼
Progress Coach      ──►  Adapts roadmap, calls CrewAI Study Buddy via A2A
  │
  └── loops back to Explainer for the next topic
```

The same architecture pattern powers production systems for sales enablement, compliance training, customer support onboarding, and engineering ramp-up.

---

## 🏗️ Architecture

| Layer | Technology | What it does |
|---|---|---|
| Orchestration | LangGraph 1.1.0 | Stateful agent graph with checkpointing |
| Tool Integration | MCP (mcp 1.26.0) | Standardized agent-to-tool protocol |
| Agent Coordination | A2A (a2a-sdk 0.3.25) | Cross-framework agent-to-agent protocol |
| Local Inference | Ollama | LLM serving at `localhost:11434` |
| Cross-Framework | CrewAI 1.13.0 | Study Buddy agent (called via A2A) |
| Observability | Langfuse 4.0.1 | Full trace of every agent and LLM call |
| Evaluation | DeepEval 3.9.1 | LLM-as-judge quality metrics |

### The Four Agents

| Agent | Role | Why it's separate |
|---|---|---|
| **Curriculum Planner** | Takes a learning goal, produces a structured study roadmap | Single LLM call, `temperature=0.1`, JSON format — zero tools. Fast and deterministic. |
| **Explainer** | Reads your notes via MCP, explains topics to the student | Multi-turn tool-calling loop. Non-deterministic iteration count. Completely different execution pattern. |
| **Quiz Generator** | Generates questions (creative), then grades answers (analytical) | Two LLM calls with different temperatures. Interactive — pauses for user input. Also runs as a standalone A2A service. |
| **Progress Coach** | Synthesizes results, updates topic status, routes to the next topic or ends | Makes the only cross-agent A2A call. Reads/writes MCP memory. Owns the routing decision. |

---

## 📋 Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- Docker Desktop *(optional — for Langfuse observability)*
- **RAM:** 16 GB minimum, 32 GB recommended
- **VRAM:** 8 GB for `qwen2.5:7b` | 24 GB for `qwen2.5-coder:32b`

---

## 🚀 Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/Tipto-Ghosh/Multi-Agent-AI-System
cd Multi-Agent-AI-System
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Pull your model

```bash
# Choose based on available VRAM
ollama pull qwen2.5:7b          # 8 GB VRAM
ollama pull qwen2.5-coder:32b   # 24 GB VRAM
```

### 3. Start Ollama

```bash
ollama serve   # In a separate terminal
# macOS: start the Ollama app from your Applications folder
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env — set OLLAMA_MODEL to the model you pulled
```

### 5. Run

```bash
python main.py
```

---

## ⚙️ Running All Services (Full System)

The complete system runs three processes. Open three terminal tabs:

**Tab 1 — Quiz Generator A2A service:**
```bash
source .venv/bin/activate
python src/a2a_services/quiz_service.py
# Serves at http://localhost:9001
```

**Tab 2 — CrewAI Study Buddy A2A service:**
```bash
source .venv/bin/activate
python src/crewai_agent/study_buddy.py
# Serves at http://localhost:9002
```

**Tab 3 — Main LangGraph application:**
```bash
source .venv/bin/activate
python main.py
```

Or use the Makefile:
```bash
make services   # Starts both A2A services in the background
make run        # Runs the main application
```

---

## 🗂️ Project Structure

```
Multi-Agent-AI-System/
├── src/
│   ├── agents/                     # LangGraph agent nodes
│   │   ├── curriculum_planner.py
│   │   ├── explainer.py
│   │   ├── quiz_generator.py
│   │   ├── progress_coach.py
│   │   └── human_approval.py
│   ├── graph/
│   │   ├── state.py                # Shared AgentState TypedDict
│   │   └── workflow.py             # LangGraph graph definition
│   ├── mcp_servers/                # MCP tool servers
│   │   ├── filesystem_server.py
│   │   └── memory_server.py
│   ├── a2a_services/               # A2A protocol services and client
│   │   ├── quiz_service.py         # Quiz Generator as A2A service
│   │   └── a2a_client.py           # Client for calling A2A services
│   ├── crewai_agent/
│   │   └── study_buddy.py          # CrewAI agent served via A2A
│   ├── constants/                  # Shared constants
│   ├── exception/                  # Custom exception handling
│   ├── logger/                     # Logging configuration
│   ├── prompts/                    # Agent prompt templates
│   ├── utils/                      # Utility helpers
│   └── observability/
│       └── langfuse_setup.py       # Langfuse callback handler
├── tests/
│   ├── conftest.py                 # Shared fixtures and markers
│   ├── test_state.py               # 24 tests
│   ├── test_curriculum_planner.py  # 11 tests
│   ├── test_mcp_servers.py         # 36 tests
│   ├── test_explainer.py           # 14 tests
│   ├── test_quiz_and_coach.py      # 17 tests
│   ├── test_checkpointing.py       # 20 tests
│   ├── test_observability.py       # 16 tests
│   ├── test_a2a.py                 # 19 tests
│   ├── test_crewai_interop.py      # 25 tests
│   └── test_eval.py                # 12 eval tests (requires Ollama)
├── study_materials/
│   └── sample_notes/               # Markdown files the agents read
├── data/                           # SQLite checkpoint DB (created at runtime)
├── Images/                         # Architecture diagrams
├── main.py                         # Entry point
├── streamlit_app.py                # Streamlit UI
├── demo.py                         # Demo script
├── docker-compose.yml              # Langfuse self-hosted stack
├── Makefile                        # One-command startup
├── requirements.txt
└── .env.example
```

---

## 🧪 Testing

```bash
# Fast unit tests — run during development (~3 seconds)
# 182 tests across 9 test files
pytest tests/ -m "not eval" -v

# Quality evaluation tests — run before releases (~90 seconds, requires Ollama)
# 12 LLM-as-judge tests
pytest tests/test_eval.py -v -s -m eval
```

---

## 💾 Session Resume

Every session is checkpointed to `data/checkpoints.db` after each agent node. To resume a stopped session:

```bash
python main.py --resume <session-id>
```

> The session ID is printed at the start of every run.

---

## 📊 Observability

Start Langfuse locally with Docker:

```bash
docker compose up -d
# Open http://localhost:3000
```

Add your API keys to `.env` (from the Langfuse project settings), then run as normal. Every agent call, LLM completion, and tool call will appear in the trace UI automatically.

---

## 📚 Adding Your Own Study Materials

Replace or add Markdown files in `study_materials/sample_notes/`. The Explainer agent reads every `.md` file in that directory automatically via the MCP filesystem server — no configuration changes needed.

---

## 🔧 Configuration Reference

See `.env.example` for all available settings.

| Variable | Default | Effect |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:7b` | Model used by all agents |
| `USE_A2A_QUIZ` | `true` | Route quiz tasks to the A2A service |
| `USE_STUDY_BUDDY` | `true` | Call CrewAI Study Buddy for low scores |
| `CHECKPOINT_DB` | `data/checkpoints.db` | SQLite path for checkpoints |

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ using LangGraph · MCP · A2A · Ollama · CrewAI
</p>
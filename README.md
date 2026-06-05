# Redis Eats Agentic Workshop — Workshop 2

> **Workshop 2 of 2** — Build a context-aware AI agent on Redis Cloud using Redis Iris: Agent Memory, Context Retriever, LangCache, and RedisVL.

This workshop extends [Workshop 1 (RAG Chatbot)](https://github.com/your-org/redis-eats-rag-workshop) into a full **context-aware support agent** that knows who the customer is, remembers conversations, looks up live order data, and answers policy questions — all grounded in Redis Cloud.

---

## What You Will Build

An agentic Redis Eats support bot that combines four Redis Iris components:

| Component | Role |
|---|---|
| **Agent Memory** | Remembers the customer across sessions (long-term) and within a conversation (session) |
| **Context Retriever** | Exposes live order, customer, and restaurant data as governed tools the agent can call |
| **LangCache** | Avoids redundant LLM calls for repeated or similar questions |
| **RedisVL + RAG** | Answers policy questions from the Workshop 1 knowledge base |

The agent uses an **OpenAI function-calling loop** — no LangGraph or external agent frameworks required.

---

## Prerequisites

Complete these **before** the workshop:

### 1 — Redis Cloud Database
- Same database used in Workshop 1 (free tier is fine)
- Host, port, and password from the Redis Cloud console

### 2 — OpenAI API Key
- Paid account at [platform.openai.com](https://platform.openai.com)

### 3 — Agent Memory Service (Redis Cloud → Context Engine → Agent Memory)
- Provision a new Agent Memory service in the Redis Cloud console
- Save the **URL**, **Store ID**, and **API key**

### 4 — Context Retriever Service (Redis Cloud → Context Engine → Context Retriever)
- Provision a new Context Retriever service in the Redis Cloud console
- Save the **URL**, **Admin key**, **Agent key**, and **MCP URL**

### 5 — LangCache (same as Workshop 1)
- LangCache credentials from Workshop 1 work here too

> **Workshop 1 not required:** This notebook checks for the Workshop 1 policy index and reloads it automatically if needed.

---

## How to Run

### Option 1 — Google Colab (recommended)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/your-org/redis-eats-agentic-workshop/blob/main/notebooks/redis_eats_agentic_workshop.ipynb)

### Option 2 — Local

```bash
git clone https://github.com/bcooper-redis/redis-eats-agentic-workshop
cd redis-eats-agentic-workshop
pip install -r requirements.txt
# Open notebooks/redis_eats_agentic_workshop.ipynb
```

---

## Expected Duration

**~2.5–3 hours** including exercises, tool-calling demos, and multi-turn agent scenarios.

---

## File Structure

```
redis-eats-agentic-workshop/
├── README.md
├── requirements.txt
├── .env.example
├── notebooks/
│   └── redis_eats_agentic_workshop.ipynb
├── data/
│   ├── source_json/
│   │   ├── customers.json
│   │   ├── orders.json
│   │   ├── restaurants.json
│   │   └── drivers.json
│   └── live/                         # Redis Insight exports (generated)
├── docs/
│   ├── instructor_guide.md
│   └── architecture/
│       └── redis-eats-agentic-workshop-architecture.png
├── scripts/
│   ├── load_live_data.py             # Loads JSON data into Redis (mocked RDI)
│   └── update_repo_url.py            # Set GitHub username before first push
└── tests/
    └── README.md
```

---

## What Is Covered

- Redis Iris Context Engine overview
- Mocked RDI: loading live operational data into Redis
- Context Retriever: defining and calling governed data tools
- Agent Memory: session memory + long-term memory
- OpenAI function-calling agent loop
- Memory-enriched prompts
- LangCache integration in the agent pipeline
- Multi-turn realistic agent scenarios
- Reset lab

## What Is Intentionally Not Covered

- LangGraph or other agent orchestration frameworks
- Live RDI CDC pipeline (mocked for the workshop)
- Redis Flex or FeatureForm
- Multi-agent systems
- Production deployment patterns

---

## About

Based on the [Redis Iris Demos](https://github.com/redis/redis-iris-demos) — Redis Eats / Reddash domain.
Live demo: [redis-iris-demo-yus.vercel.app](https://redis-iris-demo-yus.vercel.app/)

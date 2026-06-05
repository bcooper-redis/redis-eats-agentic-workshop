"""
build_notebook.py

Builds Sections 0–5 of the Redis Eats Agentic Workshop notebook:
  0 — Welcome and What We Are Building
  1 — Setup
  2 — Load Live Data (Mocked RDI)
  3 — Check / Reload Workshop 1 Policy Index
  4 — Context Retriever — Connect and Explore Tools
  5 — Agent Memory — Session and Long-term Memory

Run:
    python3 scripts/build_notebook.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OUTPUT    = REPO_ROOT / "notebooks" / "redis_eats_agentic_workshop.ipynb"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}

def code(src, tags=None):
    meta = {"tags": tags} if tags else {}
    return {"cell_type": "code", "execution_count": None,
            "metadata": meta, "outputs": [], "source": [src]}


cells = []

# ============================================================
# COLAB SETUP
# ============================================================

cells.append(code("""\
#@title ⚙️ Google Colab Setup (run this first if using Colab) { display-mode: 'form' }
import os, subprocess, sys

REPO_URL = "https://github.com/your-org/redis-eats-agentic-workshop"
REPO_DIR = "/content/redis-eats-agentic-workshop"

if "google.colab" in str(get_ipython()):
    if not os.path.exists(REPO_DIR):
        print(f"Cloning {REPO_URL} ...")
        result = subprocess.run(["git", "clone", REPO_URL, REPO_DIR],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print("\\n❌ git clone failed:")
            print(result.stderr or result.stdout)
            print("\\n  → Check that REPO_URL has been updated with your GitHub username")
            print("    Run: python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-agentic-workshop")
            sys.exit(1)
        print(f"✅ Repo cloned to {REPO_DIR}")
    else:
        print(f"✅ Repo already present at {REPO_DIR}")
    os.chdir(REPO_DIR)
    print(f"✅ Working directory: {os.getcwd()}")
else:
    print("Not running in Colab — skipping clone.")
    print("Make sure you are running from the repo root directory.")
"""))

# ============================================================
# SECTION 0 — Welcome
# ============================================================

cells.append(md(
    "# 🍕 Redis Eats Agentic Workshop\n",
    "## *Don't Talk With Food In Your Mouth — Workshop 2*\n",
    "\n",
    "Welcome to Workshop 2. This workshop extends the RAG chatbot from Workshop 1 into a\n",
    "**context-aware AI agent** powered by four Redis Iris components:\n",
    "\n",
    "| Component | What It Adds |\n",
    "|---|---|\n",
    "| **Agent Memory** | The agent knows who you are and remembers your conversation |\n",
    "| **Context Retriever** | The agent looks up live order, customer, and restaurant data |\n",
    "| **LangCache** | Repeated questions are answered instantly from cache |\n",
    "| **RedisVL + RAG** | Policy questions answered from the Workshop 1 knowledge base |\n",
    "\n",
    "The agent uses an **OpenAI function-calling loop** — clean, readable, no extra frameworks.\n",
    "\n",
    "---\n",
    "\n",
    "## Architecture\n",
    "\n",
    "![Architecture](../docs/architecture/redis-eats-agentic-workshop-architecture.png)\n",
    "\n",
    "---\n",
    "\n",
    "## What This Workshop Adds vs Workshop 1\n",
    "\n",
    "| Feature | Workshop 1 | Workshop 2 |\n",
    "|---|---|---|\n",
    "| Policy Q&A (RAG) | ✅ | ✅ |\n",
    "| Semantic routing | ✅ | ✅ |\n",
    "| LangCache | ✅ | ✅ |\n",
    "| **Live order/customer/restaurant data** | ❌ | ✅ |\n",
    "| **Context Retriever tools** | ❌ | ✅ |\n",
    "| **Agent Memory (session + long-term)** | ❌ | ✅ |\n",
    "| **Multi-turn personalised conversations** | ❌ | ✅ |\n",
    "\n",
    "---\n",
    "\n",
    "## 📋 Table of Contents\n",
    "\n",
    "| # | Section |\n",
    "|---|---|\n",
    "| 0 | Welcome |\n",
    "| 1 | Setup — packages, credentials, connectivity |\n",
    "| 2 | Load Live Data — mocked RDI |\n",
    "| 3 | Check / Reload Workshop 1 Policy Index |\n",
    "| 4 | Context Retriever — connect and explore tools |\n",
    "| 5 | Agent Memory — session and long-term memory |\n",
    "| 6 | Tool Definitions — wrap everything for the agent |\n",
    "| 7 | Basic Agent Loop — function calling |\n",
    "| 8 | Add Agent Memory — personalised responses |\n",
    "| 9 | Add LangCache — skip redundant LLM calls |\n",
    "| 10 | Full Pipeline — all components together |\n",
    "| 11 | Live Scenarios — multi-turn conversations |\n",
    "| 12 | Reset Lab |\n",
    "| 13 | What Comes Next |\n",
    "\n",
    "**Estimated time:** ~2.5–3 hours\n",
))

# ============================================================
# SECTION 1 — Setup
# ============================================================

cells.append(md(
    "---\n",
    "## Section 1 — Setup\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 1 — Package Installation
# ---------------------------------------------------------------------------
import importlib.util, subprocess, sys

REQUIRED_PACKAGES = {
    "redis":                "redis>=5.0.0",
    "redisvl":              "redisvl>=0.20.0",
    "redis_agent_memory":   "redis-agent-memory>=0.0.4",
    "context_surfaces":     "context-surfaces>=0.0.5",
    "langcache":            "langcache>=0.12.0",
    "openai":               "openai>=1.30.0",
    "pypdf":                "pypdf>=4.0.0",
    "sentence_transformers":"sentence-transformers>=2.2.0",
    "tqdm":                 "tqdm>=4.66.0",
    "dotenv":               "python-dotenv>=1.0.0",
}

missing = {
    k: v for k, v in REQUIRED_PACKAGES.items()
    if importlib.util.find_spec(k) is None
}

if missing:
    print(f"Installing {len(missing)} package(s): {', '.join(missing.values())}\\n")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", *missing.values(), "--quiet"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ pip install failed:")
        print(result.stderr or result.stdout)
    else:
        print("✅ Packages installed.")
        print()
        print("=" * 55)
        print("  ACTION REQUIRED: Restart the runtime now.")
        print()
        print("  Colab : Runtime menu → Restart session")
        print("  Local : Kernel menu  → Restart kernel")
        print("  Then re-run from the top of the notebook.")
        print("=" * 55)
else:
    print("✅ All packages ready — continue to the next cell.")
    import redis, redisvl, openai, pypdf
    print(f"   redis={redis.__version__}  redisvl={redisvl.__version__}  openai={openai.__version__}")
"""))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import os, uuid, json, time
import subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import redis as redis_lib
from redisvl.index import SearchIndex
from redisvl.schema import IndexSchema
from redisvl.query import VectorQuery
from redisvl.extensions.router import SemanticRouter, Route
from redisvl.extensions.router.schema import RoutingConfig

import openai
from openai import OpenAI

import numpy as np
import pypdf
from tqdm import tqdm

# Redis Iris imports
from redis_agent_memory import AgentMemory
from redis_agent_memory import models as memory_models
from context_surfaces import MCPClient, ContextSurfacesClient
from langcache import LangCache

# ---------------------------------------------------------------------------
# Safe-default variables — set by credential and connectivity cells below
# ---------------------------------------------------------------------------
r             = None    # Redis client  (set by Section 1.2)
openai_client = None    # OpenAI client (set by Section 1.3)
agent_memory  = None    # Agent Memory  (set by Section 1.4)
mcp_client    = None    # Context Retriever MCP client (set by Section 1.5)
lang_cache    = None    # LangCache     (set by Section 1.6)

_redis_ok   = False
_openai_ok  = False
_memory_ok  = False
_ctx_ok     = False
_cache_ok   = False

print("✅ Imports complete")
"""))

# --- 1.1 Credentials ---
cells.append(md(
    "### 1.1 — Credentials\n",
    "\n",
    "Paste all your credentials below. This workshop uses five services:\n",
    "\n",
    "| Credential | Where to find it |\n",
    "|---|---|\n",
    "| Redis CLI command | Redis Cloud → your database → **Connect** → **Redis CLI** |\n",
    "| OpenAI API key | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |\n",
    "| Agent Memory | Redis Cloud → Context Engine → **Agent Memory** → your service |\n",
    "| Context Retriever | Redis Cloud → Context Engine → **Context Retriever** → your service |\n",
    "| LangCache | Redis Cloud → Context Engine → **LangCache** → your cache (same as Workshop 1) |\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 1.1 — Paste all credentials here, then run this cell
# ---------------------------------------------------------------------------
from urllib.parse import urlparse

# ✏️  Redis Cloud CLI command (Redis Cloud → Connect → Redis CLI)
REDIS_CLI_COMMAND = "redis-cli -u redis://default:notmyactualpassword@your-host.db.redis.io:12345"

# ✏️  OpenAI API key
OPENAI_API_KEY = "sk-your-openai-api-key-here"

# ✏️  Agent Memory (Redis Cloud → Context Engine → Agent Memory)
AGENT_MEMORY_URL      = "https://your-agent-memory-host.redis.io"
AGENT_MEMORY_STORE_ID = "your-store-id-here"
AGENT_MEMORY_API_KEY  = "your-agent-memory-api-key-here"

# ✏️  Context Retriever (Redis Cloud → Context Engine → Context Retriever)
CTX_SURFACES_URL   = "https://your-context-surfaces-host.redis.io"
CTX_ADMIN_KEY      = "your-admin-key-here"
CTX_AGENT_KEY      = "your-agent-key-here"
CTX_MCP_URL        = "https://your-mcp-host.redis.io"

# ✏️  LangCache (same as Workshop 1)
LANGCACHE_URL      = "https://your-langcache-host.langcache.redis.io"
LANGCACHE_CACHE_ID = "your-cache-id-here"
LANGCACHE_API_KEY  = "your-langcache-api-key-here"

# ---------------------------------------------------------------------------
# Parse Redis CLI command — no edits needed below this line
# ---------------------------------------------------------------------------
PLACEHOLDERS = (
    "notmyactualpassword", "yourpassword", "",
    "your-host.db.redis.io",
)

def _parse_redis_cli(cmd: str) -> dict:
    \"\"\"Parse a redis-cli -u command into connection components.\"\"\"
    cmd = cmd.strip()
    if cmd.lower().startswith("redis-cli -u "):
        cmd = cmd[len("redis-cli -u "):].strip()
    parse_url = cmd
    if parse_url.startswith("rediss://"):
        parse_url = "redis://" + parse_url[len("rediss://"):]
    if not parse_url.startswith("redis://"):
        raise ValueError(f"Expected redis:// or rediss://, got: {cmd!r}")
    p = urlparse(parse_url)
    if not p.hostname:
        raise ValueError("Could not parse hostname.")
    scheme = "rediss" if cmd.startswith("rediss://") else "redis"
    return {
        "host": p.hostname, "port": p.port or 6379,
        "username": p.username or "default", "password": p.password or "",
        "use_ssl": cmd.startswith("rediss://"),
        "redis_url": f"{scheme}://{p.username or 'default'}:{p.password or ''}@{p.hostname}:{p.port or 6379}",
    }

errors = []

# Parse Redis
try:
    _creds = _parse_redis_cli(REDIS_CLI_COMMAND)
    if _creds["password"] in PLACEHOLDERS:
        errors.append("REDIS_CLI_COMMAND is still the placeholder")
    else:
        REDIS_HOST     = _creds["host"]
        REDIS_PORT     = _creds["port"]
        REDIS_USERNAME = _creds["username"]
        REDIS_PASSWORD = _creds["password"]
        REDIS_USE_SSL  = _creds["use_ssl"]
        REDIS_URL      = _creds["redis_url"]
        os.environ["REDIS_URL"] = REDIS_URL
        _masked = REDIS_PASSWORD[:2] + "*" * max(len(REDIS_PASSWORD)-2, 3)
        print(f"✅ Redis     : {REDIS_HOST}:{REDIS_PORT}  password={_masked}")
except ValueError as e:
    errors.append(f"REDIS_CLI_COMMAND parse error: {e}")

# Validate OpenAI
if OPENAI_API_KEY in ("sk-your-openai-api-key-here", ""):
    errors.append("OPENAI_API_KEY is still the placeholder")
elif not OPENAI_API_KEY.startswith("sk-"):
    errors.append("OPENAI_API_KEY doesn't look valid (must start with sk-)")
else:
    print(f"✅ OpenAI    : key starts with sk-...")

# Validate Agent Memory
_am_phs = ("your-store-id-here", "your-agent-memory-api-key-here",
           "your-agent-memory-host.redis.io")
if any(v in _am_phs for v in [AGENT_MEMORY_STORE_ID, AGENT_MEMORY_API_KEY, AGENT_MEMORY_URL]):
    errors.append("Agent Memory credentials still contain placeholders")
else:
    print(f"✅ Agent Memory : {AGENT_MEMORY_URL}  store={AGENT_MEMORY_STORE_ID}")

# Validate Context Retriever
_cr_phs = ("your-admin-key-here", "your-agent-key-here",
           "your-context-surfaces-host.redis.io", "your-mcp-host.redis.io")
if any(v in _cr_phs for v in [CTX_ADMIN_KEY, CTX_AGENT_KEY, CTX_SURFACES_URL, CTX_MCP_URL]):
    errors.append("Context Retriever credentials still contain placeholders")
else:
    print(f"✅ Context Retriever : {CTX_SURFACES_URL}")

# Validate LangCache
_lc_phs = ("your-cache-id-here", "your-langcache-api-key-here",
           "your-langcache-host.langcache.redis.io")
LANGCACHE_AVAILABLE = not any(v in _lc_phs for v in
                              [LANGCACHE_CACHE_ID, LANGCACHE_API_KEY, LANGCACHE_URL])
if LANGCACHE_AVAILABLE:
    print(f"✅ LangCache : {LANGCACHE_URL}")
else:
    print("⚠️  LangCache : credentials not set — LangCache section will be skipped")

print()
if errors:
    print("⚠️  Fix the following before continuing:")
    for e in errors:
        print(f"   → {e}")
else:
    print("✅ All credentials set — run the next cell to test connections.")
"""))

# --- 1.2 Redis connectivity ---
cells.append(md("### 1.2 — Test Redis Connection\n"))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 1.2 — Redis connectivity check (same robust pattern as Workshop 1)
# ---------------------------------------------------------------------------
import concurrent.futures

_redis_ok       = True
CONNECT_TIMEOUT = 5

print("Checking Redis Cloud connectivity...\\n")

if not REDIS_HOST or not REDIS_PASSWORD:
    print("  ❌ Credentials not set — run Section 1.1 first")
    _redis_ok = False
else:
    print(f"  ✅ Pre-flight OK  (protocol: {'rediss://' if REDIS_USE_SSL else 'redis://'})")

def _connect_redis():
    \"\"\"Create client and ping — runs in thread for hard timeout.\"\"\"
    client = redis_lib.Redis(
        host=REDIS_HOST, port=REDIS_PORT,
        username=REDIS_USERNAME, password=REDIS_PASSWORD,
        ssl=REDIS_USE_SSL, decode_responses=True,
        socket_connect_timeout=4, socket_timeout=4,
    )
    client.ping()
    return client

r = None
if _redis_ok:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_connect_redis)
        try:
            r = fut.result(timeout=CONNECT_TIMEOUT)
            info = r.info("server")
            print(f"  ✅ TCP connection  OK")
            print(f"  ✅ Redis version   {info['redis_version']}")
        except concurrent.futures.TimeoutError:
            print(f"  ❌ Connection timed out after {CONNECT_TIMEOUT}s")
            _redis_ok = False
        except redis_lib.exceptions.AuthenticationError:
            print("  ❌ Authentication failed — check username/password in Section 1.1")
            _redis_ok = False
        except Exception as e:
            print(f"  ❌ Connection error: {e}")
            _redis_ok = False

    if _redis_ok:
        # Verify Redis Search module
        search_found = False
        try:
            r.execute_command("FT._LIST")
            search_found = True
        except Exception:
            pass
        if search_found:
            print("  ✅ Redis Search    available")
        else:
            print("  ❌ Redis Search    NOT found — check your database plan")
            _redis_ok = False

        # Verify RedisVL
        if _redis_ok:
            try:
                from redisvl.index import SearchIndex
                from redisvl.schema import IndexSchema
                _ts = IndexSchema.from_dict({
                    "index": {"name": "_w2test", "prefix": "_w2test:"},
                    "fields": [{"name": "v", "type": "text"}]
                })
                SearchIndex(_ts, redis_client=r).client.ping()
                print("  ✅ RedisVL         OK")
            except Exception as e:
                print(f"  ❌ RedisVL: {e}")
                _redis_ok = False

print()
if _redis_ok:
    print(f"✅ All Redis checks passed")
    print(f"   {REDIS_HOST}:{REDIS_PORT}  |  user: {REDIS_USERNAME}  |  ssl: {REDIS_USE_SSL}")
else:
    print("❌ Fix Redis errors above before continuing.")
"""))

# --- 1.3 OpenAI connectivity ---
cells.append(md("### 1.3 — Test OpenAI Connection\n"))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 1.3 — OpenAI connectivity (auth + embedding model + chat model)
# ---------------------------------------------------------------------------
_openai_ok = False
print("Checking OpenAI connectivity...\\n")

try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    openai_client.models.list()
    print("  ✅ API key               valid")
    _key_ok = True
except openai.AuthenticationError:
    print("  ❌ API key invalid — check Section 1.1")
    _key_ok = False
except Exception as e:
    print(f"  ❌ OpenAI error: {e}")
    _key_ok = False

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS  = 1536
CHAT_MODEL      = "gpt-4o-mini"

_embed_ok = False
if _key_ok:
    try:
        resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input="test")
        dims = len(resp.data[0].embedding)
        print(f"  ✅ Embedding model       {EMBEDDING_MODEL} ({dims} dims)")
        _embed_ok = True
    except openai.RateLimitError:
        print("  ❌ Embedding model — rate limit / insufficient credits")
    except Exception as e:
        print(f"  ❌ Embedding model: {e}")

if _embed_ok:
    try:
        reply = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": "Reply with one word: ready"}],
            max_tokens=5, temperature=0,
        ).choices[0].message.content.strip().lower()
        print(f"  ✅ Chat model            {CHAT_MODEL} (response: '{reply}')")
        _openai_ok = True
    except openai.RateLimitError:
        print("  ❌ Chat model — rate limit / insufficient credits")
    except Exception as e:
        print(f"  ❌ Chat model: {e}")

print()
if _openai_ok:
    print("✅ All OpenAI checks passed")
else:
    print("❌ Fix OpenAI errors above before continuing.")
"""))

# --- 1.4 Agent Memory ---
cells.append(md(
    "### 1.4 — Test Agent Memory Connection\n",
    "\n",
    "Agent Memory is a Redis Cloud managed service that provides two tiers of memory for AI agents:\n",
    "\n",
    "- **Session memory** — the current conversation, stored with a TTL\n",
    "- **Long-term memory** — facts extracted from past sessions, stored as semantic vectors\n",
    "\n",
    "When a customer sends a message, the agent retrieves relevant long-term memories\n",
    "and injects them into the prompt — so it *already knows* who you are.\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 1.4 — Agent Memory connectivity check
# ---------------------------------------------------------------------------
_memory_ok = False
print("Checking Agent Memory connectivity...\\n")

_am_phs = ("your-store-id-here", "your-agent-memory-api-key-here",
           "your-agent-memory-host.redis.io")
if any(v in _am_phs for v in [AGENT_MEMORY_STORE_ID, AGENT_MEMORY_API_KEY, AGENT_MEMORY_URL]):
    print("  ⚠️  Agent Memory credentials not set — update Section 1.1")
else:
    try:
        agent_memory = AgentMemory(
            AGENT_MEMORY_URL,
            store_id=AGENT_MEMORY_STORE_ID,
            api_key=AGENT_MEMORY_API_KEY,
        )
        health = agent_memory.health()
        print(f"  ✅ Agent Memory connected")
        print(f"     URL      : {AGENT_MEMORY_URL}")
        print(f"     Store ID : {AGENT_MEMORY_STORE_ID}")
        if hasattr(health, 'status'):
            print(f"     Status   : {health.status}")
        _memory_ok = True
    except Exception as e:
        print(f"  ❌ Agent Memory error: {e}")
        print("     → Check AGENT_MEMORY_URL, AGENT_MEMORY_STORE_ID, and AGENT_MEMORY_API_KEY")
        print("     → Verify the Agent Memory service is Active in Redis Cloud")

print()
if _memory_ok:
    print("✅ Agent Memory ready")
else:
    print("❌ Fix Agent Memory errors above before continuing.")
"""))

# --- 1.5 Context Retriever ---
cells.append(md(
    "### 1.5 — Test Context Retriever Connection\n",
    "\n",
    "Context Retriever exposes your Redis data as **governed tools** that the agent can call.\n",
    "Instead of writing raw Redis queries, the agent calls named tools like `get_order_status`\n",
    "and gets back structured, live data.\n",
    "\n",
    "The **MCP client** is how the agent calls those tools at runtime.\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 1.5 — Context Retriever connectivity check
# ---------------------------------------------------------------------------
_ctx_ok = False
print("Checking Context Retriever connectivity...\\n")

_cr_phs = ("your-admin-key-here", "your-agent-key-here",
           "your-context-surfaces-host.redis.io", "your-mcp-host.redis.io")
if any(v in _cr_phs for v in [CTX_ADMIN_KEY, CTX_AGENT_KEY, CTX_SURFACES_URL, CTX_MCP_URL]):
    print("  ⚠️  Context Retriever credentials not set — update Section 1.1")
else:
    try:
        # Admin client — used to manage surfaces (not called by the agent)
        ctx_admin = ContextSurfacesClient(base_url=CTX_SURFACES_URL)
        health = ctx_admin.health()
        print(f"  ✅ Context Retriever admin client connected")

        # MCP client — used by the agent to call tools at runtime
        mcp_client = MCPClient(mcp_url=CTX_MCP_URL, agent_key=CTX_AGENT_KEY)
        mcp_client.connect()
        mcp_client.initialize()
        tools = mcp_client.list_tools()
        print(f"  ✅ MCP client connected  ({len(tools)} tool(s) available)")
        for t in tools:
            name = t.get('name', '?')
            desc = t.get('description', '')[:60]
            print(f"     • {name}: {desc}")
        _ctx_ok = True
    except Exception as e:
        print(f"  ❌ Context Retriever error: {e}")
        print("     → Check CTX_SURFACES_URL, CTX_AGENT_KEY, and CTX_MCP_URL")
        print("     → Verify the Context Retriever service is Active in Redis Cloud")

print()
if _ctx_ok:
    print("✅ Context Retriever ready")
else:
    print("❌ Fix Context Retriever errors above before continuing.")
"""))

# --- 1.6 LangCache ---
cells.append(md("### 1.6 — LangCache (same as Workshop 1)\n"))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 1.6 — LangCache client initialisation
# ---------------------------------------------------------------------------
lang_cache = None
_lc_phs = ("your-cache-id-here", "your-langcache-api-key-here",
           "your-langcache-host.langcache.redis.io")
LANGCACHE_AVAILABLE = not any(v in _lc_phs for v in
                              [LANGCACHE_CACHE_ID, LANGCACHE_API_KEY, LANGCACHE_URL])

if LANGCACHE_AVAILABLE:
    try:
        lang_cache = LangCache(
            server_url=LANGCACHE_URL,
            cache_id=LANGCACHE_CACHE_ID,
            api_key=LANGCACHE_API_KEY,
        )
        print("✅ LangCache client initialised")
        print(f"   URL      : {LANGCACHE_URL}")
        print(f"   Cache ID : {LANGCACHE_CACHE_ID}")
        _cache_ok = True
    except Exception as e:
        print(f"❌ LangCache init failed: {e}")
        LANGCACHE_AVAILABLE = False
else:
    print("⚠️  LangCache credentials not provided — semantic caching will be skipped.")
    print("   Sections 9 and 10 will degrade gracefully.")
"""))

# ============================================================
# SECTION 2 — Load Live Data (Mocked RDI)
# ============================================================

cells.append(md(
    "---\n",
    "## Section 2 — Load Live Data (Mocked RDI)\n",
    "\n",
    "### How RDI Works in Production\n",
    "\n",
    "In a real Redis Eats deployment, **Redis Data Integration (RDI)** keeps Redis Cloud\n",
    "in sync with the operational database using Change Data Capture (CDC):\n",
    "\n",
    "```\n",
    "PostgreSQL / MySQL  →  RDI (CDC)  →  Redis Cloud  (near real-time, seconds)\n",
    "```\n",
    "\n",
    "When an order status changes in the database, RDI detects the change and propagates\n",
    "it to Redis within seconds — no polling, no stale data.\n",
    "\n",
    "### What We Do Instead\n",
    "\n",
    "For this workshop, we simulate the RDI-synced state by loading JSON files directly\n",
    "into Redis using the same key structure RDI would create. The agent sees exactly\n",
    "the same data it would see in production.\n",
    "\n",
    "**Key naming convention:**\n",
    "```\n",
    "redis-eats:customer:<customer_id>   → customer profile hash\n",
    "redis-eats:order:<order_id>         → order details hash\n",
    "redis-eats:restaurant:<restaurant_id> → restaurant info hash\n",
    "redis-eats:driver:<driver_id>       → driver status hash\n",
    "```\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 2 — Load operational data into Redis
# Prerequisite check
# ---------------------------------------------------------------------------
if r is None or not _redis_ok:
    raise RuntimeError(
        "Redis client not ready.\\n"
        "Run Section 1.2 (Redis connectivity check) first."
    )

from pathlib import Path

# Locate data directory (works in Colab and local)
CANDIDATE_DATA_DIRS = [
    Path("../data/source_json"),
    Path("data/source_json"),
    Path("/content/redis-eats-agentic-workshop/data/source_json"),
]
DATA_DIR = next((d for d in CANDIDATE_DATA_DIRS if d.exists()), None)
if DATA_DIR is None:
    raise FileNotFoundError(
        "data/source_json/ not found. "
        "Make sure the repo was cloned (run Colab Setup cell) "
        "or you are running from the repo root."
    )

print(f"Data directory: {DATA_DIR}\\n")

def load_entity(r, entity_type: str, json_file: str, id_field: str) -> int:
    \"\"\"
    Load entities from a JSON file into Redis as Hashes.

    Each record is written to:  redis-eats:<entity_type>:<id>

    Nested lists and dicts are JSON-serialised to strings so every
    Hash field is a plain Redis string.

    Args:
        r:           Redis client (decode_responses=True)
        entity_type: e.g. 'customer', 'order', 'restaurant', 'driver'
        json_file:   filename inside DATA_DIR
        id_field:    the dict key used as the unique identifier

    Returns:
        Number of records written.
    \"\"\"
    filepath = DATA_DIR / json_file
    if not filepath.exists():
        print(f"  ⚠️  {json_file} not found — skipping {entity_type}")
        return 0

    with open(filepath) as f:
        records = json.load(f)

    pipe = r.pipeline(transaction=False)
    for record in records:
        key = f"redis-eats:{entity_type}:{record[id_field]}"
        flat = {
            k: json.dumps(v) if isinstance(v, (list, dict)) else
               ("" if v is None else str(v))
            for k, v in record.items()
        }
        pipe.hset(key, mapping=flat)
    pipe.execute()
    return len(records)

# Load all four entity types
entities = [
    ("customer",   "customers.json",   "customer_id"),
    ("restaurant", "restaurants.json", "restaurant_id"),
    ("order",      "orders.json",      "order_id"),
    ("driver",     "drivers.json",     "driver_id"),
]

total = 0
for entity_type, json_file, id_field in entities:
    count = load_entity(r, entity_type, json_file, id_field)
    if count:
        print(f"  ✅ {entity_type:12s} {count:3d} records → redis-eats:{entity_type}:*")
    total += count

print(f"\\n✅ {total} total records loaded into Redis Cloud")
"""))

cells.append(md(
    "### Spot-check: Read One Record Back\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Spot-check — read a customer and an order back from Redis
# r.hmget() avoids any binary decode issues
# ---------------------------------------------------------------------------
# Customer
cust_key = "redis-eats:customer:cust-001"
name, tier, prefs, address = r.hmget(cust_key, "name", "loyalty_tier",
                                     "dietary_preferences", "address")
print("Customer cust-001:")
print(f"  Name    : {name}")
print(f"  Tier    : {tier}")
print(f"  Prefs   : {prefs}")
print(f"  Address : {address}")

print()

# Order
ord_key = "redis-eats:order:ord-1002"
customer_id, status, items, total, special = r.hmget(
    ord_key, "customer_id", "status", "items", "total", "special_instructions"
)
print("Order ord-1002:")
print(f"  Customer: {customer_id}")
print(f"  Status  : {status}")
print(f"  Items   : {items}")
print(f"  Total   : ${total}")
print(f"  Notes   : {special}")
"""))

cells.append(md(
    "> ### 🔍 Redis Insight — View the Live Data\n",
    ">\n",
    "> Browse your Redis Cloud database in Redis Insight. Search for:\n",
    ">\n",
    "> - `redis-eats:customer:*` — 8 customer Hashes\n",
    "> - `redis-eats:order:*` — 10 order Hashes (try `ord-1002` — it is currently `in_transit`)\n",
    "> - `redis-eats:restaurant:*` — 8 restaurants (try `rest-005` — it is `paused`)\n",
    "> - `redis-eats:driver:*` — 5 drivers\n",
    ">\n",
    "> This is exactly what RDI would have synced from your production database.\n",
    "> In production, any change in PostgreSQL would appear here within seconds.\n",
))

# ============================================================
# SECTION 3 — Check / Reload W1 Policy Index
# ============================================================

cells.append(md(
    "---\n",
    "## Section 3 — Check / Reload Workshop 1 Policy Index\n",
    "\n",
    "The agent can answer policy questions using the RAG pipeline built in Workshop 1.\n",
    "This cell checks whether the `redis-eats-chunks` index already exists in your\n",
    "Redis Cloud database.\n",
    "\n",
    "- **If it exists** — connect to it and continue.\n",
    "- **If it doesn't** — rebuild it automatically from the Workshop 1 PDFs.\n",
    "\n",
    "This makes Workshop 2 self-contained: you do not need to have completed\n",
    "Workshop 1 first, but if you did the index is ready to use immediately.\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 3 — Connect to or rebuild the Workshop 1 policy index
# ---------------------------------------------------------------------------
if r is None or not _redis_ok:
    raise RuntimeError("Redis client not ready — run Section 1.2 first.")
if openai_client is None or not _openai_ok:
    raise RuntimeError("OpenAI client not ready — run Section 1.3 first.")

W1_INDEX_NAME = "redis-eats-chunks"
W1_KEY_PREFIX = "redis-eats:chunk:"

# ---------------------------------------------------------------------------
# Schema definition (same as Workshop 1)
# ---------------------------------------------------------------------------
W1_SCHEMA_DICT = {
    "index": {
        "name": W1_INDEX_NAME,
        "prefix": W1_KEY_PREFIX,
        "storage_type": "hash",
    },
    "fields": [
        {"name": "text",        "type": "text"},
        {"name": "source",      "type": "tag"},
        {"name": "page_number", "type": "numeric"},
        {"name": "chunk_index", "type": "numeric"},
        {
            "name": "embedding", "type": "vector",
            "attrs": {
                "dims": 1536, "algorithm": "FLAT",
                "distance_metric": "COSINE", "datatype": "FLOAT32",
            },
        },
    ],
}
w1_schema = IndexSchema.from_dict(W1_SCHEMA_DICT)

# ---------------------------------------------------------------------------
# Check if index already exists using SearchIndex.exists()
# ---------------------------------------------------------------------------
policy_index = SearchIndex(w1_schema, redis_client=r)

if policy_index.exists():
    info = policy_index.info()
    doc_count = info.get("num_docs", "?")
    print(f"✅ Workshop 1 index '{W1_INDEX_NAME}' found ({doc_count} documents indexed)")
    print("   Skipping rebuild — continuing with existing index.")
else:
    print(f"ℹ️  Index '{W1_INDEX_NAME}' not found — rebuilding from Workshop 1 PDFs...\\n")

    # --- Locate PDFs ---
    PDF_CANDIDATES = [
        Path("../redis-eats-rag-workshop/data/pdfs"),
        Path("../../redis-eats-rag-workshop/data/pdfs"),
        Path("/content/redis-eats-rag-workshop/data/pdfs"),
    ]
    PDF_DIR = next((d for d in PDF_CANDIDATES if d.exists() and list(d.glob("*.pdf"))), None)

    if PDF_DIR is None:
        print("❌ Workshop 1 PDFs not found.")
        print("   Expected at: /content/redis-eats-rag-workshop/data/pdfs/")
        print("   Run the Workshop 1 Colab Setup cell to clone that repo, then re-run this cell.")
        raise FileNotFoundError("Workshop 1 PDF directory not found.")

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs in {PDF_DIR}")

    # --- Extract, chunk, embed ---
    def get_embedding_bytes(text: str) -> bytes:
        \"\"\"Embed text and return as FLOAT32 bytes for Redis VECTOR field.\"\"\"
        resp = openai_client.embeddings.create(model="text-embedding-3-small", input=text)
        return np.array(resp.data[0].embedding, dtype=np.float32).tobytes()

    def extract_text(pdf_path):
        pages = []
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for pg_num, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    pages.append({"text": text, "source": pdf_path.name, "page_number": pg_num})
        return pages

    def chunk_text(text, source, page_number, chunk_size=500, overlap=50):
        chunks, start, idx = [], 0, 0
        while start < len(text):
            chunks.append({
                "chunk_id": str(uuid.uuid4()), "text": text[start:start+chunk_size],
                "source": source, "page_number": page_number, "chunk_index": idx,
            })
            start += chunk_size - overlap
            idx   += 1
        return chunks

    all_chunks = []
    for pdf in tqdm(pdf_files, desc="Processing PDFs"):
        for page in extract_text(pdf):
            all_chunks.extend(chunk_text(page["text"], page["source"], page["page_number"]))

    print(f"\\n{len(all_chunks)} chunks extracted. Generating embeddings...")
    for chunk in tqdm(all_chunks, desc="Embedding"):
        chunk["embedding"] = get_embedding_bytes(chunk["text"])

    # --- Create index and load ---
    policy_index.create(overwrite=True)
    records = [{
        "id": c["chunk_id"], "text": c["text"], "source": c["source"],
        "page_number": c["page_number"], "chunk_index": c["chunk_index"],
        "embedding": c["embedding"],
    } for c in all_chunks]
    keys = policy_index.load(records, id_field="id")

    print(f"\\n✅ Policy index rebuilt: {len(keys)} chunks loaded into '{W1_INDEX_NAME}'")

# ---------------------------------------------------------------------------
# Confirm — define search helper used later by the policy tool
# ---------------------------------------------------------------------------
def search_policy_chunks(query: str, top_k: int = 4) -> List[Dict]:
    \"\"\"
    Search the W1 policy index for chunks relevant to the given query.
    Returns a list of result dicts with text, source, and score.
    \"\"\"
    q_bytes = np.array(
        openai_client.embeddings.create(
            model="text-embedding-3-small", input=query
        ).data[0].embedding,
        dtype=np.float32,
    ).tobytes()
    q = VectorQuery(
        vector=q_bytes,
        vector_field_name="embedding",
        return_fields=["text", "source", "page_number"],
        num_results=top_k,
    )
    return policy_index.query(q)

# Quick test
test_results = search_policy_chunks("Can I get a refund if my food arrived cold?", top_k=1)
if test_results:
    print(f"\\n✅ Policy search working — top result from '{test_results[0]['source']}'")
else:
    print("\\n⚠️  Policy search returned no results — check index doc count")
"""))

cells.append(md(
    "> ### 🔍 Redis Insight — Compare the Two Index Types\n",
    ">\n",
    "> In Redis Insight → Redis Query Engine you now have two indexes:\n",
    ">\n",
    "> | Index | Contents | Purpose |\n",
    "> |---|---|---|\n",
    "> | `redis-eats-chunks` | Policy PDF chunks (Workshop 1) | RAG policy answers |\n",
    "> | `redis-eats-router` | SemanticRouter utterances (created later) | Routing decisions |\n",
    ">\n",
    "> The same Redis Cloud database stores both document vectors and live operational data.\n",
    "> That's the Redis Iris advantage: one data layer for everything.\n",
))

# ============================================================
# SECTION 4 — Context Retriever
# ============================================================

cells.append(md(
    "---\n",
    "## Section 4 — Context Retriever\n",
    "\n",
    "### What Context Retriever Does\n",
    "\n",
    "Context Retriever turns your Redis data into **governed tools** that agents can call reliably.\n",
    "Instead of an agent writing arbitrary Redis queries (which could be slow, wrong, or unsafe),\n",
    "it calls named tools like `get_order_status` and receives structured, validated responses.\n",
    "\n",
    "```\n",
    "Agent                    Context Retriever              Redis Cloud\n",
    "  │                             │                           │\n",
    "  ├── call_tool('get_order_status', {order_id: 'ord-1002'}) ─►│\n",
    "  │                             │── HGETALL redis-eats:order:ord-1002 ─►│\n",
    "  │◄─ {'status': 'in_transit', 'items': [...], ...} ──────────│\n",
    "```\n",
    "\n",
    "The tools are defined in the Redis Cloud console once and then reused across sessions.\n",
    "You pre-provisioned this service before the workshop.\n",
    "\n",
    "### The MCP Protocol\n",
    "\n",
    "Context Retriever uses the **Model Context Protocol (MCP)** — a standard that lets\n",
    "AI agents discover and call tools through a consistent interface. The `MCPClient`\n",
    "handles the protocol details so your code just calls `call_tool(name, args)`.\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 4.1 — List available tools
# ---------------------------------------------------------------------------
if not _ctx_ok or mcp_client is None:
    raise RuntimeError(
        "Context Retriever not connected.\\n"
        "Run Section 1.5 (Context Retriever connectivity check) first."
    )

tools = mcp_client.list_tools()

print(f"Context Retriever has {len(tools)} tool(s) available:\\n")
for tool in tools:
    name   = tool.get("name", "?")
    desc   = tool.get("description", "")
    schema = tool.get("inputSchema", {}).get("properties", {})
    params = list(schema.keys())
    print(f"  🔧 {name}")
    print(f"     {desc}")
    print(f"     Parameters: {params}")
    print()
"""))

cells.append(md(
    "### 4.2 — Call a Tool Directly\n",
    "\n",
    "Before wiring tools into the agent, let's call one directly to see the raw response.\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 4.2 — Call a Context Retriever tool directly
#
# Call get_order_status for order ord-1002 (currently in_transit)
# to see the raw response before it goes through the agent.
# ---------------------------------------------------------------------------
print("Calling get_order_status for ord-1002...\\n")
try:
    result = mcp_client.call_tool("get_order_status", {"order_id": "ord-1002"})
    print("Raw tool response:")
    if isinstance(result, dict):
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        print(result)
except Exception as e:
    print(f"❌ Tool call failed: {e}")
    print("   → Verify the tool name matches what list_tools() returned above")
"""))

cells.append(md(
    "> ### 🔍 Redis Insight — The Tool and the Data\n",
    ">\n",
    "> The tool call you just made read `redis-eats:order:ord-1002` from Redis.\n",
    "> Open Redis Insight and browse that key to see the raw Hash.\n",
    "> Notice that `status` is `in_transit` — the agent will see this live value\n",
    "> every time it calls the tool.\n",
    ">\n",
    "> In production with RDI enabled, if the order status changed in the database\n",
    "> it would appear here within seconds — and the agent's next call would get\n",
    "> the updated status automatically.\n",
))

# ============================================================
# SECTION 5 — Agent Memory
# ============================================================

cells.append(md(
    "---\n",
    "## Section 5 — Agent Memory\n",
    "\n",
    "### The Two Memory Tiers\n",
    "\n",
    "Agent Memory provides two complementary layers:\n",
    "\n",
    "| Tier | What It Stores | How Long | Used For |\n",
    "|---|---|---|---|\n",
    "| **Session** | Current conversation turns | TTL-based | Conversation continuity |\n",
    "| **Long-term** | Facts about the customer | Persistent | Personalisation |\n",
    "\n",
    "When a customer asks a question, the agent:\n",
    "1. Searches long-term memory for relevant facts about this customer\n",
    "2. Injects those facts into the system prompt before calling the LLM\n",
    "3. After generating a response, stores the new turn in session memory\n",
    "\n",
    "This means the agent can say things like: *\"I see you prefer vegetarian options —\n",
    "here's the refund information for your order.\"*\n",
))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 5.1 — Session Memory
#
# Create a session for customer cust-001 (Alex Rivera)
# and add a conversation turn to it.
# ---------------------------------------------------------------------------
if not _memory_ok or agent_memory is None:
    raise RuntimeError(
        "Agent Memory not connected.\\n"
        "Run Section 1.4 (Agent Memory connectivity check) first."
    )

# Generate a stable session ID for our demo customer
DEMO_SESSION_ID   = f"redisvl-workshop-session-{uuid.uuid4().hex[:8]}"
DEMO_CUSTOMER_ID  = "cust-001"    # Alex Rivera

print(f"Creating session: {DEMO_SESSION_ID}\\n")

# Add a user turn to session memory
user_event = agent_memory.add_session_event(
    actor_id=DEMO_CUSTOMER_ID,
    session_id=DEMO_SESSION_ID,
    role=memory_models.MessageRole.USER,
    content=[{"text": "What happened to my last order?"}],
    created_at=datetime.now(timezone.utc),
)
print(f"✅ User turn stored  (event_id: {user_event.event_id if hasattr(user_event,'event_id') else 'ok'})")

# Add an assistant turn
agent_event = agent_memory.add_session_event(
    actor_id="redis-eats-agent",
    session_id=DEMO_SESSION_ID,
    role=memory_models.MessageRole.ASSISTANT,
    content=[{"text": "Your last order (ord-1001) was delivered on Jan 15. You gave it 5 stars!"}],
    created_at=datetime.now(timezone.utc),
)
print(f"✅ Agent turn stored (event_id: {agent_event.event_id if hasattr(agent_event,'event_id') else 'ok'})")

# Retrieve the session to confirm
session = agent_memory.get_session_memory(session_id=DEMO_SESSION_ID)
events  = session.events if hasattr(session, 'events') else []
print(f"\\nSession {DEMO_SESSION_ID} has {len(events)} event(s):")
for ev in events:
    role    = ev.role if hasattr(ev, 'role') else '?'
    content = ev.content[0].text if hasattr(ev, 'content') and ev.content else '?'
    print(f"  [{role}] {content[:80]}")
"""))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 5.2 — Long-term Memory
#
# Seed long-term memories for our demo customer cust-001.
# In production, these are extracted automatically from past sessions.
# For the workshop, we create them directly.
# ---------------------------------------------------------------------------
print(f"Seeding long-term memories for customer {DEMO_CUSTOMER_ID}...\\n")

memories_to_create = [
    {
        "text": "Customer prefers vegetarian food and never orders meat.",
        "topics": ["dietary", "preferences"],
    },
    {
        "text": "Customer is a Gold tier member with 47 orders since March 2022.",
        "topics": ["loyalty", "order_history"],
    },
    {
        "text": "Customer had a late delivery in January and was frustrated. Always follow up on delays.",
        "topics": ["service_history", "delays"],
    },
    {
        "text": "Customer loves Taco Loco (rest-001) and orders from there frequently.",
        "topics": ["preferences", "restaurants"],
    },
]

records = [
    memory_models.CreateMemoryRecord(
        text=m["text"],
        memory_type=memory_models.MemoryType.SEMANTIC,
        owner_id=DEMO_CUSTOMER_ID,
        session_id=DEMO_SESSION_ID,
        topics=m["topics"],
    )
    for m in memories_to_create
]

result = agent_memory.bulk_create_long_term_memories(memories=records)
print(f"✅ {len(records)} long-term memories created for {DEMO_CUSTOMER_ID}")
"""))

cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 5.3 — Search Long-term Memory
#
# This is what the agent does at the start of every conversation:
# search for relevant memories about this customer and inject them
# into the system prompt.
# ---------------------------------------------------------------------------
print("Searching long-term memory for context relevant to a delivery question...\\n")

search_request = memory_models.SearchLongTermMemoryRequestContent(
    text="customer preferences and delivery history",
    limit=3,
)

search_result = agent_memory.search_long_term_memory(request=search_request)
memories_found = search_result.memories if hasattr(search_result, 'memories') else []

print(f"Found {len(memories_found)} relevant memories:\\n")
for i, mem in enumerate(memories_found, 1):
    text = mem.text if hasattr(mem, 'text') else str(mem)
    print(f"  [{i}] {text}")

print()
print("These memories will be injected into the agent's system prompt in Section 8.")
print("The agent will personalise its responses based on this context.")

# ---------------------------------------------------------------------------
# Store the memory enrichment helper for use in the agent loop
# ---------------------------------------------------------------------------
def get_customer_memories(customer_id: str, query: str, limit: int = 3) -> List[str]:
    \"\"\"
    Retrieve long-term memories relevant to a query for a given customer.
    Returns a list of memory text strings to inject into the agent prompt.
    \"\"\"
    if not _memory_ok or agent_memory is None:
        return []
    try:
        result = agent_memory.search_long_term_memory(
            request=memory_models.SearchLongTermMemoryRequestContent(
                text=query, limit=limit,
            )
        )
        mems = result.memories if hasattr(result, 'memories') else []
        return [m.text for m in mems if hasattr(m, 'text')]
    except Exception:
        return []


def store_session_turn(session_id: str, customer_id: str,
                       user_msg: str, agent_msg: str) -> None:
    \"\"\"
    Store a conversation turn (user + agent) in session memory.
    Called after each agent response to maintain conversation history.
    \"\"\"
    if not _memory_ok or agent_memory is None:
        return
    try:
        ts = datetime.now(timezone.utc)
        agent_memory.add_session_event(
            actor_id=customer_id, session_id=session_id,
            role=memory_models.MessageRole.USER,
            content=[{"text": user_msg}], created_at=ts,
        )
        agent_memory.add_session_event(
            actor_id="redis-eats-agent", session_id=session_id,
            role=memory_models.MessageRole.ASSISTANT,
            content=[{"text": agent_msg}], created_at=ts,
        )
    except Exception:
        pass  # Memory store failure should not break the agent response


print("\\n✅ Memory helper functions defined — ready for Section 8")
"""))

# ============================================================
# Write notebook
# ============================================================

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
        "colab": {"provenance": [], "collapsed_sections": []},
    },
    "cells": cells,
}

OUTPUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False))
print(f"✅ Notebook written → {OUTPUT}")
print(f"   Cells: {len(cells)}")

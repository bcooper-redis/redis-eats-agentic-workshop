"""
patch_cell_descriptions.py

Inserts a short "what this cell does" markdown description immediately before
every code cell that currently lacks one. Works backwards through the cell
list so earlier insertions don't shift later indices.

Run:
    python3 scripts/patch_cell_descriptions.py
"""

import json, ast, sys
from pathlib import Path

NOTEBOOK = Path(__file__).parent.parent / "notebooks" / "redis_eats_agentic_workshop.ipynb"
nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [text]}

# ---------------------------------------------------------------------------
# Descriptions to insert — each entry is (cell_index_to_insert_before, text)
# Written in FORWARD order; the script reverses before applying.
# ---------------------------------------------------------------------------
INSERTS = [

    # -----------------------------------------------------------------------
    # Colab Setup (cell 0)
    # -----------------------------------------------------------------------
    (0, """\
> **🚀 Start here if you are running in Google Colab.**
> This cell clones the workshop repository so all data files are available.
> Run it once at the start of each session.
> If you are running locally, skip it — just make sure you are in the repo root.
"""),

    # -----------------------------------------------------------------------
    # Section 1 — pip install (cell 3)
    # -----------------------------------------------------------------------
    (3, """\
### 1a — Install Packages

**Run this cell first.** It checks which packages are already installed and
installs any that are missing.

> ⚠️ **If you see "ACTION REQUIRED: Restart the runtime":**
> Go to **Runtime → Restart session**, then run this cell again.
> It will show `✅ All packages ready` on the second run.
> After that, continue top to bottom — do not re-run cells you already passed.
"""),

    # -----------------------------------------------------------------------
    # Imports (cell 4)
    # -----------------------------------------------------------------------
    (4, """\
### 1b — Imports and Safe Defaults

Imports all Python libraries used throughout the workshop and initialises
key variables to safe defaults (`None` / `False`).

The connectivity cells below will overwrite these defaults once each service
is confirmed working. Any cell that depends on a service checks these flags
before running — so if a connectivity cell failed, you will get a clear
error rather than a confusing `AttributeError` later.
"""),

    # -----------------------------------------------------------------------
    # Section 2 — load_entity (cell 18)
    # -----------------------------------------------------------------------
    (18, """\
### 2a — Load Operational Data into Redis

**Run this cell to populate Redis with the workshop data.**

It loads four entity types from the `data/source_json/` folder into Redis
as Hashes — the same format and key structure that Redis Data Integration
(RDI) would create automatically from a relational database in production:

| Entity | Keys written | Records |
|---|---|---|
| Customers | `redis-eats:customer:*` | 8 |
| Restaurants | `redis-eats:restaurant:*` | 8 |
| Orders | `redis-eats:order:*` | 10 |
| Drivers | `redis-eats:driver:*` | 5 |

The agent tools in Section 6 read directly from these keys.
"""),

    # -----------------------------------------------------------------------
    # Section 3 — W1 index check (cell 23)
    # -----------------------------------------------------------------------
    (23, """\
### 3a — Connect to or Rebuild the Workshop 1 Policy Index

**Run this cell before continuing to Section 4.**

It checks whether the `redis-eats-chunks` vector index from Workshop 1 already
exists in your Redis Cloud database:

- **Found** → connects to it and confirms the document count. Takes under a second.
- **Not found** → rebuilds it automatically by loading the Workshop 1 PDFs,
  chunking the text, generating OpenAI embeddings, and indexing everything.
  This takes **2–4 minutes** — the progress bars show you where it is.

Either way, the `search_policy_chunks()` helper is defined at the end and
ready for the agent to use in Section 6.
"""),

    # -----------------------------------------------------------------------
    # Section 4 — list tools (cell 26)
    # -----------------------------------------------------------------------
    (26, """\
### 4.1 — List Available Tools

**Run this to see what tools the Context Retriever service exposes.**

`mcp_client.list_tools()` asks the Context Retriever service which tools
are available for this context surface. The tools were created by the
`setup_context_retriever.py` script run before the workshop — one tool
per entity (Order, Customer, Restaurant).

These are the exact tool names, descriptions, and parameters the OpenAI
function-calling loop will use in Sections 7–10. If this cell returns an
empty list, the setup script has not been run yet — see
`docs/CONTEXT_RETRIEVER_SETUP.md`.
"""),

    # -----------------------------------------------------------------------
    # Section 5 — session memory (cell 31)
    # -----------------------------------------------------------------------
    (31, """\
### 5.1 — Session Memory: Store and Retrieve a Conversation Turn

**Run this to see session memory in action.**

Stores two conversation events — a user message and an agent reply — in
the Agent Memory service for a demo session, then retrieves the full session
to confirm they are there.

Session memory is short-lived (TTL-based) and holds the current conversation.
The agent stores every turn here so it can refer back to earlier messages
within the same session.
"""),

    # -----------------------------------------------------------------------
    # Section 5 — seed long-term memories (cell 32)
    # -----------------------------------------------------------------------
    (32, """\
### 5.2a — Seed Long-term Memories for the Demo Customer

**Run this to pre-load facts about Alex Rivera (cust-001).**

In production, long-term memories are extracted automatically from past
sessions. For this workshop, we create them directly so the personalisation
demo in Section 8 works immediately.

Four facts are stored as semantic vectors in the Agent Memory service:
dietary preference, loyalty tier, delivery history, and favourite restaurant.
"""),

    # -----------------------------------------------------------------------
    # Section 5 — search long-term memory (cell 33)
    # -----------------------------------------------------------------------
    (33, """\
### 5.2b — Search Long-term Memory

**Run this to see how the agent retrieves customer context at query time.**

`search_long_term_memory()` performs a semantic search over all stored
memories for this customer and returns the most relevant ones for the given
query text. This is exactly what `run_agent_with_memory()` calls at the
start of every conversation in Section 8.

The `get_customer_memories()` and `store_session_turn()` helper functions
defined at the end are used throughout the rest of the workshop.
"""),

    # -----------------------------------------------------------------------
    # Section 6 — SemanticRouter (cell 35)
    # -----------------------------------------------------------------------
    (35, """\
### 6.1 — Set Up the Semantic Router

**Run this to initialise the out-of-domain guard.**

Creates a `SemanticRouter` in Redis with four routes (food delivery support,
account help, restaurant procedures, driver procedures). Questions that do not
match any route are refused immediately — before any tool is called or token
is spent.

This is the same routing pattern from Workshop 1, now integrated as the first
gate in the agent pipeline. The `ROUTING_THRESHOLD` and `REFUSAL_MESSAGE`
constants defined here are used throughout Sections 7–10.

> **Note:** This cell downloads the `all-mpnet-base-v2` sentence-transformers
> model on first run (~438 MB). This only happens once per Colab session.
"""),

    # -----------------------------------------------------------------------
    # Section 6 — tool schemas (cell 36)
    # -----------------------------------------------------------------------
    (36, """\
### 6.2 — Define OpenAI Tool Schemas

**Run this to tell the LLM what tools are available.**

Each schema is a JSON object that describes one tool to the OpenAI model:
its name, what it does, and what parameters it expects. The `description`
field is especially important — the model reads it to decide *when* to call
the tool. These schemas are passed to `openai_client.chat.completions.create()`
in the agent loop.

Five tools are defined here:
- `get_order_status` — live order data via Context Retriever
- `get_customer_profile` — customer data via Context Retriever
- `get_restaurant_info` — restaurant data via Context Retriever
- `search_policy` — policy answers via Workshop 1 RAG index
- `remember_fact` — write a new long-term memory to Agent Memory
"""),

    # -----------------------------------------------------------------------
    # Section 6 — execution functions (cell 37)
    # -----------------------------------------------------------------------
    (37, """\
### 6.3 — Define Tool Execution Functions

**Run this to wire the tool schemas to their actual implementations.**

Each function is called by the agent loop when the LLM requests that tool.
The Context Retriever tools try the MCP client first (the governed path),
then fall back to a direct Redis `HMGET` if the service is unavailable —
so the workshop continues even if there is a connectivity issue.

The `execute_tool()` dispatcher at the end maps tool names to functions.
This is what the agent loop calls with `tc.function.name` and
`json.loads(tc.function.arguments)`.
"""),

    # -----------------------------------------------------------------------
    # Section 7 — system prompt (cell 39)
    # -----------------------------------------------------------------------
    (39, """\
### 7.1 — Define the System Prompt

**Run this to set the agent's persona and rules.**

The system prompt is the instruction sent to the LLM as the `system` role
message at the start of every conversation. It defines who the agent is,
what it can and cannot do, and how it should behave.

Key rules in this prompt:
- Always use a tool to look up specific data — never guess
- Use `search_policy` for policy questions (refunds, delays, etc.)
- Include order IDs and source documents in responses
- If you cannot answer, say so honestly

The `BASE_SYSTEM_PROMPT` constant defined here is used in Section 7.
Section 8 extends it with injected long-term memory context.
"""),

    # -----------------------------------------------------------------------
    # Section 7 — run_agent function (cell 40)
    # -----------------------------------------------------------------------
    (40, """\
### 7.2 — Define the Agent Loop

**Run this to define the core `run_agent()` function.**

This is the heart of the workshop. `run_agent()` implements a standard
OpenAI function-calling loop:

1. SemanticRouter checks the question — refuses if out-of-domain
2. Sends the question + tool schemas to OpenAI
3. If the model returns tool calls: executes each tool, adds results to the
   message history, calls OpenAI again
4. Repeats until the model returns a plain text answer (no more tool calls)
5. Returns the final answer with a log of every tool that was called

No memory enrichment yet — that is added in Section 8.
"""),

    # -----------------------------------------------------------------------
    # Section 8 — memory-enriched agent (cell 45)
    # -----------------------------------------------------------------------
    (45, """\
### 8.1 — Define the Memory-Enriched Agent

**Run this to add Agent Memory to the agent loop.**

`run_agent_with_memory()` wraps the Section 7 loop with two additions:

**Before the loop:**
- Calls `get_customer_memories()` to search long-term memory for context
  relevant to this question
- Injects those memories into the system prompt so the agent already knows
  facts about this customer before it reads the question

**After the loop:**
- Calls `store_session_turn()` to save the user message and agent response
  in session memory for conversation continuity

Everything else is identical to `run_agent()` — same tools, same routing,
same function-calling loop.
"""),

    # -----------------------------------------------------------------------
    # Section 8 — multi-turn turn 2 (cell 50)
    # -----------------------------------------------------------------------
    (50, """\
### 8.3b — Turn 2: Follow-up Question

**Run this immediately after the Turn 1 cell above.**

This follow-up question refers to the order from Turn 1 without repeating
the order ID. The agent can answer in context because Turn 1 was stored in
session memory. Notice that `SESSION_ID` is shared between both cells —
that is what links the two turns together.
"""),

    # -----------------------------------------------------------------------
    # Section 9 — run_agent_with_cache (cell 53)
    # -----------------------------------------------------------------------
    (53, """\
### 9.1 — Define the LangCache-Wrapped Agent

**Run this to add semantic caching as the first gate in the pipeline.**

`run_agent_with_cache()` adds LangCache as a check *before* routing, memory,
and the agent loop. If a semantically similar question has been answered
before, the cached answer is returned instantly — no routing, no tool calls,
no LLM tokens.

On a cache miss, the full pipeline runs (`run_agent_with_memory()`) and the
answer is stored in LangCache for future similar questions.

The similarity threshold (`0.9` default) controls how closely two questions
must match to share a cache entry. Lower = more cache hits, higher = stricter.
"""),

    # -----------------------------------------------------------------------
    # Section 9 — 2nd cache call (cell 56)
    # -----------------------------------------------------------------------
    (56, """\
### 9.2b — Second Call: Expect a Cache Hit

**Run this immediately after the cell above.**

This question is semantically similar to the first one but worded differently.
LangCache should recognise the intent as equivalent and return the cached
answer instantly — observe the latency compared to the first call.

The `similarity_threshold` in `run_agent_with_cache()` determines how close
the phrasing needs to be. Adjust `CACHE_THRESHOLD` in the cell above and
re-run both cells to see the effect.
"""),

    # -----------------------------------------------------------------------
    # Section 10 — ask_bot (cell 58)
    # -----------------------------------------------------------------------
    (58, """\
### 10.1 — Define `ask_bot()` — The Complete Pipeline

**Run this to assemble the final single-function interface.**

`ask_bot()` is a thin wrapper around `run_agent_with_cache()` that presents
the complete four-component pipeline through one clean function call:

```
ask_bot(question, customer_id)
  → LangCache   → SemanticRouter   → Agent Memory   → Agent Loop   → Response
```

This is the function used for all demos and scenarios for the rest of the
workshop. It is intentionally simple — the complexity lives in the functions
defined in Sections 7–9.
"""),

    # -----------------------------------------------------------------------
    # Section 10 — full example battery (cell 59)
    # -----------------------------------------------------------------------
    (59, """\
### 10.2 — Run the Full Example Battery

**Run this to see all components working together in one pass.**

Runs five questions back to back using `verbose=False` to show a summary
table rather than step-by-step output. Each row shows whether the answer
came from cache (`📦 CACHED`) or the live pipeline (`🔄 LIVE`), which route
was matched, which tools were called, and a preview of the answer.

This is a good cell to run when demonstrating the full pipeline to an audience.
"""),

    # -----------------------------------------------------------------------
    # Section 12 — reset (cell 68)
    # -----------------------------------------------------------------------
    (68, """\
### 12a — Delete All Workshop Data from Redis

**Run this to clean up your Redis Cloud database.**

Deletes in order:
1. All `redis-eats:customer/order/restaurant/driver:*` keys (mocked RDI data)
2. The `redis-eats-chunks` vector search index + chunk keys (Workshop 1 data)
3. The `redis-eats-router` SemanticRouter index
4. The demo Agent Memory session

Your Redis Cloud database will be back to its pre-workshop state.
The Context Retriever context surface and Agent Memory long-term memories
are managed services — clear them separately in the Redis Cloud console
if needed.
"""),

    # -----------------------------------------------------------------------
    # Section 12 — verification (cell 69)
    # -----------------------------------------------------------------------
    (69, """\
### 12b — Verify the Cleanup

**Run this to confirm everything was removed.**

Scans for any remaining `redis-eats:*` keys and lists any workshop indexes
still present. Both should report clean (0 keys, no indexes).

Open Redis Insight and refresh — you should see an empty key space.
"""),
]

# ---------------------------------------------------------------------------
# Apply inserts in REVERSE order so earlier insertions don't shift later indices
# ---------------------------------------------------------------------------
for insert_before, description in sorted(INSERTS, key=lambda x: x[0], reverse=True):
    nb["cells"].insert(insert_before, md(description))

NOTEBOOK.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")

# ---------------------------------------------------------------------------
# Syntax check all code cells
# ---------------------------------------------------------------------------
errors = []
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        lines = [l for l in src.splitlines() if not l.startswith("%")]
        try:
            ast.parse("\n".join(lines))
        except SyntaxError as e:
            errors.append(f"Cell {i:02d}: {e}")

code_cells = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
md_cells   = sum(1 for c in nb["cells"] if c["cell_type"] == "markdown")

print(f"✅ {len(INSERTS)} description cells inserted")
print(f"   Total cells : {len(nb['cells'])}  ({code_cells} code, {md_cells} markdown)")
print("✅ All code cells pass syntax check" if not errors
      else "\n".join(f"❌ {e}" for e in errors))

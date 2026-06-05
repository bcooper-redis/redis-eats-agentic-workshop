"""
build_notebook_phase5.py

Appends Sections 9–13 to the Workshop 2 notebook:
  9  — Add LangCache (semantic caching in the agent pipeline)
  10 — Full Pipeline (all components together)
  11 — Live Scenarios (multi-turn realistic conversations)
  12 — Reset Lab
  13 — What Comes Next

Run AFTER build_notebook_phase4.py:
    python3 scripts/build_notebook_phase5.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NOTEBOOK  = REPO_ROOT / "notebooks" / "redis_eats_agentic_workshop.ipynb"


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}

def code(src):
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [], "source": [src]}


new_cells = []

# ============================================================
# SECTION 9 — Add LangCache
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 9 — Add LangCache\n",
    "\n",
    "### Where LangCache Fits in the Agent Pipeline\n",
    "\n",
    "In Workshop 1, LangCache was used for simple greeting-style inputs.\n",
    "In the full agent pipeline, it plays a more strategic role:\n",
    "\n",
    "```\n",
    "Question arrives\n",
    "  → LangCache search  ← NEW: check before routing or calling any tools\n",
    "      Cache HIT  → return instantly (no routing, no tools, no LLM call)\n",
    "      Cache MISS → run the full agent pipeline\n",
    "  → SemanticRouter\n",
    "  → Agent Memory enrichment\n",
    "  → Function-calling loop\n",
    "  → Answer + citations\n",
    "  → LangCache store  ← cache the response for next time\n",
    "  → Session memory store\n",
    "```\n",
    "\n",
    "This is especially valuable for support bots where customers repeatedly ask\n",
    "the same policy questions. Once the first customer asks about the refund policy\n",
    "for cold food, every subsequent semantically similar question gets an instant\n",
    "cached response — no tools, no embeddings, no LLM call.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 9.1 — LangCache wrapper for the agent pipeline
# ---------------------------------------------------------------------------

def run_agent_with_cache(
    question:        str,
    customer_id:     str   = "cust-001",
    session_id:      str   = None,
    cache_threshold: float = 0.9,
    verbose:         bool  = True,
) -> Dict[str, Any]:
    \"\"\"
    Run the agent with LangCache as the first check.

    If a semantically similar question has been answered before, the cached
    answer is returned immediately — skipping routing, memory, tools, and LLM.

    Cache threshold:
      0.95 = very strict (only near-identical questions hit the cache)
      0.90 = balanced default — good for policy questions
      0.85 = looser (more hits, small risk of irrelevant cache returns)

    Args:
        question:        The customer's question.
        customer_id:     Customer identifier.
        session_id:      Session ID for memory storage.
        cache_threshold: Cosine similarity threshold for cache lookup.
        verbose:         Print pipeline steps.

    Returns:
        Dict with 'answer', 'cache_hit', 'tools_called', 'route' keys.
    \"\"\"
    if session_id is None:
        session_id = f"redisvl-session-{uuid.uuid4().hex[:8]}"

    if verbose:
        print(f"\\n🤖 Redis Eats Agent (LangCache + Memory)")
        print(f"   Customer  : {customer_id}")
        print(f"   Question  : {question}")
        print()

    # --- Step 1: LangCache check ---
    if LANGCACHE_AVAILABLE and lang_cache is not None:
        try:
            cached = lang_cache.search(
                prompt=question,
                similarity_threshold=cache_threshold,
            )
            if cached.data:
                answer = cached.data[0].response
                if verbose:
                    print(f"   [cache]  → HIT  (similarity ≥ {cache_threshold})")
                    print(f"\\n   Answer: {answer}")
                    print(f"\\n   [cache]  → returned instantly — no LLM call made")
                return {
                    "answer":       answer,
                    "cache_hit":    True,
                    "tools_called": [],
                    "route":        "cached",
                }
            if verbose:
                print(f"   [cache]  → MISS — proceeding to agent pipeline")
        except Exception as e:
            if verbose:
                print(f"   [cache]  → error ({e}) — skipping cache, running agent")

    # --- Step 2: Full agent pipeline (with memory) ---
    result = run_agent_with_memory(
        question=question,
        customer_id=customer_id,
        session_id=session_id,
        verbose=verbose,
    )

    # --- Step 3: Store answer in LangCache for future similar questions ---
    if LANGCACHE_AVAILABLE and lang_cache is not None and result.get("route"):
        try:
            lang_cache.set(prompt=question, response=result["answer"])
            if verbose:
                print(f"   [cache]  → response stored (future similar questions will hit cache)")
        except Exception as e:
            if verbose:
                print(f"   [cache]  → store failed: {e}")

    result["cache_hit"] = False
    return result


print("✅ run_agent_with_cache() defined")
"""))

new_cells.append(md(
    "### 9.2 — Cache Miss Then Hit Demo\n",
    "\n",
    "Run this cell twice (or run it, then run the semantically similar question below).\n",
    "The first call is a cache miss — the full pipeline runs.\n",
    "The second similar question should be a cache hit.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 9.2 — First call: cache miss, full pipeline runs
# ---------------------------------------------------------------------------
print("FIRST CALL — expect CACHE MISS:")
print("=" * 65)
r1 = run_agent_with_cache(
    "What is your refund policy for cold food?",
    customer_id="cust-001",
    verbose=True,
)
"""))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Semantically similar question — expect CACHE HIT
# ---------------------------------------------------------------------------
import time

print("SECOND CALL — semantically similar, expect CACHE HIT:")
print("=" * 65)

start = time.time()
r2 = run_agent_with_cache(
    "Can I get my money back if my food arrived cold?",
    customer_id="cust-001",
    verbose=True,
)
elapsed = time.time() - start
print(f"\\n   Latency: {elapsed:.2f}s  ← compare to the first call above")
"""))

# ============================================================
# SECTION 10 — Full Pipeline
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 10 — Full Pipeline\n",
    "\n",
    "All four Redis Iris components are now integrated. Let's assemble\n",
    "the final `ask_bot()` function that runs the complete pipeline and\n",
    "wrap it with clean output formatting.\n",
    "\n",
    "```\n",
    "ask_bot(question, customer_id)\n",
    "    │\n",
    "    ├─► LangCache search          ← Redis Cloud (managed semantic cache)\n",
    "    │       ↓ MISS\n",
    "    ├─► SemanticRouter             ← RedisVL (route utterances in Redis)\n",
    "    │       ↓ in-domain\n",
    "    ├─► Agent Memory enrich        ← Redis Cloud (long-term memory vectors)\n",
    "    │       ↓ enriched prompt\n",
    "    ├─► OpenAI function-calling loop\n",
    "    │       ├─► get_order_status   ← Context Retriever → Redis Hash\n",
    "    │       ├─► get_customer_profile  ← Context Retriever → Redis Hash\n",
    "    │       ├─► get_restaurant_info   ← Context Retriever → Redis Hash\n",
    "    │       ├─► search_policy      ← RedisVL RAG → redis-eats-chunks index\n",
    "    │       └─► remember_fact      ← Agent Memory write\n",
    "    ├─► Session memory store       ← Redis Cloud (Agent Memory)\n",
    "    └─► LangCache store            ← Redis Cloud (LangCache)\n",
    "```\n",
    "\n",
    "Redis is at every step — not just as a cache, but as the intelligence layer.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 10.1 — ask_bot(): the final complete pipeline function
# ---------------------------------------------------------------------------

def ask_bot(
    question:        str,
    customer_id:     str   = "cust-001",
    session_id:      str   = None,
    cache_threshold: float = 0.9,
    verbose:         bool  = True,
) -> Dict[str, Any]:
    \"\"\"
    Don't Talk With Food In Your Mouth — Redis Eats Agentic Support Bot.

    Complete pipeline:
      1. LangCache    — instant answer if semantically cached
      2. Router       — refuse out-of-domain questions
      3. Memory enrich — personalise with long-term customer context
      4. Agent loop   — call tools, generate grounded answer
      5. Memory store — persist turn in session memory
      6. Cache store  — store answer for future similar questions

    All five Redis Iris components work together through a single Redis Cloud
    database and its managed services.

    Args:
        question:        Customer's question.
        customer_id:     Customer identifier.
        session_id:      Conversation session ID (auto-generated if None).
        cache_threshold: Semantic similarity threshold for LangCache.
        verbose:         Print pipeline steps.

    Returns:
        Dict with answer, cache_hit, tools_called, route, memories_used keys.
    \"\"\"
    return run_agent_with_cache(
        question=question,
        customer_id=customer_id,
        session_id=session_id,
        cache_threshold=cache_threshold,
        verbose=verbose,
    )


print("✅ ask_bot() is ready — the full Redis Iris pipeline in one call")
"""))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 10.2 — Run the full example set
# ---------------------------------------------------------------------------
print("Full pipeline test — five question types:\\n")

full_pipeline_questions = [
    ("What is the status of order ord-1002?",               "cust-002"),
    ("Can I get a refund if my food arrived cold?",          "cust-001"),
    ("Is Taco Loco currently accepting orders?",             "cust-001"),
    ("What should I do if my driver hasn't picked up yet?",  "cust-003"),
    ("Who won last night's basketball game?",                "cust-001"),
]

for question, customer_id in full_pipeline_questions:
    print("=" * 65)
    result = ask_bot(question, customer_id=customer_id, verbose=False)
    cache_indicator = "📦 CACHED" if result.get("cache_hit") else "🔄 LIVE"
    route = result.get("route") or "refused"
    tools = [t["tool"] for t in result.get("tools_called", [])]
    print(f"  {cache_indicator}  [{route}]")
    print(f"  Q: {question}")
    print(f"  Tools used: {tools if tools else 'none'}")
    print(f"  A: {result['answer'][:200]}{'...' if len(result['answer'])>200 else ''}")
    print()
"""))

# ============================================================
# SECTION 11 — Live Scenarios
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 11 — Live Scenarios\n",
    "\n",
    "Let's run three realistic multi-turn conversations that showcase\n",
    "all four Redis Iris components working together.\n",
    "\n",
    "| Scenario | Components Exercised |\n",
    "|---|---|\n",
    "| Delayed order + policy | Context Retriever + RAG + Agent Memory |\n",
    "| Returning customer | Long-term memory personalisation |\n",
    "| Mixed conversation | All components + out-of-domain routing |\n",
))

new_cells.append(md(
    "### Scenario 1 — Delayed Order\n",
    "\n",
    "Morgan Chen (cust-004) has an order that is delayed (ord-1004).\n",
    "She asks about the status, then asks about the delay policy.\n",
    "Watch how the agent uses both Context Retriever (live data) and RAG (policy) in the same conversation.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Scenario 1 — Delayed order: order lookup + policy question
# ---------------------------------------------------------------------------
S1_SESSION = f"scenario-1-{uuid.uuid4().hex[:6]}"
MORGAN     = "cust-004"

print("SCENARIO 1 — Morgan's Delayed Order")
print("=" * 65)

print("\\n--- Turn 1: Order status ---")
ask_bot(
    "What's happening with my order ord-1004? It's been a while.",
    customer_id=MORGAN,
    session_id=S1_SESSION,
    verbose=True,
)

print("\\n--- Turn 2: Policy question ---")
ask_bot(
    "That delay is really frustrating. What am I entitled to for a late delivery?",
    customer_id=MORGAN,
    session_id=S1_SESSION,
    verbose=True,
)
"""))

new_cells.append(md(
    "### Scenario 2 — Returning Customer\n",
    "\n",
    "Alex Rivera (cust-001) is a Gold member who is vegetarian and has had\n",
    "a delivery delay in the past. She asks about a restaurant.\n",
    "The agent should reference her preferences without her mentioning them.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Scenario 2 — Returning customer: long-term memory personalisation
# ---------------------------------------------------------------------------
S2_SESSION = f"scenario-2-{uuid.uuid4().hex[:6]}"
ALEX       = "cust-001"

print("SCENARIO 2 — Alex (returning Gold member, vegetarian)")
print("=" * 65)

print("\\n--- Turn 1: Restaurant recommendation ---")
ask_bot(
    "Can you tell me about Spice Garden? Is it a good option for tonight?",
    customer_id=ALEX,
    session_id=S2_SESSION,
    verbose=True,
)

print("\\n--- Turn 2: Follow-up with new preference ---")
ask_bot(
    "Great, I'll order from there. Also, just so you know — I'm also nut-free now.",
    customer_id=ALEX,
    session_id=S2_SESSION,
    verbose=True,
)
"""))

new_cells.append(md(
    "### Scenario 3 — Mixed Conversation with Refusal\n",
    "\n",
    "Sam Patel (cust-003) asks a valid question, then an off-topic one,\n",
    "then returns to a valid question. The router should intercept the\n",
    "off-topic message without disrupting the session.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Scenario 3 — Mixed: valid → out-of-domain → valid
# ---------------------------------------------------------------------------
S3_SESSION = f"scenario-3-{uuid.uuid4().hex[:6]}"
SAM        = "cust-003"

print("SCENARIO 3 — Sam (mixed valid + out-of-domain)")
print("=" * 65)

turns = [
    "How do promo codes work on Redis Eats?",
    "By the way, what do you think about the current stock market?",
    "OK back to my question — I'm a Platinum member, do I get better promo codes?",
]

for i, question in enumerate(turns, 1):
    print(f"\\n--- Turn {i} ---")
    ask_bot(question, customer_id=SAM, session_id=S3_SESSION, verbose=True)
"""))

# ============================================================
# SECTION 12 — Reset Lab
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 12 — Reset Lab\n",
    "\n",
    "Clean up everything this workshop wrote to your Redis Cloud database\n",
    "and managed services.\n",
    "\n",
    "**What gets deleted:**\n",
    "\n",
    "| Resource | What is removed |\n",
    "|---|---|\n",
    "| Redis keys `redis-eats:customer:*` | All customer Hashes |\n",
    "| Redis keys `redis-eats:order:*` | All order Hashes |\n",
    "| Redis keys `redis-eats:restaurant:*` | All restaurant Hashes |\n",
    "| Redis keys `redis-eats:driver:*` | All driver Hashes |\n",
    "| Redis keys `redis-eats:chunk:*` | Workshop 1 policy chunks |\n",
    "| Index `redis-eats-chunks` | Workshop 1 vector search index |\n",
    "| Index `redis-eats-router` | SemanticRouter index |\n",
    "| Agent Memory session | Demo session events |\n",
    "\n",
    "> ⚠️ **Agent Memory long-term memories** are stored in the managed Agent Memory service,\n",
    "> not directly in your Redis database. Use the Redis Cloud console or the\n",
    "> `agent_memory.bulk_delete_long_term_memories()` API to remove them if needed.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 12 — Reset Lab
# ---------------------------------------------------------------------------
if r is None or not _redis_ok:
    raise RuntimeError("Redis client not ready — run Section 1.2 first.")

import time

print("Starting Workshop 2 cleanup...\\n")

# --- Delete live data keys (the mocked RDI data) ---
live_entities = ["customer", "order", "restaurant", "driver"]
for entity in live_entities:
    keys = list(r.scan_iter(f"redis-eats:{entity}:*", count=500))
    if keys:
        r.delete(*keys)
        print(f"  ✅ Deleted {len(keys):3d} redis-eats:{entity}:* keys")
    else:
        print(f"  ✅ redis-eats:{entity}:*  (already clean)")

# --- Drop Workshop 1 policy index ---
try:
    policy_index.delete(drop=True)
    print("  ✅ Index 'redis-eats-chunks' dropped")
except Exception as e:
    print(f"  ⚠️  Index drop: {e}")

# --- Delete any remaining chunk keys ---
chunk_keys = list(r.scan_iter("redis-eats:chunk:*", count=500))
if chunk_keys:
    r.delete(*chunk_keys)
    print(f"  ✅ Deleted {len(chunk_keys)} stray chunk keys")

# --- Drop SemanticRouter ---
try:
    router.delete()
    print("  ✅ SemanticRouter 'redis-eats-router' deleted")
except Exception as e:
    print(f"  ⚠️  Router cleanup: {e}")

# --- Delete demo Agent Memory session ---
if _memory_ok and agent_memory is not None:
    try:
        agent_memory.delete_session_memory(session_id=DEMO_SESSION_ID)
        print(f"  ✅ Demo session memory deleted ({DEMO_SESSION_ID})")
    except Exception as e:
        print(f"  ⚠️  Session memory cleanup: {e}")

# --- Verify ---
time.sleep(0.5)
remaining = list(r.scan_iter("redis-eats:*", count=500))
if remaining:
    print(f"\\n⚠️  {len(remaining)} redis-eats:* keys still present:")
    for k in remaining[:5]:
        print(f"   {k}")
else:
    print("\\n✅ All redis-eats:* keys removed — database is clean")

print("\\n🏁 Reset complete.")
"""))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Final verification
# ---------------------------------------------------------------------------
count = sum(1 for _ in r.scan_iter("redis-eats:*", count=500))
print(f"Keys matching 'redis-eats:*' : {count}")

try:
    indexes = r.execute_command("FT._LIST")
    workshop_indexes = [str(idx) for idx in indexes if "redis-eats" in str(idx)]
    if workshop_indexes:
        print(f"Indexes still present       : {workshop_indexes}")
    else:
        print("Indexes                     : none (clean)")
except Exception:
    print("(Could not list indexes)")
"""))

new_cells.append(md(
    "> ### 🔍 Redis Insight — Confirm the Cleanup\n",
    ">\n",
    "> Refresh Redis Insight. You should see:\n",
    "> - **No keys** matching `redis-eats:*`\n",
    "> - **No indexes** named `redis-eats-chunks` or `redis-eats-router`\n",
    ">\n",
    "> Your Redis Cloud database is back to its pre-workshop state.\n",
    "> The Agent Memory service (long-term memories) is managed separately in Redis Cloud\n",
    "> and can be cleared from the Redis Cloud console if needed.\n",
))

# ============================================================
# SECTION 13 — What Comes Next
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 13 — What Comes Next\n",
    "\n",
    "Congratulations — you built a context-aware AI agent on Redis Cloud! 🎉\n",
    "\n",
    "### What You Accomplished in Workshop 2\n",
    "\n",
    "| ✅ | Skill |\n",
    "|---|---|\n",
    "| ✅ | Loaded live operational data into Redis (mocked RDI) |\n",
    "| ✅ | Connected to Context Retriever and called MCP tools |\n",
    "| ✅ | Defined OpenAI function-calling tool schemas |\n",
    "| ✅ | Built a ReAct-style agent loop with tool execution |\n",
    "| ✅ | Enriched agent prompts with Agent Memory (long-term) |\n",
    "| ✅ | Stored conversation history in Agent Memory (session) |\n",
    "| ✅ | Added LangCache for instant responses to repeated questions |\n",
    "| ✅ | Combined all components into a full production-shaped pipeline |\n",
    "| ✅ | Ran multi-turn realistic support conversations |\n",
    "\n",
    "---\n",
    "\n",
    "### The Complete Redis Iris Stack\n",
    "\n",
    "Across both workshops you have used the full Redis Iris Context Engine:\n",
    "\n",
    "| Component | Workshop | What It Did |\n",
    "|---|---|---|\n",
    "| **RedisVL + Vector Search** | 1 + 2 | Stored and searched policy chunk embeddings |\n",
    "| **SemanticRouter** | 1 + 2 | Filtered off-topic questions before LLM calls |\n",
    "| **LangCache** | 1 + 2 | Cached repeated answers instantly |\n",
    "| **Context Retriever** | 2 | Exposed live Redis data as governed agent tools |\n",
    "| **Agent Memory** | 2 | Personalised responses with persistent customer context |\n",
    "\n",
    "---\n",
    "\n",
    "### Where to Go From Here\n",
    "\n",
    "**Enable live RDI:**\n",
    "Replace the JSON loader with a real Redis Data Integration pipeline.\n",
    "Order status updates in your database will appear in Redis within seconds —\n",
    "and your agent will see them on the next tool call.\n",
    "\n",
    "**Add LangGraph:**\n",
    "The function-calling loop you built is the core of any agent framework.\n",
    "LangGraph adds state management, parallel tool calls, and conditional branching\n",
    "for more complex workflows.\n",
    "\n",
    "**Add more tools via Context Retriever:**\n",
    "Define new context surfaces for any Redis data — driver location, restaurant ratings,\n",
    "loyalty points, delivery zones — without changing agent code.\n",
    "\n",
    "**Scale to multi-agent:**\n",
    "Each agent type (support, driver-facing, restaurant-facing) can share the same\n",
    "Redis Cloud database but have separate context surfaces and memory stores.\n",
    "\n",
    "---\n",
    "\n",
    "### Keep Exploring\n",
    "\n",
    "- 📖 [Redis Iris documentation](https://redis.io/docs/latest/develop/ai/)\n",
    "- 📖 [Agent Memory docs](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/)\n",
    "- 📖 [Context Retriever docs](https://redis.io/docs/latest/develop/ai/context-engine/context-retriever/)\n",
    "- 📖 [RDI documentation](https://redis.io/docs/latest/develop/ai/context-engine/data-integration/)\n",
    "- 📖 [RedisVL documentation](https://docs.redisvl.com)\n",
    "- 🚀 [Redis Cloud free tier](https://redis.io/try-free)\n",
    "- 💻 [Redis Iris Demos on GitHub](https://github.com/redis/redis-iris-demos)\n",
    "\n",
    "Thanks for attending the Redis Eats workshops. Now go build something fast. 🚀\n",
))

# ============================================================
# Append to notebook
# ============================================================
nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
nb["cells"].extend(new_cells)
NOTEBOOK.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"✅ Sections 9–13 appended → {NOTEBOOK}")
print(f"   Total cells: {len(nb['cells'])}")

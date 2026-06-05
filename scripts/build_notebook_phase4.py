"""
build_notebook_phase4.py

Appends Sections 6–8 to the Workshop 2 notebook:
  6 — Tool Definitions (SemanticRouter + OpenAI function tool schemas)
  7 — Basic Agent Loop (function calling without memory)
  8 — Add Agent Memory (personalised, memory-enriched responses)

Run AFTER build_notebook.py:
    python3 scripts/build_notebook_phase4.py
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
# SECTION 6 — Tool Definitions
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 6 — Tool Definitions\n",
    "\n",
    "### What We Are Building\n",
    "\n",
    "The agent needs five tools — one for each type of question it can answer:\n",
    "\n",
    "| Tool | Data Source | What It Returns |\n",
    "|---|---|---|\n",
    "| `get_order_status` | Context Retriever → Redis | Current order status, items, ETA |\n",
    "| `get_customer_profile` | Context Retriever → Redis | Customer name, tier, preferences |\n",
    "| `get_restaurant_info` | Context Retriever → Redis | Restaurant status, menu, hours |\n",
    "| `search_policy` | RedisVL RAG → W1 index | Policy/procedure answers with citations |\n",
    "| `remember_fact` | Agent Memory | Stores a new long-term fact about the customer |\n",
    "\n",
    "Each tool has two parts:\n",
    "1. An **OpenAI tool schema** — tells the LLM what the tool does and what parameters it takes\n",
    "2. An **execution function** — runs the actual logic when the LLM calls the tool\n",
    "\n",
    "### Semantic Routing\n",
    "\n",
    "Before the agent loop runs, a `SemanticRouter` filters out off-topic questions.\n",
    "This is the same routing pattern from Workshop 1 — Redis still guards the pipeline.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 6.1 — Semantic Router (same as Workshop 1)
#
# Filters out-of-domain questions before they reach the agent loop.
# The router uses the same route definitions as Workshop 1.
# ---------------------------------------------------------------------------
import warnings, logging

warnings.filterwarnings("ignore")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

if r is None or not _redis_ok:
    raise RuntimeError("Redis client not ready — run Section 1.2 first.")

ROUTING_THRESHOLD = 0.5
REFUSAL_MESSAGE   = "I can't answer that question. I'm a food delivery support bot."

route_food_delivery = Route(
    name="food_delivery_support",
    distance_threshold=ROUTING_THRESHOLD,
    references=[
        "Can I get a refund for my order?",
        "My food arrived cold, what can I do?",
        "My order never arrived.",
        "What happens if my delivery is late?",
        "I want to cancel my order.",
        "My delivery is taking too long.",
        "Wrong items were delivered to me.",
        "How do I report a missing item?",
        "How do promo codes work?",
        "Is my food safe to eat?",
    ],
)

route_account = Route(
    name="account_and_login",
    distance_threshold=ROUTING_THRESHOLD,
    references=[
        "How do I reset my password?",
        "I can't log in to my account.",
        "How do I update my email address?",
        "How do I add a new payment method?",
        "I want to delete my account.",
        "My account has been locked.",
    ],
)

route_restaurant = Route(
    name="restaurant_procedures",
    distance_threshold=ROUTING_THRESHOLD,
    references=[
        "How do I pause orders on Redis Eats?",
        "How do I update my restaurant menu?",
        "How do I change my restaurant hours?",
        "How does restaurant onboarding work?",
        "When do restaurants get paid?",
    ],
)

route_driver = Route(
    name="driver_procedures",
    distance_threshold=ROUTING_THRESHOLD,
    references=[
        "How do I report a problem during a delivery?",
        "What do I do if the restaurant isn't ready?",
        "How does driver pay work?",
        "How do I contact driver support?",
        "How do I report a safety incident as a driver?",
    ],
)

router = SemanticRouter(
    name="redis-eats-router",
    routes=[route_food_delivery, route_account, route_restaurant, route_driver],
    redis_url=REDIS_URL,
    overwrite=True,
)

print(f"✅ SemanticRouter 'redis-eats-router' created")
print(f"   Routes           : {[r.name for r in router.routes]}")
print(f"   Routing threshold: {ROUTING_THRESHOLD}")
"""))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 6.2 — OpenAI Tool Schemas
#
# These JSON schemas tell the OpenAI model what each tool does, what
# parameters it expects, and which parameters are required.
# The model uses these to decide which tool to call and with what arguments.
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Look up the current status of a Redis Eats order. "
                "Use this when a customer asks about their order — status, items, "
                "estimated delivery time, or whether it has been delivered."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to look up (e.g. ord-1002)"
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_profile",
            "description": (
                "Retrieve a customer's profile including their name, loyalty tier, "
                "dietary preferences, and order history summary. "
                "Use this to personalise responses."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID (e.g. cust-001)"
                    }
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_info",
            "description": (
                "Retrieve information about a restaurant including its name, cuisine, "
                "current status (open/paused/closed), hours, and menu highlights. "
                "Use this when a customer asks about a specific restaurant."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "string",
                        "description": "The restaurant ID (e.g. rest-001)"
                    }
                },
                "required": ["restaurant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": (
                "Search the Redis Eats policy and procedure knowledge base. "
                "Use this for questions about refunds, cancellations, delivery delays, "
                "food safety, promo codes, account help, or customer support procedures."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The customer's policy question in their own words"
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": (
                "Store an important fact about the customer in long-term memory. "
                "Use this when the customer shares a preference, dietary requirement, "
                "or significant piece of information that should be remembered "
                "in future conversations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "The fact to remember about the customer"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "The customer's ID"
                    },
                },
                "required": ["fact", "customer_id"],
            },
        },
    },
]

print(f"✅ {len(TOOL_SCHEMAS)} tool schemas defined")
for t in TOOL_SCHEMAS:
    name = t["function"]["name"]
    params = list(t["function"]["parameters"]["properties"].keys())
    print(f"   🔧 {name}({', '.join(params)})")
"""))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 6.3 — Tool Execution Functions
#
# Each function is called by the agent loop when the LLM requests a tool.
# They return dicts that get serialised to JSON and added to the message
# history as a "tool" role message.
# ---------------------------------------------------------------------------

def get_order_status(order_id: str) -> dict:
    \"\"\"
    Fetch order details from Redis via the Context Retriever MCP tool.

    Falls back to a direct Redis HMGET if the MCP tool is unavailable,
    ensuring the workshop continues even without a Context Retriever service.

    Args:
        order_id: The order ID string (e.g. 'ord-1002')

    Returns:
        Dict with order fields or an error message.
    \"\"\"
    # Primary path: Context Retriever MCP tool
    if _ctx_ok and mcp_client is not None:
        try:
            return mcp_client.call_tool("get_order_status", {"order_id": order_id})
        except Exception:
            pass  # Fall through to direct Redis read

    # Fallback: read directly from Redis
    key = f"redis-eats:order:{order_id}"
    if not r.exists(key):
        return {"error": f"Order '{order_id}' not found."}
    fields = ["order_id", "customer_id", "restaurant_id", "driver_id",
              "status", "items", "total", "placed_at", "estimated_delivery_mins",
              "special_instructions", "delay_reason"]
    values = r.hmget(key, *fields)
    result = {k: v for k, v in zip(fields, values) if v}
    return result


def get_customer_profile(customer_id: str) -> dict:
    \"\"\"
    Fetch customer profile from Redis via Context Retriever or direct read.

    Args:
        customer_id: The customer ID string (e.g. 'cust-001')

    Returns:
        Dict with customer profile fields or an error message.
    \"\"\"
    if _ctx_ok and mcp_client is not None:
        try:
            return mcp_client.call_tool("get_customer_profile", {"customer_id": customer_id})
        except Exception:
            pass

    key = f"redis-eats:customer:{customer_id}"
    if not r.exists(key):
        return {"error": f"Customer '{customer_id}' not found."}
    fields = ["customer_id", "name", "email", "loyalty_tier",
              "dietary_preferences", "favorite_cuisines", "total_orders", "notes"]
    values = r.hmget(key, *fields)
    return {k: v for k, v in zip(fields, values) if v}


def get_restaurant_info(restaurant_id: str) -> dict:
    \"\"\"
    Fetch restaurant details from Redis via Context Retriever or direct read.

    Args:
        restaurant_id: The restaurant ID string (e.g. 'rest-001')

    Returns:
        Dict with restaurant fields or an error message.
    \"\"\"
    if _ctx_ok and mcp_client is not None:
        try:
            return mcp_client.call_tool("get_restaurant_info", {"restaurant_id": restaurant_id})
        except Exception:
            pass

    key = f"redis-eats:restaurant:{restaurant_id}"
    if not r.exists(key):
        return {"error": f"Restaurant '{restaurant_id}' not found."}
    fields = ["restaurant_id", "name", "cuisine", "status",
              "hours", "delivery_time_mins", "menu_highlights",
              "dietary_options", "rating"]
    values = r.hmget(key, *fields)
    return {k: v for k, v in zip(fields, values) if v}


def search_policy(question: str) -> dict:
    \"\"\"
    Search the Workshop 1 RAG knowledge base for policy/procedure answers.

    Retrieves the top relevant chunks and formats them as context.
    The agent will use this context to compose a grounded answer.

    Args:
        question: The customer's policy question.

    Returns:
        Dict with 'context' (policy text) and 'sources' (PDF filenames).
    \"\"\"
    results = search_policy_chunks(question, top_k=4)
    if not results:
        return {"context": "No relevant policy information found.", "sources": []}

    context_parts, seen_sources = [], set()
    for chunk in results:
        context_parts.append(
            f"[Source: {chunk['source']}, Page: {chunk['page_number']}]\\n{chunk['text']}"
        )
        seen_sources.add(chunk["source"])

    return {
        "context": "\\n\\n".join(context_parts),
        "sources": list(seen_sources),
    }


def remember_fact(fact: str, customer_id: str) -> dict:
    \"\"\"
    Store a new long-term memory for a customer in Agent Memory.

    Called when the agent learns something new about the customer
    that should persist across future conversations.

    Args:
        fact:        The fact string to store.
        customer_id: The customer's ID.

    Returns:
        Dict confirming storage or reporting an error.
    \"\"\"
    if not _memory_ok or agent_memory is None:
        return {"status": "skipped", "reason": "Agent Memory not available"}
    try:
        record = memory_models.CreateMemoryRecord(
            text=fact,
            memory_type=memory_models.MemoryType.SEMANTIC,
            owner_id=customer_id,
            topics=["learned_preference"],
        )
        agent_memory.bulk_create_long_term_memories(memories=[record])
        return {"status": "stored", "fact": fact, "customer_id": customer_id}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


# ---------------------------------------------------------------------------
# Tool dispatcher — maps tool name to function
# ---------------------------------------------------------------------------
TOOL_DISPATCH = {
    "get_order_status":     get_order_status,
    "get_customer_profile": get_customer_profile,
    "get_restaurant_info":  get_restaurant_info,
    "search_policy":        search_policy,
    "remember_fact":        remember_fact,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    \"\"\"
    Execute a tool by name with the given arguments.

    Called by the agent loop each time the LLM requests a tool call.
    Returns the tool result as a dict for JSON serialisation.

    Args:
        tool_name:  The name of the tool to execute.
        arguments:  Dict of keyword arguments for the tool.

    Returns:
        Tool result dict, or an error dict if the tool is unknown.
    \"\"\"
    fn = TOOL_DISPATCH.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: '{tool_name}'"}
    return fn(**arguments)


print("✅ Tool execution functions defined")
print(f"   Dispatch table: {list(TOOL_DISPATCH.keys())}")
"""))

# ============================================================
# SECTION 7 — Basic Agent Loop
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 7 — Basic Agent Loop\n",
    "\n",
    "### How OpenAI Function Calling Works\n",
    "\n",
    "The agent loop follows a simple ReAct-style pattern:\n",
    "\n",
    "```\n",
    "1. Send question + tool schemas to OpenAI\n",
    "2. If OpenAI returns tool_calls:\n",
    "     → Execute each tool\n",
    "     → Add tool results to message history\n",
    "     → Call OpenAI again with the updated history\n",
    "     → Repeat until no more tool calls\n",
    "3. When OpenAI returns a plain text response → that's the final answer\n",
    "```\n",
    "\n",
    "No LangGraph, no agent SDK, no extra dependencies — just the OpenAI chat API\n",
    "and a while loop. The tool schemas we defined in Section 6 guide the model's decisions.\n",
    "\n",
    "This section builds the agent **without** memory enrichment so you can clearly see\n",
    "the function-calling pattern before we add personalisation in Section 8.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 7.1 — Agent system prompt (no memory yet)
# ---------------------------------------------------------------------------

BASE_SYSTEM_PROMPT = \"\"\"You are Don't Talk With Food In Your Mouth, the Redis Eats customer support agent.

You have access to tools that let you look up live order data, customer profiles,
restaurant information, and policy documents. Use them to answer questions accurately.

Rules:
- Always use a tool to look up specific order, customer, or restaurant data.
  Do not guess or make up order statuses, names, or details.
- For policy questions (refunds, cancellations, delays, etc.), use search_policy.
- If you learn something important about a customer's preferences, use remember_fact.
- Include order IDs, restaurant names, or source documents in your response
  so the customer knows where the information came from.
- Be concise, friendly, and helpful.
- If you cannot answer from the available tools, say so honestly.
\"\"\"

print("✅ System prompt defined")
print(f"   Length: {len(BASE_SYSTEM_PROMPT)} characters")
"""))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 7.2 — The agent loop
# ---------------------------------------------------------------------------

def run_agent(
    question: str,
    customer_id: str = "cust-001",
    session_id: str  = None,
    verbose: bool    = True,
    max_turns: int   = 6,
) -> Dict[str, Any]:
    \"\"\"
    Run the Redis Eats support agent for a single customer question.

    Flow:
      1. SemanticRouter — refuse out-of-domain questions immediately
      2. OpenAI function-calling loop:
           a. Call OpenAI with the question + tool schemas
           b. Execute any requested tools
           c. Repeat until a plain text answer is returned
      3. Return answer + tool call log

    Memory enrichment is added in Section 8.

    Args:
        question:    The customer's question.
        customer_id: Customer identifier (used for tool calls and memory).
        session_id:  Optional session ID for memory storage.
        verbose:     Print step-by-step output.
        max_turns:   Maximum tool-call rounds before forcing a final answer.

    Returns:
        Dict with 'answer', 'tools_called', and 'route' keys.
    \"\"\"
    if verbose:
        print(f"\\n🤖 Redis Eats Agent")
        print(f"   Customer : {customer_id}")
        print(f"   Question : {question}")
        print()

    # --- Step 1: Semantic routing ---
    route_match = router(question)
    route_name  = route_match.name if route_match else None

    if route_name is None:
        if verbose:
            print(f"   [router] → out-of-domain — refused")
            print(f"\\n   Answer: {REFUSAL_MESSAGE}")
        return {"answer": REFUSAL_MESSAGE, "tools_called": [], "route": None}

    if verbose:
        print(f"   [router] → {route_name}")

    # --- Step 2: Function-calling loop ---
    messages = [
        {"role": "system",  "content": BASE_SYSTEM_PROMPT},
        {"role": "user",    "content": question},
    ]
    tools_called = []
    turn = 0

    while turn < max_turns:
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = response.choices[0].message

        # No tool calls — final answer ready
        if not msg.tool_calls:
            answer = msg.content
            if verbose:
                print(f"   [agent] → final answer (after {turn} tool round(s))")
                print(f"\\n   Answer: {answer}")
            return {"answer": answer, "tools_called": tools_called, "route": route_name}

        # Execute each requested tool
        messages.append(msg)   # add the assistant message with tool_calls

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)

            if verbose:
                print(f"   [tool]  → {name}({args})")

            result = execute_tool(name, args)
            tools_called.append({"tool": name, "args": args, "result": result})

            if verbose:
                # Print a brief result summary
                summary = str(result)[:120].replace("\\n", " ")
                print(f"           ← {summary}...")

            # Add tool result to message history
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      json.dumps(result),
            })

        turn += 1

    # Safety net — too many turns
    final = openai_client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, temperature=0.2,
    ).choices[0].message.content
    return {"answer": final, "tools_called": tools_called, "route": route_name}


print("✅ run_agent() defined — ready for testing")
"""))

new_cells.append(md(
    "### 7.3 — Test the Basic Agent\n",
    "\n",
    "Let's run a few questions to see the function-calling loop in action.\n",
    "Watch the tool calls logged below — the agent decides which tools to call\n",
    "based on the question, not hard-coded logic.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 7.3 — Test queries: order lookup, policy question, out-of-domain
# ---------------------------------------------------------------------------
test_questions = [
    ("What is the status of order ord-1002?",        "Order lookup via Context Retriever"),
    ("Can I get a refund if my food arrived cold?",  "Policy question via RAG"),
    ("Is Seoul Kitchen currently accepting orders?", "Restaurant lookup via Context Retriever"),
    ("What is the capital of France?",               "Out-of-domain — should be refused"),
]

for question, label in test_questions:
    print("=" * 65)
    print(f"  [{label}]")
    result = run_agent(question, customer_id="cust-001", verbose=True)
    print()
"""))

new_cells.append(md(
    "### ✅ Checkpoint — What You Just Saw\n",
    "\n",
    "- **Order lookup** called `get_order_status` via Context Retriever → Redis Hash\n",
    "- **Policy question** called `search_policy` → RAG → Workshop 1 vector index\n",
    "- **Restaurant lookup** called `get_restaurant_info` → Redis Hash\n",
    "- **Out-of-domain** was refused by SemanticRouter before any tool was called\n",
    "\n",
    "Notice that the agent decided *which* tool to call based on the question — you\n",
    "didn't write any routing logic for this. The tool schemas you defined in Section 6\n",
    "are what guided the model's decisions.\n",
    "\n",
    "One thing is missing: the agent doesn't know who Alex Rivera is, doesn't remember\n",
    "her preference for vegetarian food, and won't recall this conversation next time.\n",
    "Section 8 fixes that.\n",
))

# ============================================================
# SECTION 8 — Add Agent Memory
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 8 — Add Agent Memory\n",
    "\n",
    "### What Changes With Memory\n",
    "\n",
    "Right now the agent answers correctly, but it treats every customer as a stranger.\n",
    "With Agent Memory, the pipeline becomes:\n",
    "\n",
    "```\n",
    "Question arrives\n",
    "  → Fetch long-term memories about this customer from Agent Memory\n",
    "  → Inject them into the system prompt\n",
    "  → Run the function-calling loop (same as before)\n",
    "  → Store the conversation turn in session memory\n",
    "  → Return grounded, personalised answer\n",
    "```\n",
    "\n",
    "The long-term memories we seeded in Section 5 will now flow into the agent's\n",
    "context automatically — the agent will know Alex is vegetarian, a Gold member,\n",
    "and sensitive about delays before she even mentions it.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 8.1 — Memory-enriched agent loop
# ---------------------------------------------------------------------------

def run_agent_with_memory(
    question:    str,
    customer_id: str  = "cust-001",
    session_id:  str  = None,
    verbose:     bool = True,
    max_turns:   int  = 6,
) -> Dict[str, Any]:
    \"\"\"
    Run the Redis Eats agent with full Agent Memory integration.

    Adds two steps around the base agent loop:
      BEFORE: search long-term memory for relevant customer context
              and inject it into the system prompt
      AFTER:  store the conversation turn in session memory

    Args:
        question:    The customer's question.
        customer_id: Customer identifier for memory lookup and storage.
        session_id:  Session ID for conversation continuity.
                     Auto-generated if not provided.
        verbose:     Print step-by-step output.
        max_turns:   Maximum tool-call rounds.

    Returns:
        Dict with 'answer', 'tools_called', 'route', and 'memories_used' keys.
    \"\"\"
    if session_id is None:
        session_id = f"redisvl-session-{uuid.uuid4().hex[:8]}"

    if verbose:
        print(f"\\n🤖 Redis Eats Agent (with Memory)")
        print(f"   Customer  : {customer_id}")
        print(f"   Session   : {session_id}")
        print(f"   Question  : {question}")
        print()

    # --- Step 1: Semantic routing ---
    route_match = router(question)
    route_name  = route_match.name if route_match else None

    if route_name is None:
        if verbose:
            print(f"   [router] → out-of-domain — refused")
            print(f"\\n   Answer: {REFUSAL_MESSAGE}")
        return {
            "answer": REFUSAL_MESSAGE, "tools_called": [],
            "route": None, "memories_used": [],
        }

    if verbose:
        print(f"   [router] → {route_name}")

    # --- Step 2: Fetch long-term memories ---
    memories = get_customer_memories(customer_id, question, limit=3)

    if verbose:
        if memories:
            print(f"   [memory] → {len(memories)} relevant memorie(s) retrieved:")
            for m in memories:
                print(f"             • {m[:80]}")
        else:
            print("   [memory] → no relevant memories found")

    # --- Step 3: Build memory-enriched system prompt ---
    if memories:
        memory_context = "\\n".join(f"- {m}" for m in memories)
        enriched_prompt = (
            f"{BASE_SYSTEM_PROMPT}\\n\\n"
            f"What you already know about this customer:\\n{memory_context}\\n\\n"
            f"Use this context to personalise your response where appropriate."
        )
    else:
        enriched_prompt = BASE_SYSTEM_PROMPT

    # --- Step 4: Function-calling loop (same as Section 7, enriched prompt) ---
    messages = [
        {"role": "system", "content": enriched_prompt},
        {"role": "user",   "content": question},
    ]
    tools_called = []
    turn = 0

    while turn < max_turns:
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            answer = msg.content
            if verbose:
                print(f"   [agent]  → final answer (after {turn} tool round(s))")
                print(f"\\n   Answer: {answer}")
            break

        messages.append(msg)
        for tc in msg.tool_calls:
            name   = tc.function.name
            args   = json.loads(tc.function.arguments)
            result = execute_tool(name, args)
            tools_called.append({"tool": name, "args": args})

            if verbose:
                print(f"   [tool]   → {name}({args})")

            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      json.dumps(result),
            })
        turn += 1
    else:
        answer = openai_client.chat.completions.create(
            model=CHAT_MODEL, messages=messages, temperature=0.2,
        ).choices[0].message.content

    # --- Step 5: Store conversation turn in session memory ---
    store_session_turn(session_id, customer_id, question, answer)
    if verbose:
        print(f"\\n   [memory] → turn stored in session {session_id}")

    return {
        "answer":        answer,
        "tools_called":  tools_called,
        "route":         route_name,
        "memories_used": memories,
    }


print("✅ run_agent_with_memory() defined")
"""))

new_cells.append(md(
    "### 8.2 — Compare: Without Memory vs With Memory\n",
    "\n",
    "Let's ask the same question both ways and compare the responses.\n",
    "The question doesn't mention dietary preferences — but the memory-enriched\n",
    "agent should incorporate that context anyway.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 8.2 — Side-by-side comparison
# ---------------------------------------------------------------------------
question = "My order just arrived — the food looks good but I want to double-check it's safe."

print("WITHOUT MEMORY:")
print("=" * 65)
result_no_mem = run_agent(question, customer_id="cust-001", verbose=False)
print(f"Answer: {result_no_mem['answer']}")
print()

print("WITH MEMORY:")
print("=" * 65)
result_mem = run_agent_with_memory(question, customer_id="cust-001", verbose=True)
"""))

new_cells.append(md(
    "### 8.3 — Multi-turn Conversation\n",
    "\n",
    "Because each turn is stored in session memory, the agent maintains\n",
    "conversation context across multiple messages in the same session.\n",
    "\n",
    "Run the cells below in sequence — the second question refers back\n",
    "to the first without explicitly repeating the order ID.\n",
))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Section 8.3 — Multi-turn: start a new session for cust-001
# ---------------------------------------------------------------------------
SESSION_ID = f"redisvl-demo-{uuid.uuid4().hex[:8]}"
print(f"Session ID: {SESSION_ID}\\n")

# Turn 1
print("TURN 1")
print("=" * 65)
t1 = run_agent_with_memory(
    "What is the current status of my order ord-1002?",
    customer_id="cust-001",
    session_id=SESSION_ID,
    verbose=True,
)
"""))

new_cells.append(code("""\
# ---------------------------------------------------------------------------
# Turn 2 — follow-up that depends on knowing the previous context
# ---------------------------------------------------------------------------
print("TURN 2")
print("=" * 65)
t2 = run_agent_with_memory(
    "And what is the refund policy if it arrives cold?",
    customer_id="cust-001",
    session_id=SESSION_ID,
    verbose=True,
)
"""))

new_cells.append(md(
    "> ### 🔍 Redis Insight — Session Memory in Redis\n",
    ">\n",
    "> Agent Memory stores session events in your Redis Cloud database.\n",
    "> Browse the keys — you should see entries related to the session you just created.\n",
    ">\n",
    "> Each turn (user + agent message) is stored as a structured event with:\n",
    "> - `actor_id` — who said it (customer ID or 'redis-eats-agent')\n",
    "> - `role` — USER or ASSISTANT\n",
    "> - `content` — the message text\n",
    "> - `created_at` — timestamp\n",
    ">\n",
    "> Long-term memories (the facts we seeded in Section 5) are stored as separate\n",
    "> semantic vectors — searchable by meaning, not just by key.\n",
))

# ============================================================
# Append to notebook
# ============================================================

nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
nb["cells"].extend(new_cells)
NOTEBOOK.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"✅ Sections 6–8 appended → {NOTEBOOK}")
print(f"   Total cells: {len(nb['cells'])}")

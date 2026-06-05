# Redis Eats Agentic Workshop — Instructor Guide

> **⚠️ Not for attendees.** This document is for instructors only.

---

## 1. Workshop Overview

### Session Goal

Teach developers and Redis customers how to build a context-aware AI agent using the full Redis Iris Context Engine — Agent Memory, Context Retriever, LangCache, and RedisVL — in 2.5 to 3 hours.

By the end, every attendee should have a working agentic pipeline that knows who the customer is, looks up live data, answers policy questions, and remembers conversations.

### Target Audience

- Developers who completed Workshop 1 (RAG Chatbot) or have equivalent Redis/RAG experience
- Redis customers evaluating Redis Iris for production agent workloads
- Developers building AI agents who want to understand the Redis context layer

### Expected Background

| Assumption | Detail |
|---|---|
| Workshop 1 | Completed or familiar with RedisVL, vector search, LangCache basics |
| Python | Comfortable with async/await not required — everything is synchronous |
| Agents | No prior agent framework experience required |
| Redis Cloud | Has a working database from Workshop 1 |

### Required Pre-Provisioning (Attendees Complete Before the Session)

1. Redis Cloud database (from Workshop 1 — same instance)
2. OpenAI API key with credits
3. Agent Memory service — Redis Cloud → Context Engine → Agent Memory
4. Context Retriever service — Redis Cloud → Context Engine → Context Retriever
5. LangCache — same instance as Workshop 1

> **Action item:** Send a setup checklist to attendees 48 hours before the workshop. Provisioning Agent Memory and Context Retriever takes 5–10 minutes but needs to be done in advance.

### What Attendees Build

A context-aware Redis Eats support agent that:
- Knows customer preferences from long-term memory
- Looks up live order/restaurant data via Context Retriever tools
- Answers policy questions via the Workshop 1 RAG knowledge base
- Refuses off-topic questions via SemanticRouter
- Avoids redundant LLM calls via LangCache

### What Is Out of Scope

- LangGraph or other agent orchestration frameworks
- Live RDI CDC (mocked with a Python script)
- Multi-agent systems
- Redis Flex, FeatureForm, Redis Iris production configuration

---

## 2. Timing Plan

Total target: **2.5–3 hours**

| Section | Content | Time |
|---|---|---|
| Pre-start | Verify all 5 services provisioned, Colab connected | Before session |
| **0 — Welcome** | W1 recap, what W2 adds, architecture walkthrough | 10 min |
| **1 — Setup** | pip install, all 5 credential groups, connectivity tests | 15 min |
| **2 — Live Data** | Load JSON into Redis, explain RDI production pattern | 10 min |
| **3 — Policy Index** | Check/reload W1 index, confirm search works | 5 min |
| **4 — Context Retriever** | List tools, call a tool directly, explain MCP pattern | 15 min |
| **5 — Agent Memory** | Session events, long-term memory, seed demo memories | 20 min |
| **6 — Tool Definitions** | Router setup, OpenAI tool schemas, execution functions | 15 min |
| **7 — Basic Agent Loop** | Function calling, test questions, explain the loop | 20 min |
| **8 — Add Memory** | Memory-enriched prompt, before/after comparison, multi-turn | 20 min |
| **9 — LangCache** | Cache miss/hit demo, latency comparison | 10 min |
| **10 — Full Pipeline** | `ask_bot()`, complete example battery | 10 min |
| **11 — Live Scenarios** | Three multi-turn conversations | 15 min |
| **12 — Reset Lab** | Cleanup | 5 min |
| **13 — What's Next** | RDI production, LangGraph, multi-agent | 5 min |
| **Buffer / Q&A** | Questions, stuck attendees | 15 min |
| **Total** | | **~2h 50min** |

> **Tip:** Sections 2 and 3 can overlap — start the policy index reload running (it takes a few minutes) while you talk through the RDI narrative.

---

## 3. Instructor Talk Track

### Section 0 — Welcome (10 min)

**Say:**
> "In Workshop 1 we built a chatbot that answers policy questions. It's good but it has a problem: it doesn't know who you are. Every conversation starts from zero. It can't look up your actual order. It doesn't remember you're vegetarian or that you had a frustrating delay last month.
>
> Workshop 2 fixes that. We're going to add four more Redis capabilities that transform the chatbot into a real agent. By the end of this session, the bot will know who you are, look up your live order data, remember your preferences, and skip redundant LLM calls — all through Redis Cloud."

**Walk through the architecture diagram.** Point at each component:
- "LangCache is the first gate — if we've answered this before, we return instantly"
- "SemanticRouter is the second gate — off-topic gets refused immediately"
- "Agent Memory enriches the prompt before we call the model"
- "The function-calling loop decides which tools to call — we don't hard-code that"
- "Context Retriever is what connects the tools to your live Redis data"
- "Redis Cloud sits behind all of it — one database powering the whole pipeline"

---

### Section 1 — Setup (15 min)

**Say:**
> "This workshop has more credentials than Workshop 1. You need five things — Redis, OpenAI, Agent Memory, Context Retriever, and LangCache. All of these should be provisioned and ready."

**Where to pause:**
- After credential cell — confirm no placeholder warnings before moving on
- After Agent Memory check (Section 1.4) — this is the most common connection failure point
- After Context Retriever check (Section 1.5) — confirm tools are listed

**Common issue:** Context Retriever MCP URL is different from the admin URL. Attendees often paste the wrong one. The MCP URL is shown separately in the Redis Cloud console.

**Redis positioning:**
> "Notice that Agent Memory, Context Retriever, and LangCache are all managed services that live on Redis Cloud. You're not running separate infrastructure for each — they're all part of the same Redis platform."

---

### Section 2 — Live Data (10 min)

**Say:**
> "Before the agent can look up orders or customer profiles, we need data in Redis. In production, Redis Data Integration — RDI — handles this automatically using Change Data Capture. Any change in your PostgreSQL or MySQL database propagates to Redis within seconds. For this workshop, we simulate that with a Python script that loads JSON files using the same key structure RDI would create."

**Point at the key naming:**
> "Notice the pattern: `redis-eats:customer:cust-001`, `redis-eats:order:ord-1002`. This is the same prefix convention we used in Workshop 1 for `redis-eats:chunk:*`. One namespace, consistent across all data types."

**Show Redis Insight** with the customer and order Hashes visible.

---

### Section 3 — Policy Index (5 min)

**Say:**
> "This cell checks whether the Workshop 1 vector index already exists. If you ran Workshop 1 on the same database and didn't reset, it's still there and we connect to it in under a second. If not, we rebuild it automatically. Either way, the agent has access to the full policy knowledge base."

**Expected questions:**
- *"Do I need Workshop 1 first?"* → "No — this cell makes Workshop 2 self-contained."

---

### Section 4 — Context Retriever (15 min)

**Say:**
> "Context Retriever is the component that makes Redis data available to agents through a governed interface. Instead of the agent running arbitrary Redis queries — which could be wrong, slow, or unsafe — it calls named tools and gets back structured responses."

**Walk through `list_tools()` output:**
> "The tools you see here were defined in the Redis Cloud console when you provisioned the Context Retriever service. The agent doesn't know how they work internally — it just calls `get_order_status` with an order ID and gets back the order data. The schema is what governs access."

**Run `call_tool()` directly:**
> "Watch what happens. The MCP client sends the call to the Context Retriever service, which reads the `redis-eats:order:ord-1002` Hash from Redis and returns it as structured JSON. The agent gets clean, typed data — not raw Redis output."

**Expected questions:**
- *"What's MCP?"* → "Model Context Protocol — a standard that lets agents discover and call tools through a consistent interface. It's the same protocol Claude uses with MCP servers. Context Retriever exposes your Redis data through MCP."
- *"Can I add more tools without changing agent code?"* → "Yes — define a new context surface in the Redis Cloud console and it appears in `list_tools()` automatically."

---

### Section 5 — Agent Memory (20 min)

**Say:**
> "Agent Memory gives agents two types of memory — session and long-term. Session memory is the current conversation. Long-term memory is facts about the customer that persist across sessions."

**Walk through session events:**
> "We're calling `add_session_event()` with a role — USER, ASSISTANT, or SYSTEM. This stores the conversation turn in the Agent Memory service. At the start of the next session, the agent can retrieve these events to understand the conversation context."

**Walk through long-term memory:**
> "Now we're seeding facts about Alex Rivera: she's vegetarian, she's a Gold member, she had a frustrating delay. These get stored as semantic vectors. When Alex asks a question next time, we search these memories for the most relevant ones and inject them into the system prompt. The agent already knows things about Alex before she says a word."

**Key Redis positioning:**
> "Long-term memories are stored as vectors — the same technology as the Workshop 1 RAG index. Agent Memory is Redis doing what it does for document search, but for customer facts."

---

### Section 6 — Tool Definitions (15 min)

**Say:**
> "We need two things for each tool: a schema that tells the model what the tool does and what parameters it takes, and a function that actually runs when the model calls it."

**Walk through a tool schema:**
> "The description field is critical — this is what the model reads to decide whether to call this tool. Be specific. 'Look up the current status of a Redis Eats order' is much better than 'get order'. The model uses this description every time it decides which tool to call."

**Walk through execution function:**
> "Each execution function tries the MCP client first — that's the governed path through Context Retriever. If the MCP client isn't available, it falls back to a direct Redis HMGET. This makes the workshop resilient, but in production you'd use the MCP path exclusively."

---

### Section 7 — Basic Agent Loop (20 min)

**Say:**
> "This is the core of any function-calling agent. Send a message to OpenAI with tool schemas attached. If it returns tool calls, execute them, add the results to the message history, and call again. Repeat until it returns a plain text answer."

**Run the test battery slowly** and read each tool call aloud:
> "Watch the `[tool]` lines — the model decided to call `get_order_status` here because the question mentioned a specific order ID. It decided to call `search_policy` because the question was about a refund. We didn't write any if-statements for this — the tool schema descriptions did that work."

**For the out-of-domain question:**
> "Notice the router fires before the agent loop even starts. 'What is the capital of France?' never reaches OpenAI. No embeddings, no tool calls, no tokens spent."

---

### Section 8 — Add Agent Memory (20 min)

**Say:**
> "Now let's add memory. Two lines change: before we call OpenAI, we search long-term memory for relevant facts and inject them into the system prompt. After we get an answer, we store the turn in session memory."

**Run the side-by-side comparison** and read the two answers aloud. Point out the difference:
> "The memory-enriched version mentioned Alex's vegetarian preference even though she didn't mention it. That's long-term memory doing its job — personalising the response from information the agent learned in a past session."

**Run the multi-turn demo:**
> "Turn 2 asks 'what is the refund policy if it arrives cold?' without mentioning the order. The agent answers about the order it already knows about from Turn 1. That's session memory maintaining conversation context."

---

### Section 9 — LangCache (10 min)

**Say:**
> "LangCache is the same component from Workshop 1, but now it's at the very front of the pipeline — before routing, before memory, before any tool calls. If we've answered a semantically similar question before, we return the cached answer instantly. No LLM call, no tool calls, no tokens."

**Point at the latency numbers:**
> "Look at the difference. Cache miss: 3-4 seconds. Cache hit: under 100 milliseconds. That's the cost of one Redis lookup versus a full OpenAI round-trip with tool calls."

---

### Sections 10–11 — Full Pipeline and Scenarios (25 min)

**Section 10:** Read through the pipeline diagram in the markdown cell. Run the example battery with `verbose=False` to show the summary table — `CACHED`, `LIVE`, tools used, answer preview.

**Section 11 Scenario 1 — Morgan's delayed order:**
> "Watch how the agent uses two different data sources in the same conversation. Turn 1 calls Context Retriever to get the live order status and delay reason. Turn 2 calls `search_policy` to answer the compensation question. The session memory connects them."

**Section 11 Scenario 2 — Alex returning customer:**
> "This is the Workshop 2 payoff moment. Alex never mentions she's vegetarian. The agent mentions it anyway, based on long-term memory from Section 5. Then when she says she's also nut-free, the agent calls `remember_fact` to store that for next time."

**Section 11 Scenario 3 — Mixed conversation:**
> "The router holds even mid-conversation. Turn 2 is off-topic and gets refused cleanly. Turn 3 returns to a valid question and the agent answers normally — the session is intact."

---

## 4. Redis Iris Positioning Points

| Positioning Point | When to Use |
|---|---|
| "Redis is not just a cache — it's the intelligence layer" | Opening, every section |
| "One Redis Cloud database powers everything — data, vectors, routing, memory, cache" | Section 2, Section 10 |
| "Context Retriever gives agents governed access to live data — no SQL, no custom wrappers" | Section 4 |
| "Agent Memory is Redis doing vector search — but for customer facts, not documents" | Section 5 |
| "LangCache at the front of the pipeline eliminates entire classes of LLM calls" | Section 9 |
| "RDI makes the live data truly live — changes in your database appear in Redis within seconds" | Section 2, Section 13 |
| "This agent has no LangGraph, no SDK, no framework — just OpenAI function calling and Redis" | Section 7 |

**Avoid:**
- Making this an OpenAI tutorial
- Spending more than 2 minutes on LLM theory
- Suggesting attendees would need to build their own memory layer

---

## 5. Common Attendee Issues

### Agent Memory Connection Failure

**Symptom:** `❌ Agent Memory error` in Section 1.4.

| Error pattern | Cause | Fix |
|---|---|---|
| 401 / Unauthorized | Wrong API key | Re-copy from Redis Cloud console — keys are case-sensitive |
| 404 / Store not found | Wrong Store ID | Check the exact Store ID in Redis Cloud → Agent Memory → your service |
| Connection refused | Wrong URL | URL should include `https://` and end without a trailing slash |
| Service not Active | Service still provisioning | Wait 2–3 minutes and retry — new services take time to start |

---

### Context Retriever MCP URL Wrong

**Symptom:** MCP client connects but `list_tools()` returns empty or errors.

The MCP URL is shown separately from the admin URL in the Redis Cloud console. It typically looks like:
```
https://your-service-name-mcp.context-retriever.redis.io
```

The admin URL (for `ContextSurfacesClient`) is different. Make sure attendees paste the correct URL into `CTX_MCP_URL`.

---

### No Tools Listed After MCP Connect

**Symptom:** `list_tools()` returns `[]`.

The Context Retriever service was provisioned but no context surfaces have been defined yet. Attendees need to:
1. Open Redis Cloud → Context Retriever → their service
2. Define at least one context surface pointing at the `redis-eats:order:*` keys
3. Re-run Section 1.5

For a workshop, consider pre-defining the surfaces as part of the pre-workshop setup instructions.

---

### Redis Connectivity Spins

**Symptom:** Section 1.2 hangs past 5 seconds.

The pre-flight check catches empty/placeholder credentials before touching the network. If it's spinning, the credentials cell parsed a value that passed the placeholder check but is still invalid. Most common cause: the Redis CLI command contains an extra space or a port number in the hostname field.

**Fix:** Re-paste the CLI command from Redis Cloud → Connect → Redis CLI exactly as shown.

---

### Workshop 1 Policy Index Not Found / Slow Rebuild

**Symptom:** Section 3 triggers a full rebuild (takes 3–5 minutes).

This is expected if Workshop 1 was reset or the attendee is using a fresh database. The rebuild runs automatically and the attendee can continue reading ahead while it runs. Do not skip Section 3 — the `search_policy_chunks()` helper is defined there and needed in Section 6.

---

### Tool Execution Returns Errors

**Symptom:** `execute_tool()` returns `{"error": "Order 'ord-1002' not found."}`.

Section 2 (Load Live Data) was not run, or the attendee's database was reset between sessions. Re-run Section 2 to reload the operational data.

---

### Agent Memory `SearchLongTermMemoryRequestContent` Error

**Symptom:** `search_long_term_memory()` fails with a validation error.

The `SearchLongTermMemoryRequestContent` model requires `text` at minimum. Confirm the request object is constructed as:
```python
memory_models.SearchLongTermMemoryRequestContent(text="...", limit=3)
```
Not as a raw dict.

---

## 6. Expected Outputs

### Section 1.4 — Agent Memory
```
Checking Agent Memory connectivity...

  ✅ Agent Memory connected
     URL      : https://your-service.redis.io
     Store ID : your-store-id
     Status   : healthy

✅ Agent Memory ready
```

### Section 1.5 — Context Retriever
```
Checking Context Retriever connectivity...

  ✅ Context Retriever admin client connected
  ✅ MCP client connected  (3 tool(s) available)
     • get_order_status: Look up the current status of a Redis Eats order...
     • get_customer_profile: Retrieve a customer's profile...
     • get_restaurant_info: Retrieve information about a restaurant...

✅ Context Retriever ready
```

### Section 2 — Live Data
```
  ✅ customer        8 records → redis-eats:customer:*
  ✅ restaurant      8 records → redis-eats:restaurant:*
  ✅ order          10 records → redis-eats:order:*
  ✅ driver          5 records → redis-eats:driver:*

✅ 31 total records loaded into Redis Cloud
```

### Section 5.3 — Long-term Memory Search
```
Found 3 relevant memories:

  [1] Customer prefers vegetarian food and never orders meat.
  [2] Customer had a late delivery in January and was frustrated...
  [3] Customer is a Gold tier member with 47 orders since March 2022.
```

### Section 7 — Basic Agent (order lookup)
```
🤖 Redis Eats Agent
   Customer : cust-001
   Question : What is the status of order ord-1002?

   [router] → food_delivery_support
   [tool]   → get_order_status({'order_id': 'ord-1002'})
            ← {'status': 'in_transit', 'items': '["Salmon Roll x2",...', ...}

   [agent]  → final answer (after 1 tool round(s))

   Answer: Your order ord-1002 is currently in transit...
```

### Section 8 — Memory comparison
```
WITHOUT MEMORY:
Answer: ...generic refund information...

WITH MEMORY:
   [memory] → 3 relevant memorie(s) retrieved:
              • Customer prefers vegetarian food...
              • Customer had a late delivery in January...

Answer: ...personalised response referencing dietary preferences and delivery history...
```

### Section 9 — Cache hit
```
SECOND CALL — semantically similar, expect CACHE HIT:
   [cache]  → HIT  (similarity ≥ 0.9)

   Answer: ...same answer as first call...
   [cache]  → returned instantly — no LLM call made

   Latency: 0.08s  ← compare to the first call above
```

### Section 12 — Reset
```
  ✅ Deleted   8 redis-eats:customer:* keys
  ✅ Deleted  10 redis-eats:order:* keys
  ✅ Deleted   8 redis-eats:restaurant:* keys
  ✅ Deleted   5 redis-eats:driver:* keys
  ✅ Index 'redis-eats-chunks' dropped
  ✅ SemanticRouter 'redis-eats-router' deleted
  ✅ Demo session memory deleted

✅ All redis-eats:* keys removed — database is clean
🏁 Reset complete.
```

---

## 7. Workshop 1 → Workshop 2 Transition Talk Track

Use this to open the session or when attendees ask how the two workshops relate.

> "Workshop 1 built a solid foundation. You have a chatbot that retrieves policy answers, refuses off-topic questions, and caches repeated inputs. But it has a fundamental limitation: it has no idea who you are.
>
> Every time a customer starts a conversation, the Workshop 1 bot starts completely fresh. It doesn't know the customer's name. It can't see their actual orders. It doesn't remember that last week they told you they're vegetarian, or that they had a frustrating delay.
>
> Workshop 2 changes all of that. The same Redis Cloud database that held your policy chunks now also holds your customer profiles, live orders, restaurant status, and driver data. The same Redis Cloud platform that powered your semantic cache now also powers your agent's long-term memory.
>
> The Workshop 1 skills carry forward exactly — vectors, routing, LangCache. Everything you built is still there. Workshop 2 adds the context layer on top of it."

---

## 8. Delivery Guidance

### Manage the Credential Setup Carefully

Section 1 has five credential groups. Budget 15 minutes and do not rush it. If one attendee is missing a service, they can watch the instructor screen while the rest of the session runs and provision it afterward.

### Run Section 3 Early

Start Section 3 (policy index check) running as soon as Section 2 is done. If it needs to rebuild (3–5 minutes), use that time to explain the Context Retriever architecture in depth. The rebuild runs in the background.

### Instructor Fallback Setup

Before the session, prepare your own credentials for all 5 services and pre-run Sections 1–6. Have the following ready:
- A demo session seeded with Alex Rivera's long-term memories
- Confirmed tool list from `list_tools()`
- At least one successful `ask_bot()` call

If something breaks mid-session, switch to showing your pre-run output.

### The Memory Comparison Is the Highlight

Section 8.2 (without memory vs with memory) is the Workshop 2 equivalent of Workshop 1's "how many of you expected Redis to do this?" moment. Run it slowly, read both answers aloud, and ask the room to spot the difference. Let it land.

### Keep Focus on Redis

Attendees may ask about LangGraph, LlamaIndex, or other agent frameworks. Acknowledge briefly and redirect:
> "Those are great frameworks and they work well with Redis. For this workshop, we're keeping it simple to show you the Redis layer clearly. In production you'd often add LangGraph on top of exactly what we've built here."

---

*Guide version: Workshop 2 — Redis Eats Agentic*
*Prerequisite: Workshop 1 — Redis Eats RAG Chatbot*

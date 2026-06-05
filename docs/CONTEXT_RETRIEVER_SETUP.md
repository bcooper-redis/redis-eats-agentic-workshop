# Setting Up Context Retriever for Workshop 2

Context Retriever is the component that gives the agent access to live order, customer, and restaurant data. This guide walks through the two steps required:

1. **Provision the service** — one-time click in Redis Cloud (2 minutes, UI only)
2. **Create the context surface** — automated by a script (30 seconds)

That's it. The script handles everything else.

---

## Step 1 — Provision the Context Retriever Service

You only need to do this once per Redis Cloud account.

1. Log into [app.redislabs.com](https://app.redislabs.com)
2. In the left sidebar, click **Context Engine**
3. Click **Context Retriever**
4. Click **Create service**
5. Select your Redis Cloud database (the same one used for the workshop)
6. Give it a name (e.g. `redis-eats-workshop`)
7. Click **Create**

Wait about 2–3 minutes for the service to become **Active**.

Once active, find and copy these four values — you'll need them for the script and notebook:

| Value | Where to find it |
|---|---|
| **Service URL** | Context Retriever → your service → **Connection** tab |
| **Admin key** | Context Retriever → your service → **API Keys** → **Create admin key** |
| **MCP URL** | Context Retriever → your service → **Connection** tab → **MCP endpoint** |

> **Note:** The MCP URL is different from the service URL. It ends in `/mcp` or has `-mcp` in the hostname. Copy it separately.

---

## Step 2 — Run the Setup Script

The script creates the context surface (data model) and generates an agent key automatically. You do not need to configure anything in the Redis Cloud UI beyond Step 1.

**Make sure workshop data is loaded first:**
```bash
# If you haven't loaded the workshop data yet:
python3 scripts/load_live_data.py --redis-url "redis://default:password@your-host:port"
```

**Then run the setup script:**
```bash
python3 scripts/setup_context_retriever.py \
  --ctx-url   "https://your-ctx-service.redis.io" \
  --admin-key "your-admin-key" \
  --redis-url "redis://default:password@your-host:port"
```

Or using environment variables:
```bash
export CTX_SURFACES_URL="https://your-ctx-service.redis.io"
export CTX_ADMIN_KEY="your-admin-key"
export REDIS_URL="redis://default:password@your-host:port"

python3 scripts/setup_context_retriever.py
```

**Expected output:**
```
✅ Connected to Context Retriever: https://your-ctx-service.redis.io
Building data model...
✅ Data model built: 3 entities — ['Order', 'Customer', 'Restaurant']
✅ Redis connection parsed: your-host:port  tls=False
Creating context surface 'redis-eats-workshop'...
✅ Surface created
   ID     : surf-abc123
   Name   : redis-eats-workshop
   Status : active
   Tools  : [get_order, get_customer, get_restaurant]
Creating agent key 'redis-eats-workshop-agent'...
✅ Agent key created

==============================================================
  Context Retriever setup complete!

  Paste these values into Section 1.1 of the notebook:

  CTX_SURFACES_URL = "https://your-ctx-service.redis.io"
  CTX_ADMIN_KEY    = "your-admin-key"
  CTX_AGENT_KEY    = "agt_xxxxxxxxxxxx"
  CTX_MCP_URL      = "<get from Redis Cloud console — Context Retriever → MCP URL>"

  Surface ID for reference:
    surf-abc123
==============================================================
```

---

## Step 3 — Update the Notebook

Copy the four values from the script output and paste them into **Section 1.1** of the notebook:

```python
CTX_SURFACES_URL = "https://your-ctx-service.redis.io"
CTX_ADMIN_KEY    = "your-admin-key"
CTX_AGENT_KEY    = "agt_xxxxxxxxxxxx"
CTX_MCP_URL      = "https://your-ctx-service-mcp.redis.io"   # from Redis Cloud console
```

> **The MCP URL** is the one value the script can't retrieve automatically — get it from the Redis Cloud console (Context Retriever → your service → Connection tab → MCP endpoint).

---

## What the Script Creates

The script creates a **context surface** with three entities that map to the Redis Hashes loaded in Section 2 of the notebook:

| Entity | Redis key pattern | Tools generated |
|---|---|---|
| Order | `redis-eats:order:{order_id}` | `get_order` |
| Customer | `redis-eats:customer:{customer_id}` | `get_customer` |
| Restaurant | `redis-eats:restaurant:{restaurant_id}` | `get_restaurant` |

The tools are **auto-generated** from the data model — you don't define them manually. Each tool takes the entity ID as a parameter and returns all fields from the corresponding Redis Hash.

---

## Re-running After a Reset

If you run the Section 12 Reset Lab (which deletes all `redis-eats:*` keys) and then restart:

1. Re-run **Section 2** of the notebook to reload the live data
2. You do **not** need to re-run the setup script — the context surface and agent key are still valid
3. The tools will start returning data again as soon as the Redis keys exist

If you need to recreate the surface (e.g. you changed the data schema):
```bash
python3 scripts/setup_context_retriever.py \
  --ctx-url "..." --admin-key "..." --redis-url "..." \
  --overwrite
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `❌ Cannot reach Context Retriever` | Service may still be provisioning — wait 2–3 minutes and retry |
| `❌ Surface creation failed: 401` | Admin key is wrong — re-copy from Redis Cloud console |
| `list_tools()` returns `[]` in notebook | Surface was created but may not be active yet — wait 1 minute and re-run Section 1.5 |
| Tools return `{"error": "not found"}` | Workshop data not loaded — run Section 2 or `load_live_data.py` first |
| `CTX_MCP_URL` wrong | MCP URL is separate from the service URL — check Connection tab in Redis Cloud console |

---

## For Instructors: Pre-Workshop Setup Option

For a smoother workshop experience, you can run this setup on behalf of all attendees:

1. Provision one shared Context Retriever service
2. Run the setup script with your Redis Cloud credentials
3. Share only the `CTX_AGENT_KEY` and `CTX_MCP_URL` with attendees — they do not need the admin key

Attendees then paste just those two values into the notebook and skip the setup script entirely.

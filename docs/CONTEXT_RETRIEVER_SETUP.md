# Setting Up Context Retriever for Workshop 2

Context Retriever gives the agent access to live order, customer, and restaurant data.
Setup has two steps:

1. **Provision the service** — one-time click in the Redis Cloud wizard (~3 minutes)
2. **Create the context surface** — runs automatically in the Colab notebook (Section 4)

That's it. The notebook handles everything after the wizard.

---

## Step 1 — Provision the Context Retriever Service in Redis Cloud

1. Log into [app.redislabs.com](https://app.redislabs.com)
2. In the left sidebar, click **Context Engine → Context Retriever**
3. Click **Create service**
4. Select your Redis Cloud database (same one used for the workshop)
5. Give it a name (e.g. `redis-eats-workshop`)

### The Wizard Requires a Placeholder Entity

The wizard will prompt you to define at least one entity before it lets you
finish. Use these exact values — this is only a placeholder to satisfy the
wizard requirement:

| Field | Value to enter |
|---|---|
| Entity name | `Placeholder` |
| Field name | `id` |
| Field type | `String` |
| Key field | **Yes** (check the box) |

> **Why a placeholder?** The wizard needs at least one entity to create the
> service, but the real Redis Eats entities (Order, Customer, Restaurant) are
> defined as Python code in the Colab notebook. Section 4 of the notebook creates
> the correct context surface automatically — you do not need to define anything
> else in the wizard.

6. Click **Create** and wait 2–3 minutes for the service to become **Active**

### Copy These Values

Once the service is Active, find and save these three values:

| Value | Where to find it |
|---|---|
| **Service URL** (`CTX_SURFACES_URL`) | Context Retriever → your service → **Connection** tab |
| **Admin key** (`CTX_ADMIN_KEY`) | Context Retriever → your service → **API Keys** → Create admin key |
| **MCP URL** (`CTX_MCP_URL`) | Context Retriever → your service → Connection tab → **MCP endpoint** |

> **Important:** The MCP URL is different from the Service URL. It ends in `/mcp`
> or has a different hostname. Copy it separately — they are both on the Connection tab.

> **Agent key:** You do not need to create an agent key manually. The notebook
> creates one in Section 4 using your admin key.

---

## Step 2 — Paste Values into the Notebook

In **Section 1.1** of the Colab notebook, paste the three values:

```python
CTX_SURFACES_URL = "https://your-context-surfaces-host.redis.io"
CTX_ADMIN_KEY    = "your-admin-key"
CTX_MCP_URL      = "https://your-mcp-host.redis.io"
```

Leave `CTX_AGENT_KEY = None` as-is. It gets set automatically.

---

## Step 3 — Run Section 4.0 in the Notebook

Section 4.0 of the notebook does the following automatically:

1. Defines three entity models as Python classes (`Order`, `Customer`, `Restaurant`)
2. Creates a context surface named `redis-eats-workshop` with those entities
3. Generates an agent key scoped to the surface
4. Connects the MCP client

**Expected output from Section 4.0:**
```
Building data model...
✅ Data model built: 3 entities — ['Order', 'Customer', 'Restaurant']
✅ Redis connection: your-host:port  tls=True
Creating context surface 'redis-eats-workshop'...
✅ Surface created — ID: surf-xxxxxxxxxxxx
   Tools generated: ['get_order', 'get_customer', 'get_restaurant']
Creating agent key...
✅ Agent key created
Connecting MCP client...
✅ MCP client connected — ready for tool calls
✅ Context Retriever setup complete — proceed to Section 4.1 to see your tools.
```

After this you will see three tools in Section 4.1:

| Tool | What it retrieves |
|---|---|
| `get_order` | Order status, items, delivery ETA, delay reason |
| `get_customer` | Customer profile, loyalty tier, dietary preferences |
| `get_restaurant` | Restaurant name, status, hours, menu highlights |

---

## Re-running After a Reset

If you run the Section 12 Reset and restart:

1. Re-run **Section 2** to reload the live data into Redis
2. Re-run **Section 4.0** — it detects the surface already exists and just creates a new agent key
3. Continue from Section 4.1

The `ℹ️  Surface already exists` message is expected on the second run.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `❌ Context Retriever unreachable` (Section 1.5) | Service still provisioning — wait 2–3 min and re-run |
| `❌ Surface creation failed: 401` | Admin key is wrong — re-copy from Redis Cloud console |
| `❌ MCP client connection failed` | `CTX_MCP_URL` is wrong — it must be the MCP endpoint (Connection tab), not the admin URL |
| Section 4.1 `list_tools()` returns 0 tools | Surface may still be initialising — wait 30 seconds and re-run Section 4.1 |
| Tools return `{"error": "not found"}` | Live data not loaded — re-run Section 2 first |
| `ℹ️  Surface already exists` in Section 4.0 | Normal on re-run — the existing surface is reused |

---

## For Instructors: Shared Service Option

For large workshops you can provision one shared Context Retriever service
and give all attendees the same three values (`CTX_SURFACES_URL`, `CTX_ADMIN_KEY`,
`CTX_MCP_URL`). Each attendee runs Section 4.0, which creates a new agent key for
their session. The surface is created once by the first attendee (or the instructor)
and subsequent runs hit the `ℹ️  Surface already exists` path.

The `setup_context_retriever.py` script in the `scripts/` folder provides the
same functionality from the command line if you prefer to pre-provision:

```bash
python3 scripts/setup_context_retriever.py \
  --ctx-url   "https://your-service.redis.io" \
  --admin-key "your-admin-key" \
  --redis-url "redis://default:password@host:port"
```

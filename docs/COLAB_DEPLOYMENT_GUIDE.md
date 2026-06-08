# Deploying Workshop 2 to Google Colab

**Who this guide is for:** Someone deploying the agentic workshop to Colab for the first time.

**What you end up with:** A single Colab link attendees click to open the notebook — no local setup required on their end.

**Time to complete:** About 15 minutes (faster than Workshop 1 since you already have a GitHub account and Personal Access Token set up).

---

## Prerequisites

- GitHub account with Workshop 1 already pushed (`redis-eats-rag-workshop`)
- Your Personal Access Token from Workshop 1 (still works here)
- Workshop 2 repo already initialised locally at:
  `/Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-agentic-workshop`

---

## Step 1 — Create a GitHub Repository

1. Go to [github.com](https://github.com) and sign in
2. Click **+** → **New repository**
3. Fill in:

   | Field | Value |
   |---|---|
   | Repository name | `redis-eats-agentic-workshop` |
   | Visibility | **Public** ← required for Colab |
   | Initialize | **Leave all checkboxes unchecked** |

4. Click **Create repository** and copy the URL:
   ```
   https://github.com/YOUR-USERNAME/redis-eats-agentic-workshop.git
   ```

---

## Step 2 — Update the Notebook URL

```bash
cd /Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-agentic-workshop
python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-agentic-workshop
```

Output confirms what was replaced and prints your Colab link.

---

## Step 3 — Push to GitHub

```bash
cd /Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-agentic-workshop

git add .
git commit -m "Update repo URL for deployment"
git remote add origin https://github.com/YOUR-USERNAME/redis-eats-agentic-workshop.git
git branch -M main
git push -u origin main
```

When prompted for a password, paste your Personal Access Token (same one used for Workshop 1).

---

## Step 4 — Your Colab Link

```
https://colab.research.google.com/github/YOUR-USERNAME/redis-eats-agentic-workshop/blob/main/notebooks/redis_eats_agentic_workshop.ipynb
```

Open this in an Incognito window to test it as an attendee would.

---

## Step 5 — Test the Full Setup Flow

1. Open the Colab link in an Incognito window
2. Click **Connect** in the top-right
3. Run **cell 1** (Colab Setup) — should clone the repo and print `✅ Working directory: /content/redis-eats-agentic-workshop`
4. Run **cell 3** (pip install) → **restart runtime when prompted**
5. After restart, re-run cell 3 — should show `✅ All packages ready`
6. Run **cell 4** (imports) — should print `✅ Imports complete`
7. Enter all credentials in **cell 6** (Section 1.1) and run it
8. Run **cell 8** (Section 1.2) — verify `✅ All Redis checks passed`
9. Run **cell 10** (Section 1.3) — verify `✅ All OpenAI checks passed`
10. Run **cell 12** (Section 1.4) — verify `✅ Agent Memory ready`
11. Run **cell 14** (Section 1.5) — verify `✅ Context Retriever ready`
12. Stop here — setup confirmed working

---

## What Attendees Need Before the Session

Unlike Workshop 1, Workshop 2 requires **five services**. Each attendee provisions their own Context Retriever service using the Redis Cloud wizard — the notebook creates the context surface automatically.

| Service | Where to provision | What attendees need |
|---|---|---|
| Redis Cloud database | [redis.io/try-free](https://redis.io/try-free) | CLI command from Connect → Redis CLI |
| OpenAI API key | [platform.openai.com](https://platform.openai.com) | `sk-...` key |
| Agent Memory | Redis Cloud → Context Engine → Agent Memory | URL, Store ID, API key |
| Context Retriever | Redis Cloud → Context Engine → Context Retriever (see below) | Service URL, Admin key, MCP URL |
| LangCache | Redis Cloud → Context Engine → LangCache | URL, Cache ID, API key (same as W1) |

### Context Retriever: Wizard Setup (No Script Required)

Attendees provision their own Context Retriever service using the Redis Cloud wizard.
The Colab notebook (Section 4.0) creates the context surface and agent key automatically.

**Attendee steps (5 minutes, before the session):**

1. Redis Cloud → Context Engine → Context Retriever → **Create service**
2. Select their Redis Cloud database and give it a name
3. The wizard asks for an entity — use this placeholder to get through it:
   - Entity name: `Placeholder` | Field: `id` | Type: `String` | Mark as key: **Yes**
4. Click **Create** and wait for **Active** status
5. From the **Connection** tab, copy:
   - **Service URL** → `CTX_SURFACES_URL`
   - **MCP endpoint** → `CTX_MCP_URL`
6. From **API Keys**, create an admin key → `CTX_ADMIN_KEY`
7. Paste all three into Section 1.1 of the notebook — leave `CTX_AGENT_KEY = None`

**The notebook does the rest in Section 4.0:**
- Defines the real Redis Eats entities (Order, Customer, Restaurant)
- Creates the `redis-eats-workshop` context surface
- Generates an agent key automatically
- Connects the MCP client

> See [`docs/CONTEXT_RETRIEVER_SETUP.md`](CONTEXT_RETRIEVER_SETUP.md) for the full wizard walkthrough with screenshots and troubleshooting.

> **Tip:** Send attendees a setup checklist email 2 days before the workshop. Agent Memory and Context Retriever provisioning each take 5–10 minutes. Attendees only need to provision the service — the notebook handles surface creation during the workshop.

---

## Sharing With Attendees

Send two links:

```
Colab notebook:
https://colab.research.google.com/github/YOUR-USERNAME/redis-eats-agentic-workshop/blob/main/notebooks/redis_eats_agentic_workshop.ipynb

GitHub repo (for reference):
https://github.com/YOUR-USERNAME/redis-eats-agentic-workshop
```

---

## Pre-Workshop Checklist

**Instructor pre-work (complete before the session):**
- [ ] Your own Redis Cloud database is provisioned and Active
- [ ] Your own Context Retriever service is provisioned and Active in Redis Cloud
- [ ] Service URL, Admin key, and MCP URL copied from the Redis Cloud console
- [ ] All five services tested end-to-end using your own credentials in the notebook

**Attendee pre-work (send in the invite email):**
- [ ] Redis Cloud database provisioned (free tier is fine)
- [ ] OpenAI API key from [platform.openai.com](https://platform.openai.com)
- [ ] Agent Memory service provisioned and Active in Redis Cloud
- [ ] Context Retriever service provisioned and Active in Redis Cloud (wizard placeholder entity)
   - Service URL, Admin key, and MCP URL copied from the console
- [ ] LangCache credentials ready (same as Workshop 1, or new instance)

**Colab verification (test in an Incognito window):**
- [ ] GitHub repo is public and all files visible
- [ ] Colab link opens without errors
- [ ] Cell 1 (Colab Setup) clones repo and prints working directory
- [ ] Cell 3 (pip install) completes and prompts for restart
- [ ] After restart, Cell 3 shows `✅ All packages ready`
- [ ] Section 1.1 credentials cell accepts all values without errors
- [ ] Section 1.2 (Redis check) shows all 4 sub-checks green
- [ ] Section 1.3 (OpenAI check) shows all 3 sub-checks green
- [ ] Section 1.4 (Agent Memory) shows `✅ Agent Memory ready`
- [ ] Section 1.5 (Context Retriever) shows `✅ Context Retriever service reachable`
- [ ] Section 4.0 creates surface, generates agent key, connects MCP client
- [ ] Section 4.1 lists 3 tools: `get_order`, `get_customer`, `get_restaurant`
- [ ] Colab link is in your slide deck and invite email

---

## Pushing Updates Mid-Workshop

Same pattern as Workshop 1 — push to GitHub and changes are live immediately:

```bash
cd /Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-agentic-workshop
git add notebooks/redis_eats_agentic_workshop.ipynb
git commit -m "Fix description of issue"
git push
```

Attendees reopen the Colab link to get the updated notebook.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `❌ git clone failed` — `not found` | Run `update_repo_url.py` with your username, then `git push` |
| `❌ git clone failed` — `403` | Repo is private — make it public in GitHub Settings |
| `❌ Agent Memory error` | Verify the Agent Memory service is **Active** in Redis Cloud, check URL/Store ID/API key |
| `❌ Context Retriever error` | Verify the service is Active, confirm MCP URL is correct (it's separate from the admin URL) |
| pip install spins | Session may have timed out — reconnect Colab runtime and re-run from cell 1 |
| `❌ Redis Search module NOT found` | Database plan doesn't include Search — upgrade in Redis Cloud console |

---

## Quick Reference

| Thing | Value |
|---|---|
| Colab link | `https://colab.research.google.com/github/YOUR-USERNAME/redis-eats-agentic-workshop/blob/main/notebooks/redis_eats_agentic_workshop.ipynb` |
| Update username | `python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-agentic-workshop` |
| Push changes | `git add . && git commit -m "message" && git push` |
| Rebuild notebook | `python3 scripts/build_notebook.py && python3 scripts/build_notebook_phase4.py && python3 scripts/build_notebook_phase5.py` |

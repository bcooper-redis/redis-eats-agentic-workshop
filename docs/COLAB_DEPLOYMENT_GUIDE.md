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

Unlike Workshop 1, Workshop 2 requires **five services** to be pre-provisioned:

| Service | Where to provision | What to save |
|---|---|---|
| Redis Cloud database | [redis.io/try-free](https://redis.io/try-free) | CLI command from Connect → Redis CLI |
| OpenAI API key | [platform.openai.com](https://platform.openai.com) | `sk-...` key |
| Agent Memory | Redis Cloud → Context Engine → Agent Memory | URL, Store ID, API key |
| Context Retriever | Redis Cloud → Context Engine → Context Retriever | URL, Admin key, Agent key, MCP URL |
| LangCache | Redis Cloud → Context Engine → LangCache | URL, Cache ID, API key (same as W1) |

> **Tip:** Send attendees a setup checklist email 2 days before the workshop so they arrive with all five services provisioned. Agent Memory and Context Retriever provisioning takes 5–10 minutes in the Redis Cloud console.

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

- [ ] GitHub repo is public and all files visible
- [ ] Colab link opens without errors
- [ ] Cell 1 (Colab Setup) clones repo and prints working directory
- [ ] Cell 3 (pip install) completes and prompts for restart
- [ ] After restart, Cell 3 shows `✅ All packages ready`
- [ ] Cell 8 (Redis check) shows all 4 sub-checks green
- [ ] Cell 10 (OpenAI check) shows all 3 sub-checks green
- [ ] Cell 12 (Agent Memory) shows `✅ Agent Memory ready`
- [ ] Cell 14 (Context Retriever) shows tools listed
- [ ] Your instructor credentials for all 5 services are ready and tested
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

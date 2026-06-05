"""
generate_architecture_diagram.py

Creates the Redis Eats Agentic Workshop architecture diagram PNG.

The diagram shows the full agent request pipeline:
  Customer question
    → LangCache (cache hit → return instantly)
    → SemanticRouter (out-of-domain → refusal)
    → Agent Memory enrichment (inject long-term context)
    → OpenAI Function-Calling Loop
        ├── get_order_status()       → Context Retriever → Redis
        ├── get_customer_profile()   → Context Retriever → Redis
        ├── get_restaurant_info()    → Context Retriever → Redis
        └── search_policy()          → RedisVL RAG → Redis
    → Grounded response + citations
    → Agent Memory session store
    → LangCache store

Usage:
    python3 scripts/generate_architecture_diagram.py
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "architecture" / "redis-eats-agentic-workshop-architecture.png"

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
REDIS_RED    = "#DC1C1C"
REDIS_DARK   = "#1A1A2E"
REDISVL_BLUE = "#1565C0"
OPENAI_GREEN = "#10A37F"
CACHE_PURPLE = "#6A0DAD"
MEMORY_TEAL  = "#00695C"
CTX_ORANGE   = "#E65100"
RAG_INDIGO   = "#283593"
REFUSAL_RED  = "#B71C1C"
WHITE        = "#FFFFFF"
LIGHT_GREY   = "#F5F5F5"
ARROW_GREY   = "#555555"


def box(ax, x, y, w, h, label, sublabel=None,
        facecolor=LIGHT_GREY, edgecolor=REDIS_RED,
        fontsize=8.5, bold=False, text_color=REDIS_DARK):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                           facecolor=facecolor, edgecolor=edgecolor,
                           linewidth=1.5, zorder=3)
    ax.add_patch(patch)
    cy = y + h / 2 + (0.06 if sublabel else 0)
    ax.text(x + w / 2, cy, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold" if bold else "normal",
            color=text_color, zorder=4)
    if sublabel:
        ax.text(x + w / 2, y + h / 2 - 0.11, sublabel,
                ha="center", va="center", fontsize=6.5,
                color="#777777", style="italic", zorder=4)


def arrow(ax, x1, y1, x2, y2, color=ARROW_GREY, label=None,
          label_color=None, lw=1.4):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, mutation_scale=12), zorder=5)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.05, my, label, fontsize=6, color=label_color or color,
                ha="left", va="center", zorder=6)


def main():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    # -----------------------------------------------------------------------
    # Title
    # -----------------------------------------------------------------------
    ax.text(7, 8.7, "Redis Eats Agentic Workshop — Architecture",
            ha="center", fontsize=13, fontweight="bold", color=REDIS_DARK)
    ax.text(7, 8.4, "Don't Talk With Food In Your Mouth  |  Workshop 2: Context-Aware Agent",
            ha="center", fontsize=8, color="#666666", style="italic")

    BH = 0.55   # standard box height
    BW = 2.4    # standard box width

    # -----------------------------------------------------------------------
    # Row 1 — Customer input (top centre)
    # -----------------------------------------------------------------------
    R1 = 7.6
    box(ax, 5.8, R1 - BH/2, BW, BH, "Customer Question",
        facecolor=REDIS_DARK, edgecolor=REDIS_DARK, text_color=WHITE, bold=True)

    # -----------------------------------------------------------------------
    # Row 2 — LangCache  |  SemanticRouter
    # -----------------------------------------------------------------------
    R2 = 6.5
    box(ax, 1.0, R2 - BH/2, BW, BH, "Redis LangCache",
        sublabel="Cache hit → instant return",
        facecolor=CACHE_PURPLE, edgecolor=CACHE_PURPLE, text_color=WHITE)
    box(ax, 5.8, R2 - BH/2, BW, BH, "RedisVL SemanticRouter",
        sublabel="Out-of-domain → refused",
        facecolor=REDISVL_BLUE, edgecolor=REDISVL_BLUE, text_color=WHITE, bold=True)

    # -----------------------------------------------------------------------
    # Row 3 — Agent Memory enrichment
    # -----------------------------------------------------------------------
    R3 = 5.3
    box(ax, 5.8, R3 - BH/2, BW, BH, "Agent Memory — Enrich",
        sublabel="Inject long-term context into prompt",
        facecolor=MEMORY_TEAL, edgecolor=MEMORY_TEAL, text_color=WHITE, bold=True)

    # -----------------------------------------------------------------------
    # Row 4 — OpenAI function-calling loop
    # -----------------------------------------------------------------------
    R4 = 4.1
    box(ax, 5.8, R4 - BH/2, BW, BH, "OpenAI Function-Calling Loop",
        sublabel="ReAct: call tools until answer is ready",
        facecolor=OPENAI_GREEN, edgecolor=OPENAI_GREEN, text_color=WHITE, bold=True)

    # -----------------------------------------------------------------------
    # Row 5 — Tools (spread across)
    # -----------------------------------------------------------------------
    R5 = 2.8
    TW = 2.2   # tool box width
    tools = [
        (0.5,  "get_order_status()",     "Context Retriever → Redis",   CTX_ORANGE),
        (3.0,  "get_customer_profile()", "Context Retriever → Redis",   CTX_ORANGE),
        (5.5,  "get_restaurant_info()",  "Context Retriever → Redis",   CTX_ORANGE),
        (8.0,  "search_policy()",        "RedisVL RAG → W1 Index",      RAG_INDIGO),
        (10.5, "remember_fact()",        "Agent Memory write",           MEMORY_TEAL),
    ]
    for tx, tlabel, tsub, tcolor in tools:
        box(ax, tx, R5 - BH/2, TW, BH, tlabel, sublabel=tsub,
            facecolor=tcolor, edgecolor=tcolor, text_color=WHITE, fontsize=7.5)

    # -----------------------------------------------------------------------
    # Row 6 — Redis Cloud (single shared store)
    # -----------------------------------------------------------------------
    R6 = 1.5
    box(ax, 3.5, R6 - BH/2, 7.0, BH, "Redis Cloud",
        sublabel="Orders · Customers · Restaurants · Policy Index · Memory · Router · Cache",
        facecolor=REDIS_RED, edgecolor=REDIS_RED, text_color=WHITE, bold=True, fontsize=9)

    # -----------------------------------------------------------------------
    # Response path (right side) — back up to customer
    # -----------------------------------------------------------------------
    R7 = 7.6
    box(ax, 10.5, R7 - BH/2, 2.4, BH, "Grounded Response",
        sublabel="+ citations + memory stored",
        facecolor=REDIS_DARK, edgecolor=REDIS_DARK, text_color=WHITE, bold=True)

    # Cache miss label
    box(ax, 1.0, R3 - BH/2, BW, BH, "Agent Memory — Store",
        sublabel="Persist session + promote long-term",
        facecolor=MEMORY_TEAL, edgecolor=MEMORY_TEAL, text_color=WHITE)

    # -----------------------------------------------------------------------
    # Arrows — main flow down
    # -----------------------------------------------------------------------
    cx = 7.0   # centre of main column

    # Customer → LangCache branch + Router branch
    arrow(ax, cx, R1 - BH/2, 2.2, R2 + BH/2, color=CACHE_PURPLE,
          label="check cache", label_color=CACHE_PURPLE)
    arrow(ax, cx, R1 - BH/2, cx, R2 + BH/2, color=REDISVL_BLUE)

    # Cache hit return (left bypass)
    ax.annotate("", xy=(1.0, R7 - BH/2 + BH/2), xytext=(2.2, R2 + BH/2),
                arrowprops=dict(arrowstyle="-|>", color=CACHE_PURPLE,
                                lw=1.4, connectionstyle="arc3,rad=0.4"), zorder=5)
    ax.text(0.5, (R2 + R7) / 2 + 0.2, "cache\nhit →",
            ha="center", fontsize=6.5, color=CACHE_PURPLE, fontweight="bold")

    # Router → Memory enrichment
    arrow(ax, cx, R2 - BH/2, cx, R3 + BH/2, color=REDISVL_BLUE,
          label="in-domain", label_color=REDISVL_BLUE)

    # Memory → LLM loop
    arrow(ax, cx, R3 - BH/2, cx, R4 + BH/2, color=MEMORY_TEAL,
          label="enriched prompt", label_color=MEMORY_TEAL)

    # LLM loop → tools (fan out)
    tool_centres = [0.5 + TW/2, 3.0 + TW/2, 5.5 + TW/2, 8.0 + TW/2, 10.5 + TW/2]
    for tc in tool_centres:
        arrow(ax, cx, R4 - BH/2, tc, R5 + BH/2, color=OPENAI_GREEN)

    # Tools → Redis Cloud
    redis_cx = 7.0
    for tc in tool_centres:
        arrow(ax, tc, R5 - BH/2, redis_cx, R6 + BH/2, color=REDIS_RED)

    # LLM → Response
    arrow(ax, 8.0 + TW/2, R4, 11.7, R7 - BH/2,
          color=OPENAI_GREEN, label="final answer", label_color=OPENAI_GREEN)

    # Response → Memory store (right column)
    arrow(ax, 2.2, R2, 2.2, R3 + BH/2, color=MEMORY_TEAL,
          label="store session", label_color=MEMORY_TEAL)

    # LangCache store (from response back to cache)
    ax.annotate("", xy=(3.4, R2), xytext=(10.5 + 1.2, R7 - BH/2),
                arrowprops=dict(arrowstyle="-|>", color=CACHE_PURPLE,
                                lw=1.2, connectionstyle="arc3,rad=-0.3"), zorder=5)
    ax.text(13.0, 5.0, "cache\nstore", ha="center", fontsize=6.5,
            color=CACHE_PURPLE, fontweight="bold")

    # -----------------------------------------------------------------------
    # Legend
    # -----------------------------------------------------------------------
    legend_items = [
        mpatches.Patch(facecolor=REDIS_RED,    label="Redis Cloud"),
        mpatches.Patch(facecolor=REDISVL_BLUE, label="RedisVL / SemanticRouter"),
        mpatches.Patch(facecolor=MEMORY_TEAL,  label="Agent Memory"),
        mpatches.Patch(facecolor=CTX_ORANGE,   label="Context Retriever"),
        mpatches.Patch(facecolor=RAG_INDIGO,   label="RAG (Workshop 1)"),
        mpatches.Patch(facecolor=CACHE_PURPLE, label="LangCache"),
        mpatches.Patch(facecolor=OPENAI_GREEN, label="OpenAI"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=7,
              framealpha=0.9, bbox_to_anchor=(0.0, 0.0))

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(pad=0.3)
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"✅ Diagram saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

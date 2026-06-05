"""
update_repo_url.py

Updates the GitHub username in the notebook and README.
Run before first git push.

Usage:
    python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-agentic-workshop
"""

import re, sys, json
from pathlib import Path

REPO_ROOT  = Path(__file__).parent.parent
NOTEBOOK   = REPO_ROOT / "notebooks" / "redis_eats_agentic_workshop.ipynb"
README     = REPO_ROOT / "README.md"
REPO_NAME  = "redis-eats-agentic-workshop"
PATTERN    = re.compile(rf'(github\.com/)([^/"\'`\\\s\)]+)(/{re.escape(REPO_NAME)})', re.IGNORECASE)


def replace_username(text, new_username):
    count = [0]
    def r(m):
        count[0] += 1
        return f"{m.group(1)}{new_username}{m.group(3)}"
    return PATTERN.sub(r, text), count[0]


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/{REPO_NAME}")
        sys.exit(1)

    new_url      = sys.argv[1].rstrip("/")
    new_username = new_url.split("/")[3]

    for path in [NOTEBOOK, README]:
        if not path.exists():
            print(f"⚠️  {path.name} not found — skipping")
            continue
        text, n = replace_username(path.read_text(encoding="utf-8"), new_username)
        path.write_text(text, encoding="utf-8")
        print(f"✅ {path.name:40s} {n} replacement(s) → '{new_username}'")

    colab = (f"https://colab.research.google.com/github/{new_username}/"
             f"{REPO_NAME}/blob/main/notebooks/redis_eats_agentic_workshop.ipynb")
    print(f"\nColab link:\n  {colab}")
    print(f"\nNext: git add . && git commit -m 'Set GitHub username' && git push")


if __name__ == "__main__":
    main()

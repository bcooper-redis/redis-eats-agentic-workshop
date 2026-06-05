"""
load_live_data.py

Loads the Redis Eats synthetic operational data into Redis Cloud.

This script simulates what Redis Data Integration (RDI) would do automatically
in production: reading rows from a relational database and writing them into
Redis as Hashes using a consistent key naming convention.

In production:
  PostgreSQL/MySQL → RDI (CDC) → Redis Cloud (near real-time sync)

In this workshop:
  JSON files → this script → Redis Cloud (one-time load)

Key naming convention (Redis Agent Skill: data-key-naming):
  redis-eats:customer:<customer_id>
  redis-eats:order:<order_id>
  redis-eats:restaurant:<restaurant_id>
  redis-eats:driver:<driver_id>

Usage:
    python3 scripts/load_live_data.py \\
        --redis-url "redis://default:password@host:port"

Or set REDIS_URL environment variable and run:
    python3 scripts/load_live_data.py
"""

import json
import os
import sys
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent
REPO_ROOT    = SCRIPT_DIR.parent
DATA_DIR     = REPO_ROOT / "data" / "source_json"

# ---------------------------------------------------------------------------
# Key prefix — all workshop data lives under redis-eats:
# ---------------------------------------------------------------------------
KEY_PREFIX = "redis-eats"


def load_entity(r, entity_type: str, records: list, id_field: str) -> int:
    """
    Write a list of entity records into Redis as Hashes.

    Each record is flattened to string values (Redis Hashes store strings).
    None values are stored as the empty string so HGETALL always returns
    a complete set of fields.

    Key pattern:  redis-eats:<entity_type>:<id>

    Args:
        r:           redis-py client (decode_responses=True)
        entity_type: e.g. "customer", "order", "restaurant", "driver"
        records:     list of dicts loaded from JSON
        id_field:    the field name used as the unique ID

    Returns:
        Number of records written.
    """
    pipe = r.pipeline(transaction=False)

    for record in records:
        key = f"{KEY_PREFIX}:{entity_type}:{record[id_field]}"
        # Flatten all values to strings for Redis Hash storage
        flat = {
            k: json.dumps(v) if isinstance(v, (list, dict)) else
               ("" if v is None else str(v))
            for k, v in record.items()
        }
        pipe.hset(key, mapping=flat)

    pipe.execute()
    return len(records)


def main():
    """Load all Redis Eats operational data into Redis Cloud."""
    parser = argparse.ArgumentParser(description="Load Redis Eats live data into Redis")
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", ""),
        help="Redis connection URL (or set REDIS_URL env var)"
    )
    args = parser.parse_args()

    if not args.redis_url:
        print("ERROR: Provide --redis-url or set REDIS_URL environment variable")
        sys.exit(1)

    # --- Connect to Redis ---
    try:
        import redis as redis_lib
        # Use ssl=True only for rediss:// URLs
        use_ssl = args.redis_url.startswith("rediss://")
        r = redis_lib.from_url(args.redis_url, decode_responses=True, ssl=use_ssl)
        r.ping()
        print(f"✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        sys.exit(1)

    # --- Load each entity type ---
    entities = [
        ("customer",   "customers.json",   "customer_id"),
        ("restaurant", "restaurants.json", "restaurant_id"),
        ("order",      "orders.json",      "order_id"),
        ("driver",     "drivers.json",     "driver_id"),
    ]

    total = 0
    print(f"\nLoading Redis Eats operational data → {KEY_PREFIX}:*\n")

    for entity_type, filename, id_field in entities:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"  ⚠️  {filename} not found — skipping")
            continue

        with open(filepath) as f:
            records = json.load(f)

        count = load_entity(r, entity_type, records, id_field)
        print(f"  ✅ {entity_type:12s} {count:3d} records  "
              f"(keys: {KEY_PREFIX}:{entity_type}:*)")
        total += count

    # --- Verify ---
    print(f"\nTotal records loaded: {total}")
    all_keys = list(r.scan_iter(f"{KEY_PREFIX}:*", count=500))
    # Filter to just the live data keys (not the W1 chunk/router keys)
    live_keys = [k for k in all_keys if not k.startswith(f"{KEY_PREFIX}:chunk:")]
    print(f"Live data keys in Redis: {len(live_keys)}")
    print(f"\n✅ Done. Run the notebook from Section 2 to verify the data.")


if __name__ == "__main__":
    main()

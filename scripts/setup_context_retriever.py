"""
setup_context_retriever.py

Automates the full Context Retriever setup for the Redis Eats Agentic Workshop.

This script creates:
  1. A Context Surface named 'redis-eats-workshop' with three entities:
       Order, Customer, Restaurant
  2. An Agent API key scoped to that surface

After running this script, paste the printed values into Section 1.1 of the
workshop notebook:
  CTX_AGENT_KEY  → the agent key printed at the end
  CTX_MCP_URL    → your Context Retriever service MCP URL (from Redis Cloud console)

Prerequisites:
  - Context Retriever service provisioned in Redis Cloud
  - Admin key from Redis Cloud → Context Engine → Context Retriever → your service
  - Redis Cloud database running with workshop data already loaded
    (run scripts/load_live_data.py first, or run Section 2 of the notebook)

Usage:
    python3 scripts/setup_context_retriever.py \\
        --ctx-url   "https://your-ctx-service.redis.io" \\
        --admin-key "your-admin-key" \\
        --redis-url "redis://default:password@host:port"

Or set environment variables and run without flags:
    export CTX_SURFACES_URL=https://...
    export CTX_ADMIN_KEY=...
    export REDIS_URL=redis://...
    python3 scripts/setup_context_retriever.py
"""

import argparse, json, os, sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Entity model definitions
#
# These map exactly to the Redis Hashes loaded by load_live_data.py.
# __redis_key_template__ must match the key pattern used when loading data.
# ---------------------------------------------------------------------------
def build_data_model():
    """
    Build and export the Context Retriever data model for all three entities.

    Returns a dict matching the OpenAPI schema expected by CreateContextSurfaceRequest.
    Tools are auto-generated from this model by the Context Retriever service —
    one tool per entity (e.g. get_order, get_customer, get_restaurant).
    """
    from context_surfaces import ContextModel, ContextField, export_data_model

    class Order(ContextModel):
        __redis_key_template__ = "redis-eats:order:{order_id}"
        order_id:    str = ContextField(
            description="The unique order ID (e.g. ord-1002)", is_key_component=True
        )
        status:      str = ContextField(
            description="Current status: pending, preparing, in_transit, delivered, delayed, cancelled",
            index="tag"
        )
        customer_id: str = ContextField(
            description="Customer ID who placed the order", index="tag"
        )
        restaurant_id: str = ContextField(
            description="Restaurant ID", index="tag"
        )
        driver_id:   str = ContextField(
            description="Driver ID assigned to this order", index="tag"
        )
        items:       str = ContextField(
            description="Ordered items as a JSON string"
        )
        total:       str = ContextField(
            description="Order total including delivery fee and tip"
        )
        placed_at:   str = ContextField(
            description="Timestamp when the order was placed"
        )
        estimated_delivery_mins: str = ContextField(
            description="Estimated delivery time in minutes"
        )
        special_instructions: str = ContextField(
            description="Special delivery instructions from the customer"
        )
        delay_reason: str = ContextField(
            description="Reason for delay if status is delayed", default=None
        )

    class Customer(ContextModel):
        __redis_key_template__ = "redis-eats:customer:{customer_id}"
        customer_id:  str = ContextField(
            description="The unique customer ID (e.g. cust-001)", is_key_component=True
        )
        name:         str = ContextField(
            description="Customer full name", index="text"
        )
        loyalty_tier: str = ContextField(
            description="Loyalty tier: Bronze, Silver, Gold, Platinum", index="tag"
        )
        dietary_preferences: str = ContextField(
            description="Dietary restrictions as a JSON list (e.g. vegetarian, gluten-free)"
        )
        favorite_cuisines: str = ContextField(
            description="Favourite cuisine types as a JSON list"
        )
        total_orders: str = ContextField(
            description="Total number of orders placed"
        )
        notes:        str = ContextField(
            description="Internal notes about customer preferences and service history"
        )

    class Restaurant(ContextModel):
        __redis_key_template__ = "redis-eats:restaurant:{restaurant_id}"
        restaurant_id: str = ContextField(
            description="The unique restaurant ID (e.g. rest-001)", is_key_component=True
        )
        name:          str = ContextField(
            description="Restaurant name", index="text"
        )
        cuisine:       str = ContextField(
            description="Cuisine type (e.g. Mexican, Japanese, Indian)", index="tag"
        )
        status:        str = ContextField(
            description="Current status: open, paused, closed", index="tag"
        )
        hours:         str = ContextField(
            description="Operating hours (e.g. Mon-Sun 10:00-22:00)"
        )
        delivery_time_mins: str = ContextField(
            description="Estimated delivery time in minutes"
        )
        menu_highlights: str = ContextField(
            description="Popular menu items as a JSON list"
        )
        dietary_options: str = ContextField(
            description="Available dietary options as a JSON list"
        )
        rating:        str = ContextField(
            description="Average customer rating out of 5.0"
        )

    return export_data_model(
        title="Redis Eats Operational Data",
        description=(
            "Live customer, order, and restaurant data for the Redis Eats "
            "agentic support bot. Tools are auto-generated from this model."
        ),
        entities=[Order, Customer, Restaurant],
    )


# ---------------------------------------------------------------------------
# Main setup
# ---------------------------------------------------------------------------

SURFACE_NAME = "redis-eats-workshop"
AGENT_KEY_NAME = "redis-eats-workshop-agent"


def parse_redis_url(redis_url: str) -> dict:
    """
    Parse a Redis URL into the fields needed by DataSourceConnectionConfig.

    Accepts: redis://user:pass@host:port  or  rediss://user:pass@host:port
    Returns dict with addr, username, password, tls_enabled.
    """
    from urllib.parse import urlparse
    url = redis_url.strip()
    tls = url.startswith("rediss://")
    if tls:
        url = "redis://" + url[len("rediss://"):]
    p = urlparse(url)
    return {
        "addr":        f"{p.hostname}:{p.port or 6379}",
        "username":    p.username or "",
        "password":    p.password or "",
        "tls_enabled": tls,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Set up Context Retriever for the Redis Eats Agentic Workshop"
    )
    parser.add_argument(
        "--ctx-url",
        default=os.getenv("CTX_SURFACES_URL", ""),
        help="Context Retriever service URL"
    )
    parser.add_argument(
        "--admin-key",
        default=os.getenv("CTX_ADMIN_KEY", ""),
        help="Context Retriever admin key"
    )
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", ""),
        help="Redis connection URL (redis:// or rediss://)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and recreate the surface if it already exists"
    )
    args = parser.parse_args()

    if not args.ctx_url or not args.admin_key or not args.redis_url:
        print("ERROR: --ctx-url, --admin-key, and --redis-url are all required.")
        print("       Or set CTX_SURFACES_URL, CTX_ADMIN_KEY, REDIS_URL env vars.")
        sys.exit(1)

    from context_surfaces import ContextSurfacesClient, CreateContextSurfaceRequest
    from context_surfaces.models import (
        DataSourceRequest, DataSourceConnectionConfig, CreateAgentKeyRequest
    )

    client = ContextSurfacesClient(base_url=args.ctx_url)

    # -----------------------------------------------------------------------
    # Verify admin connectivity
    # -----------------------------------------------------------------------
    try:
        client.health()
        print(f"✅ Connected to Context Retriever: {args.ctx_url}")
    except Exception as e:
        print(f"❌ Cannot reach Context Retriever: {e}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Check for existing surface
    # -----------------------------------------------------------------------
    existing_surface = None
    try:
        surfaces = client.list_context_surfaces(admin_key=args.admin_key)
        for s in surfaces.items if hasattr(surfaces, "items") else []:
            if s.name == SURFACE_NAME:
                existing_surface = s
                break
    except Exception as e:
        print(f"⚠️  Could not list surfaces: {e}")

    if existing_surface and not args.overwrite:
        print(f"\nℹ️  Surface '{SURFACE_NAME}' already exists (id: {existing_surface.id})")
        print("   Use --overwrite to recreate it, or skip this step and create an agent key.")
    else:
        if existing_surface and args.overwrite:
            try:
                client.delete_context_surface(existing_surface.id, admin_key=args.admin_key)
                print(f"✅ Deleted existing surface '{SURFACE_NAME}'")
            except Exception as e:
                print(f"⚠️  Could not delete existing surface: {e}")

        # -----------------------------------------------------------------------
        # Build data model
        # -----------------------------------------------------------------------
        print("\nBuilding data model...")
        data_model = build_data_model()
        entities = [e["name"] for e in data_model["entities"]]
        print(f"✅ Data model built: {len(entities)} entities — {entities}")

        # -----------------------------------------------------------------------
        # Parse Redis connection
        # -----------------------------------------------------------------------
        try:
            redis_conn = parse_redis_url(args.redis_url)
            print(f"✅ Redis connection parsed: {redis_conn['addr']}  tls={redis_conn['tls_enabled']}")
        except Exception as e:
            print(f"❌ Could not parse REDIS_URL: {e}")
            sys.exit(1)

        # -----------------------------------------------------------------------
        # Create the context surface
        # -----------------------------------------------------------------------
        print(f"\nCreating context surface '{SURFACE_NAME}'...")
        try:
            surface = client.create_context_surface(
                CreateContextSurfaceRequest(
                    name=SURFACE_NAME,
                    description=(
                        "Redis Eats Agentic Workshop — gives the support agent "
                        "access to live order, customer, and restaurant data."
                    ),
                    data_model=data_model,
                    data_source=DataSourceRequest(
                        type="redis",
                        connection_config=DataSourceConnectionConfig(**redis_conn),
                    ),
                ),
                admin_key=args.admin_key,
            )
            existing_surface = surface
            print(f"✅ Surface created")
            print(f"   ID     : {surface.id}")
            print(f"   Name   : {surface.name}")
            print(f"   Status : {surface.status}")
            if hasattr(surface, "tools") and surface.tools:
                print(f"   Tools  : {[t.name if hasattr(t,'name') else t for t in surface.tools]}")
        except Exception as e:
            print(f"❌ Surface creation failed: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)

    # -----------------------------------------------------------------------
    # Create agent key
    # -----------------------------------------------------------------------
    print(f"\nCreating agent key '{AGENT_KEY_NAME}'...")
    try:
        agent_key = client.create_agent_key(
            surface_id=existing_surface.id,
            request=CreateAgentKeyRequest(name=AGENT_KEY_NAME),
            admin_key=args.admin_key,
        )
        print(f"✅ Agent key created")
    except Exception as e:
        print(f"❌ Agent key creation failed: {e}")
        print("   If an agent key already exists, retrieve it from the Redis Cloud console.")
        import traceback; traceback.print_exc()
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Print final summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 62)
    print("  Context Retriever setup complete!")
    print()
    print("  Paste these values into Section 1.1 of the notebook:")
    print()
    print(f"  CTX_SURFACES_URL = \"{args.ctx_url}\"")
    print(f"  CTX_ADMIN_KEY    = \"{args.admin_key}\"")
    print(f"  CTX_AGENT_KEY    = \"{agent_key.key}\"")
    print(f"  CTX_MCP_URL      = \"<get from Redis Cloud console — Context Retriever → MCP URL>\"")
    print()
    print("  Surface ID for reference:")
    print(f"    {existing_surface.id}")
    print("=" * 62)


if __name__ == "__main__":
    main()

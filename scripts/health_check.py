#!/usr/bin/env python3
"""
SpaceShipIO - Utility scripts for n8n workflows.

Place any helper scripts here that are called via the Execute Command node
or HTTP-requested from n8n workflows.
"""

import sys
from datetime import datetime, timezone


def health_check() -> dict:
    """Simple health check callable by n8n HTTP Request node."""
    return {
        "status": "ok",
        "project": "SpaceShipIO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import json

    result = health_check()
    print(json.dumps(result, indent=2))

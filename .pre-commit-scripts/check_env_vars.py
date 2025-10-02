#!/usr/bin/env python3
"""Check that all required environment variables are documented."""

import os
import sys
from pathlib import Path

def check_env_vars():
    """Check environment variables consistency."""
    root_dir = Path(__file__).parent.parent
    env_example = root_dir / ".env.example"

    if not env_example.exists():
        print("⚠️  .env.example not found")
        return 0

    # Read .env.example
    with open(env_example) as f:
        example_vars = set(
            line.split("=")[0].strip()
            for line in f
            if line.strip() and not line.startswith("#") and "=" in line
        )

    # Check each service's environment variables
    issues = []

    for service_dir in (root_dir / "services").glob("*"):
        if not service_dir.is_dir():
            continue

        service_env_example = service_dir / ".env.example"
        if service_env_example.exists():
            with open(service_env_example) as f:
                service_vars = set(
                    line.split("=")[0].strip()
                    for line in f
                    if line.strip() and not line.startswith("#") and "=" in line
                )

            # Check for undocumented vars
            missing = service_vars - example_vars
            if missing:
                issues.append(f"{service_dir.name}: Missing in root .env.example: {missing}")

    if issues:
        print("❌ Environment variable issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Environment variables are consistent")
    return 0

if __name__ == "__main__":
    sys.exit(check_env_vars())

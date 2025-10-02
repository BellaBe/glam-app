# ruff: noqa: T201
"""Validate proper EventContext usage across services."""

import ast
import sys
from pathlib import Path


def check_event_context_usage():
    """Ensure EventContext.create() calls include proper correlation handling."""
    errors = []

    for py_file in Path("src").rglob("*.py"):
        if py_file.name.startswith("__"):
            continue

        with open(py_file) as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.Call)
                        and hasattr(node.func, "attr")
                        and node.func.attr == "create"
                        and hasattr(node.func, "value")
                        and hasattr(node.func.value, "id")
                        and node.func.value.id == "EventContext"
                    ):
                        # Check if correlation_id is properly handled
                        keywords = {kw.arg for kw in node.keywords if kw.arg}
                        if "correlation_id" not in keywords:
                            errors.append(
                                f"{py_file}:{node.lineno} - EventContext.create() missing correlation_id parameter"
                            )
            except SyntaxError:
                continue

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("\nTip: Add correlation_id parameter to EventContext.create() calls", file=sys.stderr)
        print("Example: EventContext.create(..., correlation_id=get_correlation_context())", file=sys.stderr)
        sys.exit(1)

    print("✅ All EventContext.create() calls properly handle correlation_id")


def check_uuid_usage():
    """Ensure uuid7() is used instead of uuid4() for event IDs."""
    errors = []

    for py_file in Path("src").rglob("*.py"):
        if py_file.name.startswith("__"):
            continue

        with open(py_file) as f:
            content = f.read()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "uuid4()" in line and "import" not in line:
                    errors.append(f"{py_file}:{i} - Use uuid7() instead of uuid4()")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("\nTip: Use uuid7() for monotonic ordering in events", file=sys.stderr)
        sys.exit(1)

    print("✅ All UUID usage follows monotonic ordering")


if __name__ == "__main__":
    check_event_context_usage()
    check_uuid_usage()

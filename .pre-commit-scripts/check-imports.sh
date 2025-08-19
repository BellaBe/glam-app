#!/bin/bash
for dir in services/*; do
  if [ -f "$dir/pyproject.toml" ]; then
    (cd "$dir" && poetry run python -c "import shared; import config" 2>/dev/null || echo "Warning: shared imports not available in $dir")
  fi
done

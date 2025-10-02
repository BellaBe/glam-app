#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Split a concatenated code artifact into proper files, based on header lines
# that look like:
#   # services/analytics-service/src/models/enums.py
#
# Works for *any* service, any language.  Creates missing dirs & __init__.py.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ───── config ────────────────────────────────────────────────────────────────
ARTIFACT="${1:-/dev/stdin}"       # file to read; defaults to STDIN
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# helper: create __init__.py up the tree of a python file
ensure_inits () {
  local file="$1";                               # full path to .py
  local dir
  dir="$(dirname "$file")"
  while [[ "$dir" != "$ROOT" && "$dir" != / ]]; do
    [[ "${file##*.}" == "py" ]] || break         # only python trees
    touch "${dir}/__init__.py"
    dir="$(dirname "$dir")"
  done
}

echo "📦  Distributing artifact → $ROOT"
current_file=""

# read artifact line‑by‑line
while IFS='' read -r line || [[ -n "$line" ]]; do
  # header pattern:   # path/to/file.ext
  if [[ "$line" =~ ^#\ ([[:alnum:]_.@/-]+)$ ]]; then
    rel_path="${BASH_REMATCH[1]}"
    current_file="$ROOT/$rel_path"
    mkdir -p "$(dirname "$current_file")"
    : > "$current_file"                          # truncate / create
    echo "  • $rel_path"
    [[ "$current_file" == *.py ]] && ensure_inits "$current_file"
    continue
  fi

  # write body lines
  [[ -n "$current_file" ]] && printf '%s\n' "$line" >> "$current_file"
done < "$ARTIFACT"

echo "✅  Done!  Artifact exploded into individual files."

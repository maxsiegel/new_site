#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$ROOT_DIR/templates/personal.mustache"
MONOREPO_ROOT="$(cd "$ROOT_DIR/.." && pwd)"
INPUT="$MONOREPO_ROOT/pubs.bib"
OUTPUT="$ROOT_DIR/src/pubs.html"

if ! command -v bibtex-render >/dev/null 2>&1; then
    echo "Error: bibtex-render not found in PATH." >&2
    exit 1
fi

for path in "$TEMPLATE" "$INPUT"; do
    if [[ ! -f "$path" ]]; then
        echo "Error: missing required file: $path" >&2
        exit 1
    fi
done

bibtex-render -t "$TEMPLATE" "$INPUT" -o "$OUTPUT"
echo "Rendered: $OUTPUT"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$ROOT_DIR/src"
PUBLIC_DIR="$ROOT_DIR/public"
TEMPLATE="$SRC_DIR/index.template.html"
MAIN_FRAGMENT="$SRC_DIR/main.html"
PUBS_FRAGMENT="$SRC_DIR/pubs.html"
OUTPUT="$PUBLIC_DIR/index.html"

for path in "$TEMPLATE" "$MAIN_FRAGMENT" "$PUBS_FRAGMENT"; do
    if [ ! -f "$path" ]; then
        echo "Missing required file: $path" >&2
        exit 1
    fi
done

mkdir -p "$PUBLIC_DIR"

awk -v main="$MAIN_FRAGMENT" -v pubs="$PUBS_FRAGMENT" '
function print_file(path, line) {
    while ((getline line < path) > 0) {
        print line
    }
    close(path)
}
{
    if ($0 ~ /<!-- @MAIN_HTML@ -->/) {
        print_file(main)
        next
    }
    if ($0 ~ /<!-- @PUBS_HTML@ -->/) {
        print_file(pubs)
        next
    }
    print
}
' "$TEMPLATE" > "$OUTPUT"

echo "Built $OUTPUT"

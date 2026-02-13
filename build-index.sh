#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$ROOT_DIR/index.template.html"
MAIN_FRAGMENT="$ROOT_DIR/main.html"
PUBS_FRAGMENT="$ROOT_DIR/pubs.html"
OUTPUT="$ROOT_DIR/index.html"

for path in "$TEMPLATE" "$MAIN_FRAGMENT" "$PUBS_FRAGMENT"; do
    if [ ! -f "$path" ]; then
        echo "Missing required file: $path" >&2
        exit 1
    fi
done

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

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PUBLIC_DIR="$ROOT_DIR/public"
HOST="${MIT_WEB_HOST:-athena.dialup.mit.edu}"
KERB="${1:-${MIT_KERBEROS:-}}"

if [[ -z "$KERB" ]]; then
    echo "Usage: $0 <kerberos>" >&2
    echo "   or: MIT_KERBEROS=<kerberos> $0" >&2
    exit 1
fi

REMOTE="${KERB}@${HOST}"

echo "Building index.html..."
"$SCRIPT_DIR/build-index.sh"

echo "Ensuring ~/www exists and is world-readable..."
ssh "$REMOTE" 'mkdir -p ~/www && fs sa ~/www system:anyuser rl'

echo "Syncing files to ${REMOTE}:~/www/ ..."
rsync -avz --delete \
    --exclude '.DS_Store' \
    "$PUBLIC_DIR/" "${REMOTE}:~/www/"

echo "Deploy complete: https://web.mit.edu/${KERB}/www/"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PUBLIC_DIR="$ROOT_DIR/public"
HOST="${MIT_WEB_HOST:-athena.dialup.mit.edu}"
KERB="maxs"

REMOTE="${KERB}@${HOST}"

echo "Building index.html..."
"$SCRIPT_DIR/build-index.sh"

echo "Ensuring ~/www exists and is world-readable..."
ssh "$REMOTE" 'mkdir -p ~/www && fs sa ~/www system:anyuser rl'

echo "Syncing files to ${REMOTE}:~/www/ ..."
rsync -avz --delete \
    --exclude '.DS_Store' \
    "$PUBLIC_DIR/" "${REMOTE}:~/www/"

echo "Refreshing AFS ACLs on published directories..."
ssh "$REMOTE" '
set -euo pipefail
fs sa ~/www system:anyuser rl
if [ -d ~/www ]; then
  find ~/www -type d -exec fs sa {} system:anyuser rl \;
fi
if [ -d ~/site/public ]; then
  find ~/site/public -type d -exec fs sa {} system:anyuser rl \;
fi
'

echo "Deploy complete: https://web.mit.edu/${KERB}/www/"

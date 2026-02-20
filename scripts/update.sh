#!/usr/bin/env bash
set -euo pipefail

KERB="maxs"
HOST="athena.dialup.mit.edu"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"
git push origin master

ssh "${KERB}@${HOST}" <<'EOF'
set -euo pipefail
cd "$HOME/site"
git pull --ff-only origin master
./scripts/build-index.sh
mkdir -p "$HOME/www"
fs sa "$HOME/www" system:anyuser rl
if [ -d "$HOME/www" ]; then
  find "$HOME/www" -type d -exec fs sa {} system:anyuser rl \;
fi
if [ -d "$HOME/site/public" ]; then
  find "$HOME/site/public" -type d -exec fs sa {} system:anyuser rl \;
fi
EOF

echo "Published: https://web.mit.edu/${KERB}/www/"

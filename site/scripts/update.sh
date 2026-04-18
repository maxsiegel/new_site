#!/usr/bin/env bash
set -euo pipefail

KERB="maxs"
HOST="athena.dialup.mit.edu"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_PATHS=(
  public
  scripts/build-index.sh
  src
)

cd "$ROOT_DIR"

if [ -n "$(git status --porcelain -- "${DEPLOY_PATHS[@]}")" ]; then
  echo "Uncommitted or untracked deploy files. Commit them before deploying:" >&2
  git status --short -- "${DEPLOY_PATHS[@]}" >&2
  exit 1
fi

git push origin master

ssh "${KERB}@${HOST}" <<'EOF'
set -euo pipefail
cd "$HOME/site"
git fetch origin master
git reset --hard origin/master
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

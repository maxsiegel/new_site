#!/usr/bin/env bash
set -euo pipefail

KERB="maxs"
HOST="athena.dialup.mit.edu"
SITE_REMOTE="${SITE_REMOTE:-git@github.com:maxsiegel/site.git}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [ -n "$(git status --porcelain -- .)" ]; then
  echo "Uncommitted or untracked site files. Commit them before deploying:" >&2
  git status --short -- . >&2
  exit 1
fi

git push origin master
DEPLOY_COMMIT="$(git subtree split --prefix=site HEAD)"
git push "$SITE_REMOTE" "${DEPLOY_COMMIT}:master"

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

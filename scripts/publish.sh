#!/usr/bin/env bash
set -euo pipefail

KERB="maxs"
HOST="athena.dialup.mit.edu"
SITE_DIR="\$HOME/site"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"
git push origin master

ssh "${KERB}@${HOST}" "set -euo pipefail
cd \"$SITE_DIR\"
git pull --ff-only origin master
./scripts/build-index.sh"

echo "Published: https://web.mit.edu/${KERB}/www/"

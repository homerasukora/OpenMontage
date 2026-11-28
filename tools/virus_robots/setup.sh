#!/bin/bash
# Fetches renderer dependencies (not committed): three.js and the Xbot robot model.
set -euo pipefail
cd "$(dirname "$0")"
npm install --no-audit --no-fund
mkdir -p assets
[ -f assets/Xbot.glb ] || curl -sSL -o assets/Xbot.glb https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/Xbot.glb
echo "ok"

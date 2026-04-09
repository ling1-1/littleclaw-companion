#!/bin/zsh
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
LittleClaw Companion upgrader

Usage:
  ./installer/upgrade.sh

Behavior:
  - reruns install.sh
  - preserves pet state
  - refreshes runtime mirror, presets, and assets
  - restarts pet service and Companion service
EOF
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Upgrading LittleClaw Companion runtime..."
"$ROOT_DIR/installer/install.sh"

echo
echo "Upgrade complete."
echo "Pet state and install seed were preserved."

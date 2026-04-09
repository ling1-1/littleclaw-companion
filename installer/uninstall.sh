#!/bin/zsh
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
LittleClaw Companion uninstall helper

Usage:
  ./installer/uninstall.sh

Current behavior:
  - non-destructive helper
  - shows runtime and data paths
  - preserves pet state by default
EOF
  exit 0
fi

OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
RUNTIME_HOME="${LITTLECLAW_RUNTIME_HOME:-$OPENCLAW_HOME/workspace/littleclaw-runtime}"
PRESETS_HOME="${LITTLECLAW_PRESETS_HOME:-$OPENCLAW_HOME/workspace/littleclaw-presets}"
ASSETS_HOME="${LITTLECLAW_ASSETS_HOME:-$OPENCLAW_HOME/workspace/littleclaw-assets}"

echo "LittleClaw Companion uninstall plan"
echo
echo "This script currently preserves data by default."
echo "Review these runtime locations if you want to wipe mirrored files manually:"
echo "  $RUNTIME_HOME"
echo "  $PRESETS_HOME"
echo "  $ASSETS_HOME"
echo
echo "Pet state is preserved in:"
echo "  $OPENCLAW_HOME/workspace/memory/pet-state.json"

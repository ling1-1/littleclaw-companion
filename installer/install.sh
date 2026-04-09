#!/bin/zsh
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
LittleClaw Companion installer

Usage:
  ./installer/install.sh

Optional environment variables:
  OPENCLAW_HOME
  LITTLECLAW_RUNTIME_HOME
  LITTLECLAW_PRESETS_HOME
  LITTLECLAW_ASSETS_HOME
  LITTLECLAW_OWNER_AGENT_NAME
  LITTLECLAW_PYTHON_BIN

What this installer does:
  - syncs runtime core / bridge / ui / presets / assets
  - writes runtime-config.json
  - bootstraps first pet if no state exists
  - restarts pet service
  - installs or restarts Companion LaunchAgent
EOF
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
RUNTIME_HOME="${LITTLECLAW_RUNTIME_HOME:-$OPENCLAW_HOME/workspace/littleclaw-runtime}"
PRESETS_HOME="${LITTLECLAW_PRESETS_HOME:-$OPENCLAW_HOME/workspace/littleclaw-presets}"
ASSETS_HOME="${LITTLECLAW_ASSETS_HOME:-$OPENCLAW_HOME/workspace/littleclaw-assets}"
MANIFEST_PATH="${LITTLECLAW_MANIFEST_PATH:-$RUNTIME_HOME/install-manifest.json}"
OWNER_AGENT_NAME="${LITTLECLAW_OWNER_AGENT_NAME:-OpenClaw}"
COMPANION_LABEL="${LITTLECLAW_COMPANION_LABEL:-ai.openclaw.littleclaw-companion}"
COMPANION_PLIST="${LITTLECLAW_COMPANION_PLIST:-$HOME/Library/LaunchAgents/${COMPANION_LABEL}.plist}"
RUNTIME_CONFIG_PATH="${LITTLECLAW_RUNTIME_CONFIG_PATH:-$RUNTIME_HOME/runtime-config.json}"

find_python_bin() {
  local requested="${LITTLECLAW_PYTHON_BIN:-}"
  local root_parent
  local root_grandparent
  root_parent="$(cd "$ROOT_DIR/.." && pwd)"
  root_grandparent="$(cd "$ROOT_DIR/../.." && pwd)"
  local candidates=()

  if [ -n "$requested" ]; then
    candidates+=("$requested")
  fi

  candidates+=(
    "$ROOT_DIR/.venv/bin/python"
    "$root_parent/.venv/bin/python"
    "$root_grandparent/.venv/bin/python"
    "/usr/bin/python3"
  )

  local cand
  for cand in "${candidates[@]}"; do
    if [ -x "$cand" ] && "$cand" -c "import objc, WebKit" >/dev/null 2>&1; then
      echo "$cand"
      return 0
    fi
  done

  for cand in "${candidates[@]}"; do
    if [ -x "$cand" ]; then
      echo "$cand"
      return 0
    fi
  done

  echo "/usr/bin/python3"
}

PYTHON_BIN="$(find_python_bin)"

sync_tree() {
  local src="$1"
  local dst="$2"
  mkdir -p "$dst"
  rsync -a --delete "$src"/ "$dst"/
}

cat > /tmp/littleclaw-manifest.json <<EOF
{
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "repo_root": "$ROOT_DIR",
  "openclaw_home": "$OPENCLAW_HOME",
  "runtime_home": "$RUNTIME_HOME",
  "presets_home": "$PRESETS_HOME",
  "assets_home": "$ASSETS_HOME"
}
EOF

cat > /tmp/littleclaw-runtime-config.json <<EOF
{
  "repo_root": "$RUNTIME_HOME",
  "source_repo_root": "$ROOT_DIR",
  "openclaw_home": "$OPENCLAW_HOME",
  "plugin_home": "$RUNTIME_HOME",
  "runtime_home": "$RUNTIME_HOME",
  "presets_path": "$PRESETS_HOME",
  "assets_path": "$ASSETS_HOME",
  "ui_root": "$RUNTIME_HOME/ui",
  "direct_send_script": "$RUNTIME_HOME/direct_send_openclaw.py",
  "python_executable": "$PYTHON_BIN",
  "pet_api_port": 18793,
  "openclaw_host": "127.0.0.1",
  "openclaw_port": 18789,
  "owner_agent_name": "$OWNER_AGENT_NAME"
}
EOF

echo "Installing LittleClaw Companion runtime..."
echo "  repo:      $ROOT_DIR"
echo "  openclaw:  $OPENCLAW_HOME"
echo "  runtime:   $RUNTIME_HOME"
echo "  presets:   $PRESETS_HOME"
echo "  assets:    $ASSETS_HOME"

sync_tree "$ROOT_DIR/core" "$RUNTIME_HOME/core"
sync_tree "$ROOT_DIR/bridge" "$RUNTIME_HOME/bridge"
sync_tree "$ROOT_DIR/presets" "$PRESETS_HOME"
sync_tree "$ROOT_DIR/ui/assets" "$ASSETS_HOME"
sync_tree "$ROOT_DIR/ui" "$RUNTIME_HOME/ui"
cp "$ROOT_DIR/companion_webview.py" "$RUNTIME_HOME/companion_webview.py"
cp "$ROOT_DIR/direct_send_openclaw.py" "$RUNTIME_HOME/direct_send_openclaw.py"
cp "$ROOT_DIR/runtime_config.py" "$RUNTIME_HOME/runtime_config.py"

cat > "$RUNTIME_HOME/run-companion.sh" <<EOF
#!/bin/zsh
set -euo pipefail
export LITTLECLAW_RUNTIME_CONFIG="$RUNTIME_CONFIG_PATH"
exec "$PYTHON_BIN" "$RUNTIME_HOME/companion_webview.py"
EOF
chmod +x "$RUNTIME_HOME/run-companion.sh"

mkdir -p "$(dirname "$COMPANION_PLIST")"
cat > "$COMPANION_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>$COMPANION_LABEL</string>

    <key>ProgramArguments</key>
    <array>
      <string>$RUNTIME_HOME/run-companion.sh</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PYTHONUNBUFFERED</key>
      <string>1</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>WorkingDirectory</key>
    <string>$RUNTIME_HOME</string>

    <key>StandardOutPath</key>
    <string>/tmp/littleclaw-webview.out.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/littleclaw-webview.err.log</string>
  </dict>
</plist>
EOF

mkdir -p "$(dirname "$MANIFEST_PATH")"
cp /tmp/littleclaw-manifest.json "$MANIFEST_PATH"
cp /tmp/littleclaw-runtime-config.json "$RUNTIME_CONFIG_PATH"
rm -f /tmp/littleclaw-manifest.json
rm -f /tmp/littleclaw-runtime-config.json

BOOTSTRAP_RESULT="$(/usr/bin/python3 "$ROOT_DIR/installer/bootstrap_pet.py" "$OPENCLAW_HOME" "$RUNTIME_HOME" "$PRESETS_HOME" "$OWNER_AGENT_NAME")"
PET_AGENT_STATUS="not-found"
COMPANION_STATUS="not-found"

if launchctl print "gui/$(id -u)/ai.openclaw.pet-ui" >/dev/null 2>&1; then
  if launchctl kickstart -k "gui/$(id -u)/ai.openclaw.pet-ui" >/dev/null 2>&1; then
    PET_AGENT_STATUS="restarted"
  else
    PET_AGENT_STATUS="restart-failed"
  fi
fi

if [ -f "$COMPANION_PLIST" ]; then
  if launchctl print "gui/$(id -u)/${COMPANION_LABEL}" >/dev/null 2>&1; then
    if launchctl kickstart -k "gui/$(id -u)/${COMPANION_LABEL}" >/dev/null 2>&1; then
      COMPANION_STATUS="restarted"
    else
      COMPANION_STATUS="restart-failed"
    fi
  else
    if launchctl bootstrap "gui/$(id -u)" "$COMPANION_PLIST" >/dev/null 2>&1; then
      COMPANION_STATUS="bootstrapped"
    else
      COMPANION_STATUS="bootstrap-failed"
    fi
  fi
fi

echo
echo "LittleClaw runtime installed."
echo "Manifest:"
echo "  $MANIFEST_PATH"
echo "Runtime config:"
echo "  $RUNTIME_CONFIG_PATH"
echo "Pet bootstrap:"
echo "  $BOOTSTRAP_RESULT"
echo "Pet service:"
echo "  $PET_AGENT_STATUS"
echo "Companion service:"
echo "  $COMPANION_STATUS"
echo
echo "Quick verification:"
echo "  curl -s http://127.0.0.1:18793/health"
echo "  curl -s http://127.0.0.1:18793/pet"
echo "  /bin/zsh -lc \"launchctl print gui/\$(id -u)/${COMPANION_LABEL}\""
echo
echo "Next suggested steps:"
echo "- verify Companion UI refresh"
echo "- if this is a fresh install, check the first-pet welcome flow"

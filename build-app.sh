#!/bin/zsh
set -euo pipefail

APP_DIR="/Users/baijingting/Documents/Playground/LittleClaw Companion.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RES_DIR="${CONTENTS_DIR}/Resources"

rm -rf "${APP_DIR}"
mkdir -p "${MACOS_DIR}" "${RES_DIR}"

cat > "${CONTENTS_DIR}/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>LittleClawCompanion</string>
  <key>CFBundleIdentifier</key>
  <string>ai.openclaw.littleclaw-companion</string>
  <key>CFBundleName</key>
  <string>LittleClaw Companion</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
</dict>
</plist>
EOF

cat > "${MACOS_DIR}/LittleClawCompanion" <<'EOF'
#!/bin/zsh
export PYTHONUNBUFFERED=1
exec /Users/baijingting/Documents/Playground/littleclaw-companion/.venv/bin/python /Users/baijingting/Documents/Playground/littleclaw-companion/companion_webview.py >> /tmp/littleclaw-webview-app.log 2>&1
EOF

chmod +x "${MACOS_DIR}/LittleClawCompanion"
echo "${APP_DIR}"

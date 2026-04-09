#!/bin/zsh
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
LittleClaw Companion release packager

Usage:
  ./installer/package-release.sh

What it does:
  - creates a clean release directory under ./dist
  - copies only the supported runtime / installer / docs files
  - excludes legacy and local-only development files
  - builds a .tar.gz archive for local release testing
EOF
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
PKG_NAME="littleclaw-companion-release"
PKG_DIR="$DIST_DIR/$PKG_NAME"
ARCHIVE_PATH="$DIST_DIR/${PKG_NAME}.tar.gz"

rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

copy_tree() {
  local src="$1"
  local dst="$2"
  mkdir -p "$dst"
  rsync -a --delete "$src"/ "$dst"/
}

copy_file() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
}

copy_file "$ROOT_DIR/README.md" "$PKG_DIR/README.md"
copy_file "$ROOT_DIR/runtime_config.py" "$PKG_DIR/runtime_config.py"
copy_file "$ROOT_DIR/companion_webview.py" "$PKG_DIR/companion_webview.py"
copy_file "$ROOT_DIR/direct_send_openclaw.py" "$PKG_DIR/direct_send_openclaw.py"

copy_tree "$ROOT_DIR/core" "$PKG_DIR/core"
copy_tree "$ROOT_DIR/bridge" "$PKG_DIR/bridge"
copy_tree "$ROOT_DIR/ui" "$PKG_DIR/ui"
copy_tree "$ROOT_DIR/presets" "$PKG_DIR/presets"
copy_tree "$ROOT_DIR/installer" "$PKG_DIR/installer"
copy_tree "$ROOT_DIR/docs" "$PKG_DIR/docs"

rm -f "$PKG_DIR/installer/package-release.sh"
rm -f "$ARCHIVE_PATH"

(
  cd "$DIST_DIR"
  tar -czf "$ARCHIVE_PATH" "$PKG_NAME"
)

echo "Release package created:"
echo "  dir:  $PKG_DIR"
echo "  archive: $ARCHIVE_PATH"

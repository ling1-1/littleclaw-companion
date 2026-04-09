# Release Contents

## Include In First Public Release

- `README.md`
- `core/`
- `bridge/`
- `ui/`
- `presets/`
- `installer/`
- `docs/`
- `runtime_config.py`
- `companion_webview.py`
- `direct_send_openclaw.py`

These files are enough for:
- installer-managed runtime setup
- pet service bridge support
- Companion UI runtime
- preset-driven species / rarity / growth

## Keep Out Of First Public Release

Treat these as legacy or dev-only for now:
- `companion.py`
- `companion_appkit.py`
- `run-appkit.sh`
- `run-companion.sh`
- `build-app.sh`
- `Sources/main.swift`
- local backup files
- local caches / virtualenv / compiled artifacts

## Why

The supported public path today is:
- Python + WebView Companion
- installer-managed runtime mirror
- installer-managed pet service + Companion LaunchAgent

The legacy paths still exist for iteration history, but they are not the cleanest first-run path for outside users.

# Open Source Notes

## Distributable Path

The intended distributable path is:
- `core/`
- `bridge/`
- `ui/`
- `presets/`
- `installer/`
- `docs/`

These are mirrored into OpenClaw-local runtime during install.

## Developer-Only / Legacy Files

These exist in the repo today but are not part of the preferred distributable runtime:
- `companion.py`
- `companion_appkit.py`
- `run-appkit.sh`
- `run-companion.sh`
- `build-app.sh`
- `Sources/main.swift`

They can remain for experimentation, but should be clearly treated as legacy or dev-only if the repo is published.

## Local Path Audit

Known local-path-bearing files still present in repo:
- legacy launch / appkit scripts
- legacy Swift prototype
- some docs use absolute local file links for local navigation in Codex

Before public release, prefer:
- repo-relative paths in markdown intended for GitHub
- runtime-config-driven paths in executable code

## Publishing Recommendation

For the first public GitHub release:
- keep the runtime Python + WebView path as the primary supported implementation
- mark Swift / AppKit experiments as non-supported
- avoid advertising experimental entrypoints in README

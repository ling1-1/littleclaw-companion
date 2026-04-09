# LittleClaw Companion

LittleClaw Companion is a pet-style desktop companion for OpenClaw.

It combines:
- a floating desktop companion
- a pet growth system driven by real OpenClaw usage
- screenshot / file / direct-send bridges into the current OpenClaw session
- species / rarity / evolution presets that can grow into a reusable plugin package

## Current Status

Working today:
- Companion desktop shell
- Pet API and persistent pet state
- XP + affinity split growth system
- Species / rarity preset loading
- Screenshot / file staging and upload into current OpenClaw chat
- Installer-managed runtime mirror
- First-pet onboarding flow

Still evolving:
- Multi-species polished asset packs
- Install-time first-pet reveal experience
- Fully polished GitHub-ready distribution flow

## Quick Start

Requirements:
- macOS
- local OpenClaw already installed
- `~/.openclaw` available

Install:

```bash
./installer/install.sh
```

Upgrade:

```bash
./installer/upgrade.sh
```

Uninstall:

```bash
./installer/uninstall.sh
```

After install:
- the pet service should be running on `http://127.0.0.1:18793`
- the Companion LaunchAgent should be installed
- your existing pet should be preserved, or a first pet should be initialized

Useful checks:

```bash
curl -s http://127.0.0.1:18793/health
curl -s http://127.0.0.1:18793/pet
/bin/zsh -lc "launchctl print gui/$(id -u)/ai.openclaw.littleclaw-companion"
```

## Runtime Layout

Installer-managed runtime paths:
- runtime: `~/.openclaw/workspace/littleclaw-runtime`
- presets: `~/.openclaw/workspace/littleclaw-presets`
- assets: `~/.openclaw/workspace/littleclaw-assets`
- pet state: `~/.openclaw/workspace/memory/pet-state.json`

## Repository Layout

- `core/`: pet domain model and rules
- `bridge/`: OpenClaw integration points
- `ui/`: desktop Companion UI
- `presets/`: rarity, growth, and species presets
- `installer/`: install, upgrade, and uninstall entrypoints
- `docs/`: product and technical design

## Docs

- install plan: [docs/INSTALL_PLAN.md](docs/INSTALL_PLAN.md)
- plugin architecture: [docs/PLUGIN_ARCHITECTURE.md](docs/PLUGIN_ARCHITECTURE.md)
- product roadmap: [docs/PRODUCT_ROADMAP.md](docs/PRODUCT_ROADMAP.md)
- quick start: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- release checklist: [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
- release contents: [docs/RELEASE_CONTENTS.md](docs/RELEASE_CONTENTS.md)
- open source notes: [docs/OPEN_SOURCE_NOTES.md](docs/OPEN_SOURCE_NOTES.md)

## Supported Path

Current primary supported implementation:
- installer-managed Python + WebView runtime
- installer-managed pet service
- installer-managed Companion LaunchAgent

If you only want the supported path, start with:
- `./installer/install.sh`
- `./installer/upgrade.sh`
- `./installer/uninstall.sh`
- `./installer/package-release.sh`

## Legacy / Experimental

The following files still exist for development history or experiments, but are not the primary public path:
- `companion.py`
- `companion_appkit.py`
- `run-appkit.sh`
- `run-companion.sh`
- `build-app.sh`
- `Sources/main.swift`

## Notes

- Existing pet progress is preserved by default.
- Care actions primarily restore state and affinity; real work drives XP and evolution.
- Species and rarity are now preset-driven, but the visual asset system is still being expanded.

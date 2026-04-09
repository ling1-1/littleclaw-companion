# Install Plan

## Goal

A GitHub user should be able to:
1. clone or download the repo
2. run one install command
3. see LittleClaw Companion appear with either:
   - their existing pet preserved
   - or a first pet initialized automatically

## Current Supported Flow

Installer currently handles:
- runtime mirror sync
- preset sync
- asset sync
- runtime config generation
- pet bootstrap
- pet service restart
- Companion LaunchAgent install / restart

## Runtime Paths

Default runtime locations:
- OpenClaw home: `~/.openclaw`
- Companion runtime: `~/.openclaw/workspace/littleclaw-runtime`
- presets mirror: `~/.openclaw/workspace/littleclaw-presets`
- assets mirror: `~/.openclaw/workspace/littleclaw-assets`
- pet state: `~/.openclaw/workspace/memory/pet-state.json`

## Install Command

```bash
./installer/install.sh
```

Optional env overrides:
- `OPENCLAW_HOME`
- `LITTLECLAW_RUNTIME_HOME`
- `LITTLECLAW_PRESETS_HOME`
- `LITTLECLAW_ASSETS_HOME`
- `LITTLECLAW_OWNER_AGENT_NAME`
- `LITTLECLAW_PYTHON_BIN`

## Upgrade Command

```bash
./installer/upgrade.sh
```

Expected behavior:
- keep current pet state
- refresh runtime mirror
- refresh presets and assets
- restart Companion and pet service

## Uninstall Command

```bash
./installer/uninstall.sh
```

Expected behavior for now:
- non-destructive by default
- shows runtime paths
- preserves pet state unless user manually removes it

## Verification Checklist

After install, verify:
- `curl -s http://127.0.0.1:18793/health`
- `curl -s http://127.0.0.1:18793/pet`
- `launchctl print gui/$(id -u)/ai.openclaw.pet-ui`
- `launchctl print gui/$(id -u)/ai.openclaw.littleclaw-companion`

Expected outcomes:
- pet API returns `ok: true`
- pet payload returns current pet
- both launch agents show as loaded / running

## Future Install UX

Planned next refinement:
- first install opens a full “meet your first pet” welcome page
- install summary shows:
  - pet name
  - species
  - rarity
  - stage
- optional GitHub release package with one-line copy/paste install

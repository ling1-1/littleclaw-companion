# Plugin Architecture

## Goal

Turn the current local Companion into a reusable, installable OpenClaw add-on.

## Package shape

```text
littleclaw-companion/
  core/
  bridge/
  ui/
  assets/
  presets/
  installer/
  docs/
```

## Runtime components

### 1. Pet API service

Responsibilities:
- keep pet state
- apply growth rules
- serve current pet status
- generate random encounter pets

Current source of truth:
- `/Users/baijingting/.openclaw/scripts/openclaw-pet-api.py`

Future plugin target:
- `core/pet_service.py`

Current status:
- runtime already imports `core/pet_core.py`
- installer mirrors runtime core into OpenClaw-local storage

### 2. Companion desktop shell

Responsibilities:
- show compact / expanded UI
- dispatch actions to OpenClaw
- preview attachments and screenshots
- show reply summaries

Current source of truth:
- `companion_webview.py`

Future plugin target:
- `ui/desktop/companion_webview.py`

Current status:
- Companion already runs from installer-managed runtime mirror
- LaunchAgent now points to runtime launcher instead of repo source

### 3. OpenClaw bridge

Responsibilities:
- direct-send text and attachments to current OpenClaw chat
- capture screenshots
- read final assistant replies

Current source of truth:
- `direct_send_openclaw.py`
- pieces of `companion_webview.py`

Future plugin target:
- `bridge/openclaw_bridge.py`

Current status:
- direct-send logic has been extracted into `bridge/direct_send.py`
- thin runtime entrypoint remains for compatibility

## Install model

The installer should:
- detect OpenClaw home
- install presets to an OpenClaw-local writable directory
- install or update LaunchAgents
- point Companion and Pet API to plugin-managed config
- keep user pet state outside the repo

## Config model

Install-time config should include:
- OpenClaw home path
- plugin home path
- pet state path
- presets path
- ui assets path
- launch mode

## Asset model

Assets should be grouped by species and stage.

Example:

```text
assets/
  lobster/
    seed.svg
    coral.svg
    reef.svg
    royal.svg
    mythic.svg
  sprite/
    seed.svg
    mist.svg
    star.svg
    oracle.svg
  mecha/
    seed.svg
    servo.svg
    forge.svg
    core.svg
```

## Distribution target

Phase 1:
- local install script
- local upgrade script
- GitHub-ready docs and quickstart

Phase 2:
- GitHub repo with release artifacts
- simple install command

Phase 3:
- OpenClaw community install flow

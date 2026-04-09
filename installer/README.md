# Installer

This directory contains the current installer entrypoints for the supported runtime path.

Available entrypoints:
- `install.sh`
- `upgrade.sh`
- `uninstall.sh`

The installer does not keep user state inside the repo. It installs runtime files into a stable user-local location and preserves:
- pet state
- launch configuration
- presets mirror

Supported flow:
- mirror runtime files into OpenClaw-local storage
- bootstrap first pet if needed
- preserve existing pet if already present
- restart pet service
- install or restart Companion LaunchAgent

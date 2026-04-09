# Release Checklist

## Before Publishing

- Confirm installer works on a clean OpenClaw setup
- Confirm upgrade preserves existing pet state
- Confirm uninstall remains non-destructive by default
- Confirm Companion LaunchAgent points to runtime launcher, not repo source
- Confirm pet API LaunchAgent can restart cleanly
- Confirm first-pet onboarding appears only for fresh installs
- Confirm existing users do not get onboarding again
- Confirm screenshot / file staging still works after install
- Confirm direct send still works against current OpenClaw chat
- Confirm reply capture still waits for final assistant summary

## Open-Source Hygiene

- Remove or ignore local backup files
- Ignore `.venv/`, `__pycache__/`, and generated Python caches
- Document any remaining developer-only scripts
- Avoid introducing personal absolute paths into distributable modules
- Keep local-only experiments out of the release path

## Docs

- README has install / upgrade / uninstall examples
- QUICKSTART exists and matches installer behavior
- INSTALL_PLAN reflects current runtime layout
- PLUGIN_ARCHITECTURE reflects current extraction status

## Release Smoke Test

Run:

```bash
./installer/install.sh
curl -s http://127.0.0.1:18793/health
curl -s http://127.0.0.1:18793/pet
/bin/zsh -lc "launchctl print gui/$(id -u)/ai.openclaw.littleclaw-companion"
```

Expected:
- install completes without manual patching
- pet API responds
- pet payload returns current pet
- Companion LaunchAgent is running
- Companion UI refreshes with current pet

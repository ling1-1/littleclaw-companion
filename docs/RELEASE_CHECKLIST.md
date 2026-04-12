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
- Confirm work buttons stay clickable while waiting for a real OpenClaw reply
- Confirm the unified Canvas renderer covers all shipped species and stages
- Confirm compact badge / expanded panel / pet island all use the current pet-first layout
- Confirm learning modal can continuously input Chinese without the IME candidate being interrupted
- Confirm expanded island defaults to the real current state instead of stale "处理中" copy
- Confirm encounter flow, first-pet onboarding, and partner switching still render fully in the current window size

## Open-Source Hygiene

- Remove or ignore local backup files
- Ignore `.venv/`, `__pycache__/`, and generated Python caches
- Document any remaining developer-only scripts
- Decide whether `debug_ui_enabled` should be `false` for the release runtime config while keeping local debug tools available
- Avoid introducing personal absolute paths into distributable modules
- Keep local-only experiments out of the release path
- Keep engineering-only notes separate from public-facing release copy where needed

## Docs

- README has install / upgrade / uninstall examples
- README.zh-CN reflects the current Canvas + pet-island UI
- QUICKSTART exists and matches installer behavior
- INSTALL_PLAN reflects current runtime layout
- PLUGIN_ARCHITECTURE reflects current extraction status
- Release notes mention the current UI redesign and species expansion
- Engineering notes exist for major regressions that were fixed during the release cycle

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
- release runtime hides the debug entry by default

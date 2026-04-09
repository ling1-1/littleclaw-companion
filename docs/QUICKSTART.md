# Quick Start

## 1. Install

```bash
./installer/install.sh
```

## 2. Verify

```bash
curl -s http://127.0.0.1:18793/health
curl -s http://127.0.0.1:18793/pet
/bin/zsh -lc "launchctl print gui/$(id -u)/ai.openclaw.littleclaw-companion"
```

What you should see:
- pet API is healthy
- current pet JSON is returned
- Companion LaunchAgent is loaded

## 3. Upgrade

```bash
./installer/upgrade.sh
```

## 4. Uninstall

```bash
./installer/uninstall.sh
```

## Notes

- Existing pet state is preserved by default.
- First install will initialize a pet if no pet state exists.
- If a pet already exists, installer keeps that pet and refreshes runtime files.

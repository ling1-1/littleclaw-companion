#!/usr/bin/env python3
import json
import os
from pathlib import Path


DEFAULT_OPENCLAW_HOME = Path.home() / ".openclaw"
DEFAULT_REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_RUNTIME_HOME = DEFAULT_OPENCLAW_HOME / "workspace" / "littleclaw-runtime"
DEFAULT_CONFIG_PATH = DEFAULT_RUNTIME_HOME / "runtime-config.json"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_runtime_config() -> dict:
    config_path = Path(
        os.environ.get("LITTLECLAW_RUNTIME_CONFIG") or DEFAULT_CONFIG_PATH
    ).expanduser()
    raw = _load_json(config_path) if config_path.exists() else {}

    openclaw_home = Path(raw.get("openclaw_home") or os.environ.get("OPENCLAW_HOME") or DEFAULT_OPENCLAW_HOME).expanduser()
    repo_root = Path(raw.get("repo_root") or os.environ.get("LITTLECLAW_REPO_ROOT") or DEFAULT_REPO_ROOT).expanduser()
    runtime_home = Path(raw.get("plugin_home") or raw.get("runtime_home") or os.environ.get("LITTLECLAW_RUNTIME_HOME") or (openclaw_home / "workspace" / "littleclaw-runtime")).expanduser()
    presets_home = Path(raw.get("presets_path") or os.environ.get("LITTLECLAW_PRESETS_HOME") or (openclaw_home / "workspace" / "littleclaw-presets")).expanduser()
    assets_home = Path(raw.get("assets_path") or os.environ.get("LITTLECLAW_ASSETS_HOME") or (openclaw_home / "workspace" / "littleclaw-assets")).expanduser()
    ui_root = Path(raw.get("ui_root") or os.environ.get("LITTLECLAW_UI_ROOT") or (repo_root / "ui")).expanduser()
    direct_send_script = Path(raw.get("direct_send_script") or os.environ.get("LITTLECLAW_DIRECT_SEND_SCRIPT") or (repo_root / "direct_send_openclaw.py")).expanduser()
    python_executable = str(raw.get("python_executable") or os.environ.get("LITTLECLAW_PYTHON") or "/usr/bin/python3")
    pet_api_port = int(raw.get("pet_api_port") or os.environ.get("LITTLECLAW_PET_API_PORT") or 18793)
    openclaw_host = str(raw.get("openclaw_host") or os.environ.get("LITTLECLAW_OPENCLAW_HOST") or "127.0.0.1")
    openclaw_port = int(raw.get("openclaw_port") or os.environ.get("LITTLECLAW_OPENCLAW_PORT") or 18789)
    debug_ui_enabled = bool(raw.get("debug_ui_enabled", True))

    return {
        "config_path": config_path,
        "repo_root": repo_root,
        "openclaw_home": openclaw_home,
        "runtime_home": runtime_home,
        "presets_home": presets_home,
        "assets_home": assets_home,
        "ui_root": ui_root,
        "direct_send_script": direct_send_script,
        "python_executable": python_executable,
        "pet_api_port": pet_api_port,
        "pet_api_base": f"http://127.0.0.1:{pet_api_port}",
        "openclaw_host": openclaw_host,
        "openclaw_port": openclaw_port,
        "openclaw_base": f"http://{openclaw_host}:{openclaw_port}",
        "debug_ui_enabled": debug_ui_enabled,
    }

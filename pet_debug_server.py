#!/usr/bin/env python3
import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.pet_core import PetRuntime
from runtime_config import load_runtime_config

RUNTIME = load_runtime_config()
HOST = "127.0.0.1"
PORT = 18796
PET_API = f"{RUNTIME['pet_api_base']}/pet"
PET_ACTION_API = f"{RUNTIME['pet_api_base']}/pet/action"
STATE_FILE = RUNTIME["openclaw_home"] / "workspace" / "memory" / "pet-state.json"
INSTALL_FILE = RUNTIME["openclaw_home"] / "workspace" / "memory" / "pet-install-id.txt"
PRESETS_ROOT = Path(RUNTIME["presets_home"])
FALLBACK_PRESET_ROOT = Path(__file__).resolve().parent / "presets"
LOG_FILE = Path("/tmp/littleclaw-debug-tool.log")
DEBUG_HTML = Path(__file__).resolve().parent / "ui" / "debug.html"

PET_RUNTIME = PetRuntime(
    state_file=STATE_FILE,
    install_seed_file=INSTALL_FILE,
    preset_root=PRESETS_ROOT,
    fallback_preset_root=FALLBACK_PRESET_ROOT,
)


def log(message: str):
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(message.rstrip() + "\n")
    except Exception:
        pass


def fetch_json(url: str):
    try:
        with urlopen(url, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError:
        return None
    except Exception:
        log("fetch_json failed:\n" + traceback.format_exc())
        return None


def post_json(url: str, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def current_state():
    pet = fetch_json(PET_API)
    if isinstance(pet, dict):
        return pet
    return PET_RUNTIME.load_state()


def stage_adjusted_state(state: dict, species_id: str, stage_id: str, payload: dict) -> dict:
    stages = PET_RUNTIME.evolution_stages(species_id)
    index = next((idx for idx, item in enumerate(stages) if item["id"] == stage_id), 0)
    target = stages[index]
    nxt = stages[index + 1] if index + 1 < len(stages) else None

    level = max(int(payload.get("level", target["min_level"])), int(target["min_level"]))
    affinity = max(int(payload.get("affinity", target["min_affinity"])), int(target["min_affinity"]))
    streak = max(int(payload.get("reward_streak", target["min_streak"])), int(target["min_streak"]))
    progress = max(int(payload.get("progress", target.get("min_progress", 0))), int(target.get("min_progress", 0)))

    if nxt is not None:
        level = min(level, max(int(target["min_level"]), int(nxt["min_level"]) - 1))
        affinity = min(affinity, max(int(target["min_affinity"]), int(nxt["min_affinity"]) - 1))
        streak = min(streak, max(int(target["min_streak"]), int(nxt["min_streak"]) - 1))
        progress = min(progress, max(int(target.get("min_progress", 0)), int(nxt.get("min_progress", 0)) - 1))

    state["level"] = level
    state["affinity"] = affinity
    state["reward_streak"] = streak
    state["task_score"] = progress
    state["total_actions"] = max(int(state.get("total_actions", 0)), progress * 2)
    return state


def apply_debug_pet(payload: dict):
    state = PET_RUNTIME.load_state()
    species_id = str(payload.get("species_id") or state.get("species_id") or "lobster")
    species = PET_RUNTIME.species_config(species_id)
    role = PET_RUNTIME.role_config(species_id, payload.get("role_id") or state.get("role_id"))
    state["species_id"] = species_id
    state["species_title"] = species.get("title", state.get("species_title", "龙虾系"))
    state["species"] = species.get("title", state.get("species", "龙虾系"))
    state["role_id"] = role.get("id", state.get("role_id", "companion"))
    state["role_title"] = role.get("title", state.get("role_title", "陪伴型"))
    state["rarity"] = str(payload.get("rarity") or state.get("rarity") or "common").lower()
    state["xp"] = max(0, min(99, int(payload.get("xp", state.get("xp", 0)))))
    state["energy"] = max(0, min(100, int(payload.get("energy", state.get("energy", 78)))))
    state["hunger"] = max(0, min(100, int(payload.get("hunger", state.get("hunger", 22)))))
    state["onboarding_pending"] = False
    stage_id = str(payload.get("stage_id") or "").strip()
    if stage_id:
        state = stage_adjusted_state(state, species_id, stage_id, payload)
    else:
        if "level" in payload:
            state["level"] = max(1, int(payload.get("level", state.get("level", 1))))
        if "affinity" in payload:
            state["affinity"] = max(0, min(100, int(payload.get("affinity", state.get("affinity", 75)))))
    PET_RUNTIME.save_state(state)
    return current_state()


class DebugHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log(fmt % args)

    def read_json(self):
        size = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(size) if size > 0 else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def send_json(self, payload: dict, code: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text: str, content_type: str = "text/html; charset=utf-8", code: int = 200):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            if self.path in {"/", "/index.html"}:
                self.send_text(DEBUG_HTML.read_text(encoding="utf-8"))
                return
            if self.path == "/api/state":
                self.send_json({"ok": True, "pet": current_state()})
                return
            if self.path == "/api/catalog":
                self.send_json({"ok": True, "catalog": PET_RUNTIME.species_catalog()})
                return
            self.send_text("Not Found", "text/plain; charset=utf-8", 404)
        except Exception as exc:
            log("GET failed:\n" + traceback.format_exc())
            self.send_json({"ok": False, "error": str(exc)}, 500)

    def do_POST(self):
        try:
            payload = self.read_json()
            if self.path == "/api/state":
                pet = apply_debug_pet(payload)
                self.send_json({"ok": True, "pet": pet})
                return
            if self.path == "/api/action":
                action = str(payload.get("action") or "").strip()
                if not action:
                    self.send_json({"ok": False, "error": "missing action"}, 400)
                    return
                result = post_json(PET_ACTION_API, payload)
                self.send_json({"ok": True, "result": result, "pet": current_state()})
                return
            self.send_text("Not Found", "text/plain; charset=utf-8", 404)
        except Exception as exc:
            log("POST failed:\n" + traceback.format_exc())
            self.send_json({"ok": False, "error": str(exc)}, 500)


def main():
    log("debug server boot")
    server = ThreadingHTTPServer((HOST, PORT), DebugHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()

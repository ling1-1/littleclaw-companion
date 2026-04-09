#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.pet_core import PetRuntime  # noqa: E402


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: bootstrap_pet.py <openclaw_home> <runtime_home> <presets_home> <owner_agent_name>", file=sys.stderr)
        return 2

    openclaw_home = Path(sys.argv[1]).expanduser()
    runtime_home = Path(sys.argv[2]).expanduser()
    presets_home = Path(sys.argv[3]).expanduser()
    owner_agent_name = sys.argv[4]

    state_file = openclaw_home / "workspace/memory/pet-state.json"
    install_seed_file = openclaw_home / "workspace/memory/pet-install-id.txt"

    runtime = PetRuntime(
        state_file=state_file,
        install_seed_file=install_seed_file,
        preset_root=presets_home,
        fallback_preset_root=ROOT_DIR / "presets",
    )

    existed = state_file.exists()
    pet = runtime.load_state()
    if not existed:
        pet["owner_agent_name"] = owner_agent_name
        runtime.save_state(pet)

    result = {
        "initialized": not existed,
        "pet_id": pet.get("pet_id"),
        "name": pet.get("name"),
        "species_id": pet.get("species_id"),
        "species_title": pet.get("species_title"),
        "rarity": pet.get("rarity"),
        "level": pet.get("level"),
        "stage_title": pet.get("stage_title"),
        "onboarding_pending": pet.get("onboarding_pending", False),
        "summary": (
            f"初次相遇：{pet.get('name')} · {pet.get('species_title')} · {pet.get('stage_title')}"
            if not existed
            else f"保留现有主宠：{pet.get('name')} · {pet.get('species_title')} · Lv.{pet.get('level')}"
        ),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

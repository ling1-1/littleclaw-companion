#!/usr/bin/env python3
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional


DEFAULT_SPECIES_ID = "lobster"

STAGE_EXTRAS = {
    "seed": {"form": "pet", "presence": "刚学会陪伴，会安静跟着你。"},
    "coral": {"form": "companion", "presence": "开始理解你的节奏，会主动给陪伴反馈。"},
    "reef": {"form": "avatar", "presence": "已经有一点数字人感，能替你组织动作。"},
    "royal": {"form": "partner", "presence": "更像一个一起做事的搭子，而不是单纯宠物。"},
    "mythic": {"form": "partner", "presence": "已经是高阶搭子了，适合一起处理更完整、更困难的任务。"},
    "companion": {"form": "companion", "presence": "开始理解你的节奏，会主动给陪伴反馈。"},
    "avatar": {"form": "avatar", "presence": "已经有一点数字人感，能替你组织动作。"},
    "partner": {"form": "partner", "presence": "更像一个一起做事的搭子，而不是单纯宠物。"},
}

DEFAULT_ROLE = {
    "id": "companion",
    "title": "陪伴型",
    "presence": "偏陪伴协作，会稳稳跟着你的节奏往前走。",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_dt():
    return datetime.now(timezone.utc)


def parse_ts(value: str):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def load_json(path: Path, fallback: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


@dataclass
class PetRuntime:
    state_file: Path
    install_seed_file: Path
    preset_root: Path
    fallback_preset_root: Path

    def __post_init__(self):
        self.species_cache = {}
        self.rarity_config = self.preset_json("rarity.json", {"rarities": []})
        self.growth_rules = self.preset_json("growth-rules.json", {"tracks": {}, "evolution": {}})

    @property
    def species_root(self) -> Path:
        return self.preset_root / "species"

    def preset_json(self, relative_path: str, fallback: dict) -> dict:
        primary = self.preset_root / relative_path
        secondary = self.fallback_preset_root / relative_path
        if primary.exists():
            return load_json(primary, fallback)
        if secondary.exists():
            return load_json(secondary, fallback)
        return fallback

    def species_config(self, species_id: str) -> dict:
        key = str(species_id or DEFAULT_SPECIES_ID)
        if key in self.species_cache:
            return self.species_cache[key]
        fallback = {
            "id": DEFAULT_SPECIES_ID,
            "title": "龙虾系",
            "default_names": ["小钳"],
            "stages": [],
        }
        config = self.preset_json(f"species/{key}.json", fallback)
        if not config.get("stages"):
            config["stages"] = [
                {"id": "seed", "title": "琥珀幼体", "min_level": 1, "min_affinity": 0, "min_streak": 0, "min_progress": 0},
                {"id": "companion", "title": "陪伴助手", "min_level": 2, "min_affinity": 78, "min_streak": 1, "min_progress": 2},
                {"id": "avatar", "title": "数字小助手", "min_level": 4, "min_affinity": 90, "min_streak": 2, "min_progress": 5},
                {"id": "partner", "title": "共工搭子", "min_level": 6, "min_affinity": 96, "min_streak": 3, "min_progress": 10},
            ]
        self.species_cache[key] = config
        return config

    def evolution_stages(self, species_id: str) -> list:
        config = self.species_config(species_id)
        stages = []
        default_forms = ["pet", "companion", "avatar", "partner", "partner"]
        default_presence = {
            "pet": "刚学会陪伴，会安静跟着你。",
            "companion": "开始理解你的节奏，会主动给陪伴反馈。",
            "avatar": "已经有一点数字人感，能替你组织动作。",
            "partner": "更像一个一起做事的搭子，而不是单纯宠物。",
        }
        for index, stage in enumerate(config.get("stages", [])):
            extra = STAGE_EXTRAS.get(stage.get("id", ""), {})
            form = extra.get("form", default_forms[min(index, len(default_forms) - 1)])
            stages.append({
                **stage,
                "form": form,
                "presence": extra.get("presence", default_presence.get(form, "开始陪着你一起做事。")),
            })
        return stages

    def role_options(self, species_id: str) -> list:
        config = self.species_config(species_id)
        roles = list(config.get("roles") or [])
        if not roles:
            return [dict(DEFAULT_ROLE)]
        normalized = []
        for role in roles:
            role_id = str(role.get("id") or "").strip()
            if not role_id:
                continue
            normalized.append({
                "id": role_id,
                "title": str(role.get("title") or role_id),
                "presence": str(role.get("presence") or DEFAULT_ROLE["presence"]),
            })
        return normalized or [dict(DEFAULT_ROLE)]

    def role_config(self, species_id: str, role_id: Optional[str] = None) -> dict:
        options = self.role_options(species_id)
        if role_id:
            match = next((role for role in options if role["id"] == str(role_id)), None)
            if match:
                return match
        return options[0]

    def species_catalog(self) -> dict:
        species = []
        for config in self.available_species():
            species_id = str(config.get("id") or DEFAULT_SPECIES_ID)
            species.append({
                "id": species_id,
                "title": str(config.get("title") or species_id),
                "rarity_pool": list(config.get("rarity_pool") or []),
                "default_names": list(config.get("default_names") or []),
                "traits": list(config.get("traits") or []),
                "roles": self.role_options(species_id),
                "stages": [
                    {
                        "id": str(stage.get("id") or "seed"),
                        "title": str(stage.get("title") or stage.get("id") or "初始形态"),
                        "min_level": int(stage.get("min_level", 1)),
                        "min_affinity": int(stage.get("min_affinity", 0)),
                        "min_streak": int(stage.get("min_streak", 0)),
                        "min_progress": int(stage.get("min_progress", 0)),
                    }
                    for stage in self.evolution_stages(species_id)
                ],
            })
        return {"species": species}

    def install_seed_salt(self) -> str:
        try:
            if self.install_seed_file.exists():
                value = self.install_seed_file.read_text(encoding="utf-8").strip()
                if value:
                    return value
            self.install_seed_file.parent.mkdir(parents=True, exist_ok=True)
            salt = os.urandom(12).hex()
            self.install_seed_file.write_text(salt + "\n", encoding="utf-8")
            return salt
        except Exception:
            return "fallback-install-seed"

    def stable_seed(self, owner_agent_name: str = "OpenClaw") -> str:
        host = os.environ.get("HOSTNAME") or os.uname().nodename
        base = f"{owner_agent_name}|{host}|{self.install_seed_salt()}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def rarity_table(self) -> list:
        return list(self.rarity_config.get("rarities") or [])

    def rarity_pick(self, seed: str) -> str:
        table = self.rarity_table()
        if not table:
            return "legendary"
        total = sum(max(0, int(item.get("weight", 0))) for item in table) or 1
        value = int(hashlib.sha256(f"{seed}:rarity".encode("utf-8")).hexdigest()[:8], 16) % total
        cursor = 0
        for item in table:
            cursor += max(0, int(item.get("weight", 0)))
            if value < cursor:
                return str(item.get("id", "common"))
        return str(table[-1].get("id", "common"))

    def available_species(self) -> list:
        species = []
        try:
            for path in sorted(self.species_root.glob("*.json")):
                config = load_json(path, {})
                if config.get("id"):
                    species.append(config)
        except Exception:
            pass
        if not species:
            species.append(self.species_config(DEFAULT_SPECIES_ID))
        return species

    def species_pick(self, seed: str, rarity_id: str) -> dict:
        candidates = []
        for config in self.available_species():
            pool = list(config.get("rarity_pool") or [])
            if not pool or rarity_id in pool:
                candidates.append(config)
        if not candidates:
            candidates = [self.species_config(DEFAULT_SPECIES_ID)]
        index = int(hashlib.sha256(f"{seed}:species".encode("utf-8")).hexdigest()[:8], 16) % len(candidates)
        return candidates[index]

    def pet_name_pick(self, seed: str, species: dict) -> str:
        names = list(species.get("default_names") or []) or ["小钳"]
        index = int(hashlib.sha256(f"{seed}:name".encode("utf-8")).hexdigest()[:8], 16) % len(names)
        return names[index]

    def generated_identity_from_seed(
        self,
        seed: str,
        owner_agent_name: str = "OpenClaw",
        forced_species_id: Optional[str] = None,
        forced_rarity: Optional[str] = None,
    ) -> dict:
        rarity_id = forced_rarity or self.rarity_pick(seed)
        species = self.species_config(forced_species_id) if forced_species_id else self.species_pick(seed, rarity_id)
        species_id = species.get("id", DEFAULT_SPECIES_ID)
        pet_name = self.pet_name_pick(seed, species)
        return {
            "pet_id": f"pet_{species_id}_{seed[:10]}",
            "seed": seed,
            "species_id": species_id,
            "species_title": species.get("title", "龙虾系"),
            "species": species.get("title", "龙虾系"),
            "rarity": rarity_id,
            "name": pet_name,
            "owner_agent_name": owner_agent_name,
            "stage_title": (species.get("stages") or [{}])[0].get("title", "初始形态"),
            "role_id": self.role_config(species_id).get("id", DEFAULT_ROLE["id"]),
            "role_title": self.role_config(species_id).get("title", DEFAULT_ROLE["title"]),
        }

    def generated_identity(self, owner_agent_name: str = "OpenClaw") -> dict:
        return self.generated_identity_from_seed(self.stable_seed(owner_agent_name), owner_agent_name)

    def default_state(self) -> dict:
        identity = self.generated_identity("OpenClaw")
        return {
            "pet_id": identity["pet_id"],
            "seed": identity["seed"],
            "species_id": identity["species_id"],
            "species_title": identity["species_title"],
            "rarity": identity["rarity"],
            "name": identity["name"],
            "owner_agent_name": identity["owner_agent_name"],
            "species": identity["species"],
            "emoji": "🦞",
            "affinity": 75,
            "energy": 70,
            "hunger": 25,
            "last_action": "init",
            "last_updated": utc_now(),
            "reward_streak": 0,
            "level": 1,
            "xp": 0,
            "total_actions": 0,
            "task_score": 0,
            "care_streak": 0,
            "send_count": 0,
            "learn_count": 0,
            "screenshot_count": 0,
            "reply_count": 0,
            "hard_task_count": 0,
            "project_count": 0,
            "cooldowns": {},
            "recent_actions": [],
            "affinity_xp": 0,
            "form": "pet",
            "stage_id": "seed",
            "stage_title": identity["stage_title"],
            "stage_presence": "刚学会陪伴，会安静跟着你。",
            "role_id": identity.get("role_id", DEFAULT_ROLE["id"]),
            "role_title": identity.get("role_title", DEFAULT_ROLE["title"]),
            "onboarding_pending": True,
            "unlocked_features": ["pet_panel", "pet_actions"],
        }

    def evolve_features(self, stage_id: str) -> list:
        base = ["pet_panel", "pet_actions", "screenshot_send"]
        if stage_id in {"companion", "avatar", "partner"}:
            base.append("ambient_presence")
        if stage_id == "partner":
            base.append("digital_human_mode")
        return base

    def progress_score(self, data: dict) -> int:
        return max(
            int(data.get("task_score", 0)),
            int(data.get("total_actions", 0)) // 60 + int(data.get("reward_streak", 0)) * 2,
            int(data.get("send_count", 0))
            + int(data.get("learn_count", 0)) * 2
            + int(data.get("reply_count", 0)) * 2
            + int(data.get("hard_task_count", 0)) * 3
            + int(data.get("project_count", 0)) * 4,
        )

    def stage_for(self, data: dict) -> dict:
        progress = self.progress_score(data)
        stages = self.evolution_stages(str(data.get("species_id") or DEFAULT_SPECIES_ID))
        chosen = stages[0]
        for stage in stages:
            if (
                int(data.get("level", 1)) >= stage["min_level"]
                and int(data.get("affinity", 0)) >= stage["min_affinity"]
                and int(data.get("reward_streak", 0)) >= stage["min_streak"]
                and progress >= stage.get("min_progress", 0)
            ):
                chosen = stage
        return chosen

    def next_stage_requirements(self, data: dict, current_stage_id: str) -> dict:
        stages = self.evolution_stages(str(data.get("species_id") or DEFAULT_SPECIES_ID))
        current_index = next((idx for idx, stage in enumerate(stages) if stage["id"] == current_stage_id), len(stages) - 1)
        if current_index >= len(stages) - 1:
            return {
                "available": False,
                "title": "",
                "hint": "已经达到当前可进化的最高阶段。",
                "remaining": {},
            }
        target = stages[current_index + 1]
        progress = self.progress_score(data)
        remaining = {
            "level": max(0, int(target["min_level"]) - int(data.get("level", 1))),
            "affinity": max(0, int(target["min_affinity"]) - int(data.get("affinity", 0))),
            "streak": max(0, int(target["min_streak"]) - int(data.get("reward_streak", 0))),
            "progress": max(0, int(target.get("min_progress", 0)) - progress),
        }
        parts = []
        if remaining["level"] > 0:
            parts.append(f"再升 {remaining['level']} 级")
        if remaining["affinity"] > 0:
            parts.append(f"亲密再加 {remaining['affinity']}")
        if remaining["streak"] > 0:
            parts.append(f"连续有效协作还差 {remaining['streak']} 次")
        if remaining["progress"] > 0:
            parts.append(f"真实协作进度还差 {remaining['progress']}")
        hint = f"离 {target['title']} 不远了。"
        if parts:
            hint = f"想进化到 {target['title']}，还差：{'、'.join(parts)}。"
        return {"available": True, "title": target["title"], "hint": hint, "remaining": remaining}

    def normalize(self, data: dict) -> dict:
        merged = {**self.default_state(), **data}
        if not merged.get("seed") or not merged.get("pet_id") or not merged.get("species_id") or not merged.get("rarity"):
            identity = self.generated_identity(str(merged.get("owner_agent_name") or "OpenClaw"))
            merged.setdefault("pet_id", identity["pet_id"])
            merged.setdefault("seed", identity["seed"])
            merged.setdefault("species_id", identity["species_id"])
            merged.setdefault("species_title", identity["species_title"])
            merged.setdefault("species", identity["species"])
            merged.setdefault("rarity", identity["rarity"])
            merged.setdefault("name", identity["name"])
            merged.setdefault("owner_agent_name", identity["owner_agent_name"])

        last_updated_dt = parse_ts(merged.get("last_updated"))
        if last_updated_dt is None:
            last_updated_dt = utc_dt()
        elapsed_minutes = max(0, int((utc_dt() - last_updated_dt).total_seconds() // 60))
        if elapsed_minutes > 0:
            hunger_gain = min(60, max(1, elapsed_minutes // 4))
            energy_drop = min(36, elapsed_minutes // 10)
            merged["hunger"] = int(merged.get("hunger", 0)) + hunger_gain
            merged["energy"] = int(merged.get("energy", 0)) - energy_drop

        for key in ("affinity", "energy", "hunger"):
            merged[key] = clamp(int(merged.get(key, 0)), 0, 100)
        for key in (
            "reward_streak", "level", "xp", "total_actions", "task_score", "care_streak",
            "affinity_xp", "send_count", "learn_count", "screenshot_count", "reply_count",
            "hard_task_count", "project_count",
        ):
            merged[key] = max(0, int(merged.get(key, 0)))
        merged["level"] = max(1, merged["level"])
        merged["cooldowns"] = dict(merged.get("cooldowns") or {})
        merged["recent_actions"] = list(merged.get("recent_actions") or [])[-20:]
        if "onboarding_pending" in data:
            merged["onboarding_pending"] = bool(merged.get("onboarding_pending", False))
        else:
            merged["onboarding_pending"] = not (
                int(merged.get("total_actions", 0)) > 0
                or int(merged.get("level", 1)) > 1
                or int(merged.get("send_count", 0)) > 0
                or int(merged.get("learn_count", 0)) > 0
            )

        while merged["xp"] >= 100:
            merged["xp"] -= 100
            merged["level"] += 1

        stage = self.stage_for(merged)
        species = self.species_config(str(merged.get("species_id") or DEFAULT_SPECIES_ID))
        role = self.role_config(str(merged.get("species_id") or DEFAULT_SPECIES_ID), str(merged.get("role_id") or ""))
        merged["species_title"] = species.get("title", merged.get("species_title", "龙虾系"))
        merged.setdefault("species", species.get("title", "龙虾系"))
        merged["role_id"] = role.get("id", DEFAULT_ROLE["id"])
        merged["role_title"] = role.get("title", DEFAULT_ROLE["title"])
        merged["form"] = stage["form"]
        merged["stage_id"] = stage["id"]
        merged["stage_title"] = stage["title"]
        merged["asleep"] = merged["energy"] <= 10 or merged["hunger"] >= 88
        if merged["energy"] <= 10:
            merged["blocked_reason"] = "太困了，先让小钳睡一会儿再继续。"
            merged["stage_presence"] = "它已经困得睁不开眼，先小睡恢复精力。"
        elif merged["hunger"] >= 88:
            merged["blocked_reason"] = "太饿了，先喂食再让它继续工作。"
            merged["stage_presence"] = "小钳饿得不想干活了，先喂一下。"
        elif merged["energy"] <= 22:
            merged["blocked_reason"] = ""
            merged["stage_presence"] = "精力有点低，最好别连续派太重的任务。"
        elif merged["hunger"] >= 70:
            merged["blocked_reason"] = ""
            merged["stage_presence"] = "有点饿了，继续干活前最好先喂一口。"
        else:
            merged["blocked_reason"] = ""
            role_presence = str(role.get("presence") or "").strip()
            merged["stage_presence"] = f"{stage['presence']} {role_presence}".strip()
        merged["unlocked_features"] = self.evolve_features(stage["form"])
        merged["progress_score"] = self.progress_score(merged)
        merged["next_stage"] = self.next_stage_requirements(merged, stage["id"])
        return merged

    def save_state(self, data: dict) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        normalized = json.dumps(self.normalize(data), ensure_ascii=False, indent=2) + "\n"
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(self.state_file.parent), suffix=".tmp") as fh:
            fh.write(normalized)
            tmp_path = fh.name
        os.replace(tmp_path, self.state_file)

    def load_state(self) -> dict:
        if not self.state_file.exists():
            state = self.default_state()
            self.save_state(state)
            return self.normalize(state)
        return self.normalize(json.loads(self.state_file.read_text(encoding="utf-8")))

    def grant_progress(self, data: dict, xp_gain: int = 0, affinity_gain: int = 0) -> dict:
        data["xp"] = max(0, int(data.get("xp", 0))) + xp_gain
        data["affinity"] = clamp(int(data.get("affinity", 0)) + affinity_gain, 0, 100)
        data["total_actions"] = max(0, int(data.get("total_actions", 0))) + 1
        return data

    def grant_affinity(self, data: dict, amount: int = 0) -> dict:
        amount = max(0, int(amount))
        if amount <= 0:
            return data
        data["affinity"] = clamp(int(data.get("affinity", 0)) + amount, 0, 100)
        data["affinity_xp"] = max(0, int(data.get("affinity_xp", 0))) + amount
        return data

    def preserve_progress_pet(self, current: dict, generated: dict) -> dict:
        preserved_keys = [
            "affinity", "energy", "hunger", "last_action", "last_updated", "reward_streak",
            "level", "xp", "total_actions", "task_score", "care_streak", "send_count",
            "learn_count", "screenshot_count", "reply_count", "hard_task_count",
            "project_count", "cooldowns", "recent_actions", "affinity_xp",
            "role_id", "role_title",
        ]
        merged = dict(generated)
        for key in preserved_keys:
            if key in current:
                merged[key] = current[key]
        merged["owner_agent_name"] = current.get("owner_agent_name") or generated.get("owner_agent_name") or "OpenClaw"
        return self.normalize(merged)

    def care_reward(self, now_dt, data: dict, action: str, *, hunger_delta: int = 0, energy_delta: int = 0, affinity_gain: int = 0):
        cooldown_minutes = {"feed": 8, "play": 5, "nap": 15}
        last_map = dict(data.get("cooldowns") or {})
        recent = list(data.get("recent_actions") or [])
        recent_same = [item for item in recent if item.get("action") == action]
        recent_count = len(recent_same)

        last_ts = parse_ts(last_map.get(action, ""))
        cooled = last_ts is None or (now_dt - last_ts).total_seconds() >= cooldown_minutes[action] * 60

        hunger = int(data.get("hunger", 0))
        energy = int(data.get("energy", 0))
        need_multiplier = 1.0
        if action == "feed":
            need_multiplier = 1.0 if hunger >= 55 else 0.45 if hunger >= 35 else 0.15
        elif action == "nap":
            need_multiplier = 1.0 if energy <= 35 else 0.45 if energy <= 55 else 0.15
        elif action == "play":
            need_multiplier = 1.0 if energy >= 25 else 0.35

        decay_multiplier = 1.0 if recent_count == 0 else 0.45 if recent_count == 1 else 0.12
        cooldown_multiplier = 1.0 if cooled else 0.25

        # Feeding and napping should always be able to recover core state.
        # Cooldown/decay mainly affect affinity gain so users can't exploit them for progression.
        state_multiplier = need_multiplier
        affinity_multiplier = need_multiplier * decay_multiplier * cooldown_multiplier
        if action == "play":
            state_multiplier = need_multiplier * decay_multiplier * cooldown_multiplier

        data["hunger"] = clamp(hunger + int(round(hunger_delta * max(state_multiplier, 0.2))), 0, 100)
        data["energy"] = clamp(energy + int(round(energy_delta * max(state_multiplier, 0.2))), 0, 100)
        data = self.grant_affinity(data, max(0, int(round(affinity_gain * max(affinity_multiplier, 0.15)))))
        data["total_actions"] = max(0, int(data.get("total_actions", 0))) + 1
        care_effective = max(state_multiplier, affinity_multiplier)
        data["care_streak"] = max(0, int(data.get("care_streak", 0))) + (1 if care_effective >= 0.4 else 0)
        last_map[action] = utc_now()
        data["cooldowns"] = last_map
        recent.append({"action": action, "ts": utc_now()})
        data["recent_actions"] = recent[-20:]
        return data

    @staticmethod
    def action_score(payload: dict, key: str, scale: int, cap: int) -> int:
        text = str(payload.get(key, "") or "")
        return min(cap, len(text.strip()) // scale) if text else 0

    def completion_bonus(self, payload: dict) -> int:
        text = str(payload.get("reply", "") or "")
        topic = str(payload.get("topic", "") or "")
        bonus = 0
        bonus += self.action_score(payload, "reply", 160, 18)
        bonus += self.action_score(payload, "topic", 40, 8)
        if any(word in text for word in ["完成", "修复", "方案", "总结", "结论", "通过", "已解决"]):
            bonus += 10
        if "```" in text:
            bonus += 8
        if any(word in topic for word in ["项目", "架构", "难题", "迁移", "重构", "调试", "排障"]):
            bonus += 10
        return min(42, bonus)

    @staticmethod
    def difficulty_bonus(payload: dict) -> int:
        text = " ".join(str(payload.get(key, "") or "") for key in ("text", "topic", "goal", "reply"))
        bonus = 0
        if any(word in text for word in ["项目", "架构", "重构", "迁移", "排障", "调试", "复杂", "难题", "闭环", "发布", "上线"]):
            bonus += 6
        if any(word in text for word in ["总结", "方案", "结论", "完成", "修复", "已解决", "落地"]):
            bonus += 4
        if text.count("```") >= 2:
            bonus += 4
        return min(16, bonus)

    @staticmethod
    def is_hard_task(payload: dict) -> bool:
        text = " ".join(str(payload.get(key, "") or "") for key in ("text", "topic", "goal", "reply"))
        return any(word in text for word in ["架构", "重构", "迁移", "排障", "调试", "复杂", "难题", "疑难", "卡住", "故障"])

    @staticmethod
    def is_project_task(payload: dict) -> bool:
        text = " ".join(str(payload.get(key, "") or "") for key in ("text", "topic", "goal", "reply"))
        return any(word in text for word in ["项目", "上线", "发布", "完整", "闭环", "交付", "里程碑", "方案落地"])

    def apply_action(self, action: str, data: dict, payload: Optional[dict] = None) -> dict:
        payload = payload or {}
        data = self.normalize(data)
        if action in {"send_message", "learn_request", "screenshot_send"} and data.get("asleep"):
            data["last_action"] = "sleep"
            data["last_updated"] = utc_now()
            return self.normalize(data)
        if action == "feed":
            data = self.care_reward(utc_dt(), data, "feed", hunger_delta=-18, energy_delta=4, affinity_gain=3)
        elif action == "play":
            data = self.care_reward(utc_dt(), data, "play", hunger_delta=6, energy_delta=-10, affinity_gain=6)
        elif action == "nap":
            data = self.care_reward(utc_dt(), data, "nap", hunger_delta=3, energy_delta=16, affinity_gain=2)
        elif action == "screenshot_send":
            data["energy"] = clamp(data["energy"] - 3, 0, 100)
            data["hunger"] = clamp(data["hunger"] + 2, 0, 100)
            data["task_score"] = max(0, int(data.get("task_score", 0))) + 2
            data["screenshot_count"] = max(0, int(data.get("screenshot_count", 0))) + 1
            if self.is_hard_task(payload):
                data["hard_task_count"] = max(0, int(data.get("hard_task_count", 0))) + 1
            data = self.grant_progress(data, xp_gain=18 + self.difficulty_bonus(payload), affinity_gain=2)
            data["reward_streak"] = max(data["reward_streak"], 2)
        elif action == "focus_companion":
            data = self.grant_affinity(data, 1)
            data["total_actions"] = max(0, int(data.get("total_actions", 0))) + 1
        elif action == "acknowledge_intro":
            data["onboarding_pending"] = False
            data = self.grant_affinity(data, 2)
            data["total_actions"] = max(0, int(data.get("total_actions", 0))) + 1
        elif action == "send_message":
            bonus = self.action_score(payload, "text", 40, 14)
            data["energy"] = clamp(data["energy"] - 2, 0, 100)
            data["hunger"] = clamp(data["hunger"] + 1, 0, 100)
            data["task_score"] = max(0, int(data.get("task_score", 0))) + 1
            data["send_count"] = max(0, int(data.get("send_count", 0))) + 1
            if self.is_hard_task(payload):
                data["hard_task_count"] = max(0, int(data.get("hard_task_count", 0))) + 1
            data = self.grant_progress(data, xp_gain=10 + bonus + self.difficulty_bonus(payload), affinity_gain=2)
        elif action == "learn_request":
            bonus = self.action_score(payload, "topic", 24, 12) + self.action_score(payload, "goal", 32, 12)
            data["energy"] = clamp(data["energy"] - 4, 0, 100)
            data["hunger"] = clamp(data["hunger"] + 2, 0, 100)
            data["task_score"] = max(0, int(data.get("task_score", 0))) + 3
            data["learn_count"] = max(0, int(data.get("learn_count", 0))) + 1
            if self.is_hard_task(payload):
                data["hard_task_count"] = max(0, int(data.get("hard_task_count", 0))) + 1
            if self.is_project_task(payload):
                data["project_count"] = max(0, int(data.get("project_count", 0))) + 1
            data = self.grant_progress(data, xp_gain=16 + bonus + self.difficulty_bonus(payload), affinity_gain=3)
        elif action == "reply_complete":
            bonus = self.completion_bonus(payload)
            data["energy"] = clamp(data["energy"] - 1, 0, 100)
            data["task_score"] = max(0, int(data.get("task_score", 0))) + max(2, bonus // 8)
            data["reply_count"] = max(0, int(data.get("reply_count", 0))) + 1
            if self.is_hard_task(payload):
                data["hard_task_count"] = max(0, int(data.get("hard_task_count", 0))) + 1
            if self.is_project_task(payload):
                data["project_count"] = max(0, int(data.get("project_count", 0))) + 1
            data = self.grant_progress(data, xp_gain=12 + bonus + self.difficulty_bonus(payload), affinity_gain=6)
            data["reward_streak"] = max(data["reward_streak"], 3 if bonus >= 18 else 2)
        else:
            raise ValueError("unsupported action")
        data["last_action"] = action
        data["last_updated"] = utc_now()
        return self.normalize(data)

    def encounter_seed(self, owner_agent_name: str = "OpenClaw") -> str:
        raw = f"{self.stable_seed(owner_agent_name)}|{utc_now()}|{os.urandom(6).hex()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def generated_pet_state(
        self,
        owner_agent_name: str = "OpenClaw",
        *,
        seed: Optional[str] = None,
        species_id: Optional[str] = None,
        rarity: Optional[str] = None,
    ) -> dict:
        base_seed = seed or self.stable_seed(owner_agent_name)
        identity = self.generated_identity_from_seed(base_seed, owner_agent_name, forced_species_id=species_id, forced_rarity=rarity)
        return self.normalize({
            **self.default_state(),
            **identity,
            "affinity": 72,
            "energy": 78,
            "hunger": 22,
            "level": 1,
            "xp": 0,
            "affinity_xp": 0,
            "reward_streak": 0,
            "task_score": 0,
            "care_streak": 0,
            "send_count": 0,
            "learn_count": 0,
            "screenshot_count": 0,
            "reply_count": 0,
            "hard_task_count": 0,
            "project_count": 0,
            "total_actions": 0,
            "cooldowns": {},
            "recent_actions": [],
            "last_action": "init",
            "last_updated": utc_now(),
            "onboarding_pending": True,
        })


def default_runtime(repo_root: Optional[Path] = None) -> PetRuntime:
    root = Path(repo_root or Path(__file__).resolve().parents[1])
    return PetRuntime(
        state_file=root / ".runtime" / "pet-state.json",
        install_seed_file=root / ".runtime" / "pet-install-id.txt",
        preset_root=root / "presets",
        fallback_preset_root=root / "presets",
    )

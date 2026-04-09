# Companion Pet Data Model

## Runtime State

```json
{
  "pet_id": "pet_littleclaw_001",
  "seed": "stable-seed-string",
  "species_id": "lobster",
  "species_title": "琥珀龙虾",
  "rarity": "legendary",
  "pet_name": "小钳",
  "owner_agent_name": "OpenClaw",
  "level": 12,
  "xp": 48,
  "affinity": 86,
  "affinity_xp": 22,
  "energy": 74,
  "hunger": 31,
  "mood": "idle",
  "asleep": false,
  "blocked_reason": "",
  "stage_id": "coral",
  "stage_title": "珊瑚巡游虾",
  "form": "pet",
  "task_score": 14,
  "reward_streak": 2,
  "total_actions": 81,
  "send_count": 8,
  "learn_count": 4,
  "screenshot_count": 3,
  "reply_count": 7,
  "hard_task_count": 2,
  "project_count": 1,
  "cooldowns": {},
  "recent_actions": [],
  "unlocked_features": [
    "pet_panel",
    "pet_actions",
    "screenshot_send"
  ],
  "stage_presence": "开始理解你的节奏，会主动给陪伴反馈。",
  "next_stage": {
    "available": true,
    "title": "礁岩战虾",
    "hint": "想进化到 礁岩战虾，还差：再升 3 级、真实协作进度还差 4。",
    "remaining": {
      "level": 3,
      "affinity": 0,
      "streak": 0,
      "progress": 4
    }
  }
}
```

## Model Notes

- `pet_id`: stable logical id
- `seed`: deterministic generation seed
- `species_id`: species pool key
- `rarity`: rarity bucket
- `level/xp`: work-growth track
- `affinity/affinity_xp`: care-growth track
- `task_score`: weighted work progress
- `reward_streak`: consecutive high-value collaboration streak
- `next_stage`: derived hint, not authoritative source of truth

## Non-Goals

- No user-editable direct XP injection
- No level growth from repeated care spam
- No stage changes based on UI-only interactions

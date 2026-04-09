# Core

This directory will host the reusable pet domain logic:
- pet state model
- growth rules
- rarity selection
- encounter generation
- evolution progress evaluation

Planned extraction targets:
- `pet_model.py`
- `growth_engine.py`
- `species_registry.py`
- `encounter_engine.py`

Current extracted module:
- `pet_core.py`

Minimal usage:

```python
from core import default_runtime

runtime = default_runtime()
state = runtime.load_state()
state = runtime.apply_action("send_message", state, {"text": "继续处理这个问题"})
runtime.save_state(state)
```

Current status:
- reusable runtime extracted
- live OpenClaw pet API has already been switched to import this module
- installer mirrors this module into OpenClaw-local runtime

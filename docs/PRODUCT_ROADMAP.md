# OpenClaw Companion Pets Roadmap

## Goal

Turn the current single-pet prototype into a reusable OpenClaw companion product that supports:

- per-user unique pets
- rarity and species pools
- stage-based evolution
- real event-driven growth
- installable distribution for other OpenClaw users

## Current Stage

We have a working prototype with:

- one active pet instance
- desktop companion UI
- OpenClaw bridge for send / learn / screenshot / reply
- hunger / energy / affinity / xp / level / stage
- anti-grind care rules
- first-pass evolution gating based on real work

## Delivery Phases

### Phase 1: Product Core

Target:

- separate pet state from current hard-coded UI behavior
- define stable data/config formats

Deliverables:

- `docs/DATA_MODEL.md`
- `presets/growth-rules.json`
- `presets/rarity.json`
- `presets/species/*.json`

### Phase 2: Multi-Pet Generation

Target:

- generate a unique pet on install
- support multiple species and rarity pools

Deliverables:

- install-time seed generation
- species pool selection
- rarity roll
- deterministic appearance/personality selection from seed

### Phase 3: Asset System

Target:

- replace one-off pet art with reusable species/stage asset packs

Deliverables:

- per-species stage assets
- shared animation contract
- compact / expanded asset consistency

### Phase 4: Pluginization

Target:

- package for GitHub release and install into other OpenClaw setups

Deliverables:

- installer
- updater
- uninstaller
- docs
- sample screenshots

## Product Principles

1. Real work grows the pet. Care actions do not replace collaboration.
2. UI should stay lightweight. Big data panels must stay hidden by default.
3. Companion states must be tied to real OpenClaw events, not fake loops.
4. Pet identity must be stable per install, but not identical across users.
5. Evolution is rare and meaningful. Level-up is common; evolution is a milestone.

## Immediate Next Build Targets

1. Wire the current prototype to read from `presets/growth-rules.json`
2. Add install-time pet seed generation
3. Support at least 3 species pools
4. Move current lobster pet into `presets/species/lobster.json`

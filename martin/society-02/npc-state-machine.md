# NPC State Machine

This document describes how NPCs (villagers) in Society decide what to do each turn. For the underlying movement model (one tile per turn, animation between turns, and the rule that two NPCs cannot share a tile) and for the game clock, see [README.md](README.md).

An NPC has multiple properties, each with a value from 0 to 1000. The values of these properties drive the NPC's behaviour. They change according to the rules in this state machine and through interactions with facilities around the map.

## NPC Properties

- fullness
- alertness

The values are shown as a percentage (0-100%) when an NPC is inspected (see "Inspecting Objects" in [README.md](README.md)).

The sections below list the NPC state machine rules.

## Hunger Rule

The "fullness" of an NPC decreases by two points each turn. If "fullness" falls below the current food threshold, the NPC heads straight for the nearest food source (a facility that can replenish fullness - an orchard). If "fullness" reaches 0, the NPC dies.

## Sleep Rule

The "alertness" of an NPC decreases by three points each turn. If "alertness" falls below the current rest threshold, the NPC heads straight for the nearest place to rest (a facility that can replenish alertness - a house). If "alertness" reaches 0, the NPC dies.

## Day/Night Thresholds

The day/night cycle (see "Game Clock and Day Cycle" in [README.md](README.md)) does not control NPC behaviour directly; instead it modulates the thresholds at which the hunger and sleep rules trigger. This keeps NPCs mostly - but not strictly - aligned to the cycle: they tend to eat by day and sleep at night, but a pressing need is acted on whatever the time.

The "below threshold" levels in the hunger and sleep rules are not fixed; they swing with the day/night cycle.

Each threshold is computed as `max(300, 200 + 700 * factor)`, where `factor` runs from 0 to 1 across the cycle. So a threshold swings between **300** (its floor) and **900** (its peak):

- The **rest** threshold uses the "night factor" (0 at noon, 1 at midnight), so it is **900 at midnight** and falls to its **300 floor by noon** - NPCs strongly tend to head to a house to sleep at night.
- The **food** threshold uses the opposite (1 at noon, 0 at midnight), so it is **900 at noon** and falls to its **300 floor by midnight** - NPCs strongly tend to head to an orchard to eat during the day.
- Because both thresholds are floored at 300, the survival rules above (a need below 300) always apply regardless of the time of day.

If both needs are below their thresholds at once, the NPC acts on the more depleted one first. When neither need is pressing, the NPC wanders.

Needs start between 700 and 1000 when an NPC is created. An NPC inside a facility leaves once the need being restored reaches **980** (nearly full), or sooner if its other need becomes the more urgent priority.

## Movement and Facility Use

When an NPC needs a facility it moves one tile per turn along the shortest path (breadth-first search over terrain and buildings, ignoring other NPCs, which move) toward the nearest facility of the required type. Reaching the facility's entrance it enters if there is spare capacity, otherwise it loiters nearby. While inside, the relevant need is replenished each turn; the NPC leaves once that need is nearly full, or sooner if its other need becomes the more urgent priority.

NPCs that are inside a facility are not drawn on the board; their presence is reflected in the facility's occupancy count. NPCs out on the board are drawn as coloured dots reflecting their state: amber while seeking/eating food, blue while seeking/taking rest, grey while idle (no pressing need).

## Death

When an NPC's fullness or alertness reaches 0 it dies. A dead villager is not removed from the world: it remains on the board at the tile where it died, drawn as a static grey body with a dark cross, and no longer moves or has needs. The population count in the HUD drops and a "Dead" count appears.

TODO: Only fullness and alertness exist so far. Richer properties (happiness, social needs) and behaviours such as having children are not yet implemented.

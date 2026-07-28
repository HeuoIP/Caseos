# CaseOS Theme Library

This directory holds the **content** layer for CaseOS Theme Taxonomy.
Each leaf theme is one MD file, named after its English label.

- **Total leaves:** 41
- **Total groups:** 9
- **Naming:** `<Label>.md` (PascalCase, spaces as underscores)
- **Rule (standard):** `docs/standards/CaseOS_Vision_Standard_V1.md` section 4

## Per-Theme File Schema

Every leaf MD follows the same 14 sections:

1. Story Core
2. Core Emotion
3. Learning Goal
4. Typical Color
5. Materials
6. Landscape
7. Children Behavior
8. Storyline (5 stages with arrows)
9. Design Language
10. Engineering
11. Maintain
12. Recommended Objects
13. Unsuitable Objects
14. Alternative Objects

Sections 1 to 11 are the original design template. Sections 12 to 14 extend each theme with a thin **decision interface** to the object library, so the future Space Decision Engine can reason from theme leaves without inferring object choices by hand.

## Object Linkage

- **Recommended Objects** lists `OBJECT.<ID>` items that fit this theme.
- **Unsuitable Objects** lists `OBJECT.<ID>` items that break this theme atmosphere.
- **Alternative Objects** lists non-`OBJECT` items (e.g. wooden climbing tower, pergola, sand pit) that the engine may consider when none of the five starter objects are appropriate.

Stable IDs are defined in `knowledge/objects/`. The template and identifier convention for objects is documented in `knowledge/objects/README.md`. The principles the Decision Engine will follow are documented in `knowledge/decision_rules/Space_Decision_Principles.md`.


## NATURE — Nature (自然系)

- `NATURE.FOREST` — [`Forest.md`](Forest.md)
- `NATURE.JUNGLE` — [`Jungle.md`](Jungle.md)
- `NATURE.MOUNTAIN` — [`Mountain.md`](Mountain.md)
- `NATURE.WETLAND` — [`Wetland.md`](Wetland.md)
- `NATURE.RIVER` — [`River.md`](River.md)
- `NATURE.GARDEN` — [`Garden.md`](Garden.md)

## ANIMAL — Animal (动物系)

- `ANIMAL.BEAR` — [`Bear.md`](Bear.md)
- `ANIMAL.FOX` — [`Fox.md`](Fox.md)
- `ANIMAL.RABBIT` — [`Rabbit.md`](Rabbit.md)
- `ANIMAL.WOLF` — [`Wolf.md`](Wolf.md)
- `ANIMAL.LION` — [`Lion.md`](Lion.md)
- `ANIMAL.DINOSAUR` — [`Dinosaur.md`](Dinosaur.md)
- `ANIMAL.WHALE` — [`Whale.md`](Whale.md)
- `ANIMAL.DOLPHIN` — [`Dolphin.md`](Dolphin.md)

## OCEAN — Ocean (海洋系)

- `OCEAN.CORAL` — [`Coral.md`](Coral.md)
- `OCEAN.PIRATE` — [`Pirate.md`](Pirate.md)
- `OCEAN.LIGHTHOUSE` — [`Lighthouse.md`](Lighthouse.md)
- `OCEAN.ISLAND` — [`Island.md`](Island.md)
- `OCEAN.DEEP_SEA` — [`Deep_Sea.md`](Deep_Sea.md)

## SPACE — Space (宇宙系)

- `SPACE.ROCKET` — [`Rocket.md`](Rocket.md)
- `SPACE.PLANET` — [`Planet.md`](Planet.md)
- `SPACE.GALAXY` — [`Galaxy.md`](Galaxy.md)
- `SPACE.METEOR` — [`Meteor.md`](Meteor.md)
- `SPACE.SPACE_STATION` — [`Space_Station.md`](Space_Station.md)

## CASTLE — Castle (城堡系)

- `CASTLE.CASTLE` — [`Castle.md`](Castle.md)
- `CASTLE.KNIGHT` — [`Knight.md`](Knight.md)
- `CASTLE.PRINCESS` — [`Princess.md`](Princess.md)

## TRANSPORTATION — Transportation (交通工具系)

- `TRANSPORTATION.TRAIN` — [`Train.md`](Train.md)
- `TRANSPORTATION.AIRCRAFT` — [`Aircraft.md`](Aircraft.md)
- `TRANSPORTATION.SHIP` — [`Ship.md`](Ship.md)
- `TRANSPORTATION.CAR` — [`Car.md`](Car.md)

## FANTASY — Fantasy (幻想系)

- `FANTASY.FAIRY_TALE` — [`Fairy_Tale.md`](Fairy_Tale.md)
- `FANTASY.MAGIC` — [`Magic.md`](Magic.md)
- `FANTASY.ELF` — [`Elf.md`](Elf.md)
- `FANTASY.DRAGON` — [`Dragon.md`](Dragon.md)

## SCIENCE — Science (科学系)

- `SCIENCE.LABORATORY` — [`Laboratory.md`](Laboratory.md)
- `SCIENCE.ROBOT` — [`Robot.md`](Robot.md)
- `SCIENCE.AI` — [`AI.md`](AI.md)

## TRADITIONAL_CULTURE — Traditional Culture (传统文化系)

- `TRADITIONAL_CULTURE.CHINESE_CULTURE` — [`Chinese_Culture.md`](Chinese_Culture.md)
- `TRADITIONAL_CULTURE.FOLK_STORY` — [`Folk_Story.md`](Folk_Story.md)
- `TRADITIONAL_CULTURE.FESTIVAL` — [`Festival.md`](Festival.md)

**Total entries:** 41
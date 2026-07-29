"""
Strategy Library Renderer
Reads _data.json and produces:
  - 15 individual YAML files (one per Strategy)
  - README.md (human-readable index)
  - _index.yaml (machine-readable index)
"""
import json
import pathlib
import re


GOALS_DIR = pathlib.Path(__file__).parent
DATA_FILE = GOALS_DIR / "_data.json"

PRIORITY_RE = re.compile(r"x\s*(\d+)")


def parse_priority(priority_str):
    m = PRIORITY_RE.search(priority_str)
    return int(m.group(1)) if m else 0


def _format_description(text):
    lines = [line.rstrip() for line in text.strip().splitlines()]
    if not lines:
        return 'Description: ""'
    body = "\n".join("  " + line for line in lines)
    return "Description: |\n" + body


def render_strategy(s):
    out = []
    out.append("Strategy_ID: " + s["Strategy_ID"])
    out.append("Name: " + s["Name"])
    out.append("Name_EN: " + s["Name_EN"])
    out.append(_format_description(s["Description"]))
    if s.get("Mechanism"):
        out.append(_format_description(s["Mechanism"]).replace("Description:", "Mechanism:", 1))
    for list_key in ["Addresses_Goals", "Typical_Implementations",
                     "Synergies", "Conflicts_With",
                     "Heuristics", "Domain_Affinity"]:
        items = s.get(list_key, [])
        if items:
            out.append(list_key + ":")
            for item in items:
                out.append("  - " + item)
    out.append("Priority: " + s["Priority"])
    return "\n".join(out) + "\n"


def render_readme(strategies):
    lines = []
    lines.append("# Strategy Library")
    lines.append("")
    lines.append("The Strategy Library is the **action layer** of CaseOS.")
    lines.append("")
    lines.append("It defines **HOW a Goal is achieved** -- not which equipment to install.")
    lines.append("")
    lines.append("A Goal can be addressed by multiple Strategies.")
    lines.append("A Strategy can be implemented by multiple Objects.")
    lines.append("An Object can serve multiple Strategies.")
    lines.append("")
    lines.append("This is the Goal -> Strategy -> Object decision chain.")
    lines.append("")
    lines.append("## Why Strategies (not Objects) come first")
    lines.append("")
    lines.append("- Strategies explain **intent** to clients.")
    lines.append("- Strategies are reusable across domains (a Landmark can serve a Playground, a Mall, or a Park).")
    lines.append("- Strategies make trade-offs visible (e.g., Provide Comfort vs. Interactive Experience).")
    lines.append("- Strategies bridge Goals (business intent) with Objects (physical form).")
    lines.append("")
    lines.append("## The 15 Strategies")
    lines.append("")
    lines.append("| Strategy_ID | Name | Priority | Goal it serves |")
    lines.append("| --- | --- | --- | --- |")
    for s in strategies:
        gid = s["Strategy_ID"]
        priority_count = parse_priority(s["Priority"])
        priority_stars = "\u2605" * priority_count
        primary_goal = s.get("Addresses_Goals", [""])[0] if s.get("Addresses_Goals") else ""
        lines.append("| " + gid + " | " + s["Name"] + " | " + priority_stars + " | " + primary_goal + " |")
    lines.append("")
    lines.append("## Strategy Families")
    lines.append("")
    lines.append("- **ATTRACT** (4): CREATE_LANDMARK, IMPROVE_VISIBILITY, ENABLE_PHOTO_MOMENTS, DIFFERENTIATE")
    lines.append("- **ENGAGE** (4): INTERACTIVE_EXPERIENCE, ENCOURAGE_EXPLORATION, INCREASE_STAY_TIME, BUILD_NARRATIVE")
    lines.append("- **CONNECT** (3): SUPPORT_SOCIAL_PLAY, ENABLE_PARENT_CHILD_INTERACTION, REDUCE_FRICTION")
    lines.append("- **NURTURE** (3): PROVIDE_COMFORT, CREATE_REST_POINTS, ENCOURAGE_REPEAT_VISIT")
    lines.append("- **EDUCATE** (1): PROVIDE_LEARNING_OPS")
    lines.append("")
    lines.append("## How Strategies connect to other libraries")
    lines.append("")
    lines.append("- **Strategy -> Goal**: every Strategy lists which Goals it serves (`Addresses_Goals`).")
    lines.append("- **Strategy -> Object**: every Strategy lists typical implementations from `knowledge/objects/`.")
    lines.append("- **Strategy -> Strategy**: `Synergies` and `Conflicts_With` describe how Strategies interact.")
    lines.append("- **Strategy -> Decision**: see `knowledge/reasoning/` for explanation templates.")
    lines.append("")
    lines.append("## Strategy conflict matrix")
    lines.append("")
    lines.append("Some Strategies conflict. The Decision Engine uses `Conflicts_With` to resolve:")
    lines.append("")
    lines.append("- PROVIDE_COMFORT vs. INTERACTIVE_EXPERIENCE (low-stim vs. high-stim)")
    lines.append("- PROVIDE_COMFORT vs. CREATE_LANDMARK (subtle vs. attention-grabbing)")
    lines.append("- INTERACTIVE_EXPERIENCE vs. CREATE_REST_POINTS (movement vs. stillness)")
    lines.append("- IMPROVE_VISIBILITY vs. SUBTLE_INTEGRATION (visible vs. hidden)")
    lines.append("- ENABLE_PHOTO_MOMENTS vs. SUBTLE_INTEGRATION (expressive vs. quiet)")
    lines.append("")
    lines.append("## Decision Pipeline")
    lines.append("")
    lines.append("    Client brief")
    lines.append("      |")
    lines.append("      v")
    lines.append("    1. Identify Goals (knowledge/goals/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    2. Resolve Goal conflicts")
    lines.append("      |")
    lines.append("      v")
    lines.append("    3. Select Strategies (THIS library) per Goal")
    lines.append("      |")
    lines.append("      v")
    lines.append("    4. Resolve Strategy conflicts (Conflicts_With)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    5. Map Strategies -> Object categories (knowledge/objects/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    6. Generate proposal + reasoning (knowledge/reasoning/)")
    lines.append("")
    lines.append("## Maintenance Rules")
    lines.append("")
    lines.append("1. Strategy_ID is **stable**. Never rename an existing ID; add a new one if needed.")
    lines.append("2. The 5-level priority (star count) is the only allowed priority scale.")
    lines.append("3. `Addresses_Goals` must reference existing Goal_IDs in `knowledge/goals/`.")
    lines.append("4. `Synergies` and `Conflicts_With` must reference existing Strategy_IDs.")
    lines.append("5. New Strategies should explain a Mechanism that no existing Strategy already covers.")
    lines.append("6. Every change updates `_index.yaml` (regenerated by this renderer).")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- `STRATEGY.*.yaml` -- one per Strategy.")
    lines.append("- `_index.yaml` -- machine-readable list.")
    lines.append("- `_data.json` -- source data.")
    lines.append("- `README.md` -- this file.")
    lines.append("")
    return "\n".join(lines)


def render_index(strategies):
    out = []
    out.append("Schema_Version: 1")
    out.append("Generated_At: \"2026-07-29\"")
    out.append("Strategy_Count: " + str(len(strategies)))
    out.append("Strategies:")
    for s in strategies:
        out.append("  - Strategy_ID: " + s["Strategy_ID"])
        out.append("    Name: " + s["Name"])
        out.append("    Name_EN: " + s["Name_EN"])
        out.append("    Priority: " + str(parse_priority(s["Priority"])))
        if s.get("Addresses_Goals"):
            out.append("    Addresses_Goals:")
            for g in s["Addresses_Goals"]:
                out.append("      - " + g)
        if s.get("Conflicts_With"):
            out.append("    Conflicts_With:")
            for c in s["Conflicts_With"]:
                out.append("      - " + c)
        if s.get("Synergies"):
            out.append("    Synergies:")
            for sg in s["Synergies"]:
                out.append("      - " + sg)
        out.append("    File: " + s["Strategy_ID"] + ".yaml")
    return "\n".join(out) + "\n"


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    strategies = data["strategies"]

    for s in strategies:
        path = GOALS_DIR / (s["Strategy_ID"] + ".yaml")
        path.write_text(render_strategy(s), encoding="utf-8")
        print("wrote", path.name)

    (GOALS_DIR / "README.md").write_text(render_readme(strategies), encoding="utf-8")
    print("wrote README.md")

    (GOALS_DIR / "_index.yaml").write_text(render_index(strategies), encoding="utf-8")
    print("wrote _index.yaml")


if __name__ == "__main__":
    main()
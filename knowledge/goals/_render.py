"""
Goal Library Renderer
Reads _data.json and produces:
  - 15 individual YAML files (one per Goal)
  - README.md (human-readable index)
  - _index.yaml (machine-readable index)
"""
import json
import pathlib
import re


GOALS_DIR = pathlib.Path(__file__).parent
DATA_FILE = GOALS_DIR / "_data.json"

PRIORITY_RE = re.compile(r"x\s*(\d+)")


def _format_description(text):
    """Wrap Description into literal-block YAML form (`|`)."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    if not lines:
        return 'Description: ""'
    body = "\n".join("  " + line for line in lines)
    return "Description: |\n" + body


def parse_priority(priority_str):
    """Parse 'star x N' format and return the numeric priority."""
    m = PRIORITY_RE.search(priority_str)
    return int(m.group(1)) if m else 0


def render_goal(goal):
    """Render a single Goal dict into the goal-specific YAML format."""
    out = []
    out.append("Goal_ID: " + goal["Goal_ID"])
    out.append("Name: " + goal["Name"])
    out.append("Name_EN: " + goal["Name_EN"])
    out.append(_format_description(goal["Description"]))
    for list_key in ["Success_Indicators", "Typical_Projects", "Suitable_Objects",
                     "Unsuitable_Objects", "Heuristics", "Conflicts_With",
                     "Related_Goals", "Domain_Affinity"]:
        items = goal.get(list_key, [])
        if items:
            out.append(list_key + ":")
            for item in items:
                out.append("  - " + item)
    out.append("Priority: " + goal["Priority"])
    return "\n".join(out) + "\n"


def render_readme(goals):
    """Render a human-readable README.md describing the Goal Library."""
    lines = []
    lines.append("# Goal Library")
    lines.append("")
    lines.append("The Goal Library is the most important knowledge table in CaseOS.")
    lines.append("")
    lines.append("It defines **WHY a space should be designed the way it is**.")
    lines.append("Every Space Decision in CaseOS begins by matching one or more Goals.")
    lines.append("")
    lines.append("## Why Goals First")
    lines.append("")
    lines.append("- Decisions driven by Goals are explainable to clients.")
    lines.append("- Goals connect business value with design choices.")
    lines.append("- Goals make trade-offs visible.")
    lines.append("- Goals enable cross-domain reasoning (playground <-> commercial <-> education).")
    lines.append("")
    lines.append("## The 15 Goals")
    lines.append("")
    lines.append("| Goal_ID | Name | Priority | One-line purpose |")
    lines.append("| --- | --- | --- | --- |")
    purpose_map = {
        "BUSINESS.TRAFFIC": "\u589e\u52a0\u5ba2\u6d41",
        "BUSINESS.BRAND": "\u54c1\u724c\u5efa\u8bbe",
        "BUSINESS.REVENUE": "\u8425\u6536\u589e\u957f",
        "BUSINESS.DIFFERENTIATION": "\u5dee\u5f02\u5316",
        "EDU.ENROLLMENT": "\u62db\u751f",
        "EDU.LEARNING": "\u5b66\u4e60",
        "EDU.DISCOVERY": "\u63a2\u7d22",
        "COMMUNITY.ACTIVITY": "\u793e\u533a\u6d3b\u8dc3",
        "COMMUNITY.BONDING": "\u5bb6\u5ead\u4e0e\u90bb\u91cc",
        "COMMUNITY.INCLUSION": "\u5305\u5bb9",
        "CHILD.DEVELOPMENT": "\u513f\u7ae5\u53d1\u5c55",
        "CHILD.PLAY_VALUE": "\u6e38\u620f\u4ef7\u503c",
        "PHOTO.SHARING": "\u62cd\u7167\u5206\u4eab",
        "PERSONAL.RELAXATION": "\u653e\u677e",
        "CULTURAL.HERITAGE": "\u6587\u5316\u9057\u4ea7",
    }
    for g in goals:
        gid = g["Goal_ID"]
        priority_count = parse_priority(g["Priority"])
        priority_stars = "\u2605" * priority_count
        purpose = purpose_map.get(gid, "")
        lines.append("| " + gid + " | " + g["Name"] + " | " + priority_stars + " | " + purpose + " |")
    lines.append("")
    lines.append("## Goal Groups")
    lines.append("")
    lines.append("- **BUSINESS** (4): TRAFFIC, BRAND, REVENUE, DIFFERENTIATION")
    lines.append("- **EDU** (3): ENROLLMENT, LEARNING, DISCOVERY")
    lines.append("- **COMMUNITY** (3): ACTIVITY, BONDING, INCLUSION")
    lines.append("- **CHILD** (2): DEVELOPMENT, PLAY_VALUE")
    lines.append("- **PERSONAL** (1): RELAXATION")
    lines.append("- **CULTURAL** (1): HERITAGE")
    lines.append("")
    lines.append("Plus one cross-cutting Goal: PHOTO.SHARING (no group prefix).")
    lines.append("")
    lines.append("## Controlled Object Vocabulary")
    lines.append("")
    lines.append("Every Goal's Suitable_Objects and Unsuitable_Objects use the same controlled")
    lines.append("vocabulary of object categories. This keeps Goals comparable and lets the Decision")
    lines.append("Engine translate categories into concrete objects at runtime.")
    lines.append("")
    cats = ["Landmark", "Theme Sculpture", "Public Art", "Photography Spot",
            "Theme Playground", "Interactive Installation", "Adventure Course",
            "Sports Facility", "Reading Corner", "Seating Area",
            "Performance Stage", "Amphitheater", "Nature Element",
            "Sensory Garden", "Water Feature", "Lighting Installation",
            "Wayfinding", "Shade Structure", "F&B Space", "Retail Kiosk",
            "Small Decoration", "Softscape", "Hardscape",
            "Educational Installation", "Cultural Installation"]
    for c in cats:
        lines.append("- " + c)
    lines.append("")
    lines.append("## Cross-Links")
    lines.append("")
    lines.append("- Goal <-> Object Category: via Suitable_Objects / Unsuitable_Objects.")
    lines.append("- Goal <-> Theme: via Domain_Affinity and shared Suitable_Objects with knowledge/taxonomy/theme/.")
    lines.append("- Goal <-> Decision Rule: via knowledge/decision_rules/Space_Decision_Principles.md.")
    lines.append("- Goal <-> Expert Handbook: via knowledge/expert_handbook/ (especially 02_Expert_Rules.md, 05_Negative_Rules.md).")
    lines.append("")
    lines.append("## Decision Pipeline")
    lines.append("")
    lines.append("    Client brief")
    lines.append("      |")
    lines.append("      v")
    lines.append("    1. Identify Goals (this library)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    2. Resolve Goal conflicts (Conflicts_With)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    3. Map Goals -> Suitable Object categories")
    lines.append("      |")
    lines.append("      v")
    lines.append("    4. Map categories -> concrete objects (knowledge/objects/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    5. Select Themes consistent with Goals (knowledge/taxonomy/theme/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    6. Apply Decision Principles (knowledge/decision_rules/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    7. Generate proposal")
    lines.append("")
    lines.append("## Maintenance Rules")
    lines.append("")
    lines.append("1. Goal_ID is **stable**. Never rename an existing ID; add a new one if needed.")
    lines.append("2. The 5-level priority (star count) is the only allowed priority scale.")
    lines.append("3. Object category names must stay in sync with knowledge/objects/ and knowledge/taxonomy/theme/.")
    lines.append("4. New Goals should reference existing Goals via Related_Goals or Conflicts_With.")
    lines.append("5. Every change updates _index.yaml (regenerated by this renderer).")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- BUSINESS.*.yaml, EDU.*.yaml, COMMUNITY.*.yaml, CHILD.*.yaml, PERSONAL.*.yaml, CULTURAL.*.yaml, PHOTO.*.yaml -- one per Goal.")
    lines.append("- _index.yaml -- machine-readable list (engine reads this).")
    lines.append("- _data.json -- source data (maintained by humans, consumed by the renderer).")
    lines.append("- README.md -- this file.")
    lines.append("")
    return "\n".join(lines)


def render_index(goals):
    """Render a machine-readable index for the engine."""
    out = []
    out.append("Schema_Version: 1")
    out.append("Generated_At: \"2026-07-29\"")
    out.append("Goal_Count: " + str(len(goals)))
    out.append("Goals:")
    for g in goals:
        out.append("  - Goal_ID: " + g["Goal_ID"])
        out.append("    Name: " + g["Name"])
        out.append("    Name_EN: " + g["Name_EN"])
        out.append("    Priority: " + str(parse_priority(g["Priority"])))
        if g.get("Domain_Affinity"):
            out.append("    Domain_Affinity:")
            for d in g["Domain_Affinity"]:
                out.append("      - " + d)
        if g.get("Conflicts_With"):
            out.append("    Conflicts_With:")
            for c in g["Conflicts_With"]:
                out.append("      - " + c)
        if g.get("Related_Goals"):
            out.append("    Related_Goals:")
            for r in g["Related_Goals"]:
                out.append("      - " + r)
        out.append("    File: " + g["Goal_ID"] + ".yaml")
    return "\n".join(out) + "\n"


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    goals = data["goals"]

    for g in goals:
        path = GOALS_DIR / (g["Goal_ID"] + ".yaml")
        path.write_text(render_goal(g), encoding="utf-8")
        print("wrote", path.name)

    (GOALS_DIR / "README.md").write_text(render_readme(goals), encoding="utf-8")
    print("wrote README.md")

    (GOALS_DIR / "_index.yaml").write_text(render_index(goals), encoding="utf-8")
    print("wrote _index.yaml")


if __name__ == "__main__":
    main()
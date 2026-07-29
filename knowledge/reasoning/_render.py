"""
Reasoning Library Renderer
Reads _data.json and produces:
  - 12 individual YAML files (one per Reasoning pattern)
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


def yaml_scalar(value):
    """Render a scalar safely (quote if it would be interpreted by YAML)."""
    if value is None:
        return "\"\""
    s = str(value)
    # Values starting with *, &, !, ?, :, -, <, >, {, [, %, @, `, | are special
    if s and s[0] in "*&!?-:<>{}[]%@`|" or s in ("null", "true", "false", "yes", "no", "on", "off") or any(c in s for c in [":", "#"]):
        # Use double quotes with escaping
        escaped = s.replace("\\", "\\\\").replace("\"", "\\\"")
        return "\"" + escaped + "\""
    return s


def _format_block(label, text):
    """Format a multi-line string into a YAML literal block with a custom label."""
    if not text:
        return label + ": \"\""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    body = "\n".join("  " + line for line in lines)
    return label + ": |\n" + body


def render_reasoning(r):
    out = []
    out.append("Reason_ID: " + yaml_scalar(r["Reason_ID"]))
    out.append("Name: " + yaml_scalar(r["Name"]))
    out.append("Name_EN: " + yaml_scalar(r["Name_EN"]))
    out.append(_format_block("Description", r["Description"]))
    if r.get("Trigger_When"):
        out.append("Trigger_When:")
        for t in r["Trigger_When"]:
            out.append("  - " + yaml_scalar(t))
    if r.get("Required_Factors"):
        out.append("Required_Factors:")
        for f in r["Required_Factors"]:
            out.append("  - " + yaml_scalar(f))
    if r.get("Optional_Factors"):
        out.append("Optional_Factors:")
        for f in r["Optional_Factors"]:
            out.append("  - " + yaml_scalar(f))
    out.append(_format_block("Template_Chinese", r["Template_Chinese"]))
    out.append(_format_block("Example_Output", r["Example_Output"]))
    if r.get("Uses_Goals"):
        out.append("Uses_Goals:")
        for g in r["Uses_Goals"]:
            out.append("  - " + yaml_scalar(g))
    if r.get("Uses_Strategies"):
        out.append("Uses_Strategies:")
        for s in r["Uses_Strategies"]:
            out.append("  - " + yaml_scalar(s))
    out.append("Priority: " + r["Priority"])
    return "\n".join(out) + "\n"


def render_readme(reasons):
    lines = []
    lines.append("# Reasoning Library")
    lines.append("")
    lines.append("The Reasoning Library is the **explanation layer** of CaseOS.")
    lines.append("")
    lines.append("It defines **WHY a recommendation is made** -- not the recommendation itself.")
    lines.append("")
    lines.append("In other words: CaseOS doesn't say \"we recommend a Treehouse\".")
    lines.append("CaseOS says:")
    lines.append("")
    lines.append("> Because your goal is \"increase enrollment\", children aged 3-6 prefer")
    lines.append("> role-play and are at a social-language developmental stage that needs")
    lines.append("> shared imagination. Your site has existing woodland that amplifies an")
    lines.append("> exploration experience. Budget allows the standard scope.")
    lines.append("> Therefore: **Treehouse is the highest-ROI option for your goal in your context.**")
    lines.append("")
    lines.append("These explanations are **Decision Reasons**, not Prompts. They are outputs of the AI, not inputs.")
    lines.append("")
    lines.append("## Why Reasoning Library matters")
    lines.append("")
    lines.append("- Clients trust decisions they can understand.")
    lines.append("- Reasoning makes AI decisions auditable.")
    lines.append("- Reasoning surfaces hidden assumptions.")
    lines.append("- Reasoning is what turns CaseOS from a tool into an advisor.")
    lines.append("")
    lines.append("## The 12 Reasoning Patterns")
    lines.append("")
    lines.append("| Reason_ID | Name | Priority | Purpose |")
    lines.append("| --- | --- | --- | --- |")
    purpose_map = {
        "REASON.GOAL_OBJECT_FIT": "\u5bf9\u8c61\u4e3a\u4ec0\u4e48\u9002\u5408\u8fbe\u6210\u76ee\u6807",
        "REASON.GOAL_STRATEGY_FIT": "\u7b56\u7565\u4e3a\u4ec0\u4e48\u9002\u5408\u8fbe\u6210\u76ee\u6807",
        "REASON.BUDGET_CONSTRAINT": "\u9884\u7b97\u4e0b\u4e3a\u4ec0\u4e48\u9009\u8fd9\u4e2a",
        "REASON.USER_AGE_MATCH": "\u4e3a\u4ec0\u4e48\u5339\u914d\u8be5\u5e74\u9f84\u6bb5",
        "REASON.SITE_RESOURCE_MATCH": "\u4e3a\u4ec0\u4e48\u7528\u5b83\u4f46\u4e0d\u6d6a\u8d39\u573a\u5730\u4f18\u52bf",
        "REASON.CULTURAL_FIT": "\u4e3a\u4ec0\u4e48\u4e0e\u672c\u5730\u6587\u5316\u4e0a\u4e0b\u6587\u4e00\u81f4",
        "REASON.CONFLICT_RESOLUTION": "\u591a\u4e2a\u51b2\u7a81\u4e2d\u4e3a\u4ec0\u4e48\u9009\u8fd9\u4e2a",
        "REASON.PRIORITY_TRADEOFF": "\u4e3a\u4ec0\u4e48\u987a\u5e8f\u662f\u8fd9\u4e2a",
        "REASON.ROI_CALCULATION": "\u8d44\u672c\u56de\u62a9\u4e3a\u4ec0\u4e48\u9ad8",
        "REASON.RISK_MITIGATION": "\u4e3a\u4ec0\u4e48\u80fd\u51cf\u5c11\u98ce\u9669",
        "REASON.SUCCESS_PATTERN": "\u53c2\u8003\u4e86\u54ea\u4e9b\u6210\u529f\u6848\u4f8b",
        "REASON.NEGATIVE_REASON": "\u4e3a\u4ec0\u4e48\u660e\u786e\u4e0d\u9009\u67d0\u9879",
    }
    for r in reasons:
        rid = r["Reason_ID"]
        priority_count = parse_priority(r["Priority"])
        priority_stars = "\u2605" * priority_count
        purpose = purpose_map.get(rid, "")
        lines.append("| " + rid + " | " + r["Name"] + " | " + priority_stars + " | " + purpose + " |")
    lines.append("")
    lines.append("## Pattern Families")
    lines.append("")
    lines.append("- **JUSTIFY (3)**: GOAL_OBJECT_FIT, GOAL_STRATEGY_FIT, CULTURAL_FIT")
    lines.append("- **CONSTRAIN (3)**: BUDGET_CONSTRAINT, USER_AGE_MATCH, SITE_RESOURCE_MATCH")
    lines.append("- **RESOLVE (2)**: CONFLICT_RESOLUTION, PRIORITY_TRADEOFF")
    lines.append("- **EVALUATE (2)**: ROI_CALCULATION, RISK_MITIGATION")
    lines.append("- **CITE (1)**: SUCCESS_PATTERN")
    lines.append("- **EXCLUDE (1)**: NEGATIVE_REASON")
    lines.append("")
    lines.append("## How Reasoning is generated")
    lines.append("")
    lines.append("1. The Decision Engine identifies candidate Strategies and Objects.")
    lines.append("2. For each candidate, it selects the relevant Reasoning Patterns.")
    lines.append("3. It fills the templates with concrete factors (goal, object, benefit, etc.).")
    lines.append("4. Patterns are concatenated into a coherent explanation paragraph.")
    lines.append("")
    lines.append("## Template variable syntax")
    lines.append("")
    lines.append("Templates use `{variable}` placeholders. The engine substitutes concrete values:")
    lines.append("")
    lines.append("- `{goal}` -- human-readable goal name (e.g., \"increase enrollment\")")
    lines.append("- `{strategy}` -- strategy name (e.g., \"interactive experience\")")
    lines.append("- `{object}` -- concrete object (e.g., \"interactive wall\")")
    lines.append("- `{benefit}` -- how the object contributes to the goal")
    lines.append("- `{site_feature}` -- site-specific resource (e.g., \"existing woodland\")")
    lines.append("- `{age_group}` -- target children age range")
    lines.append("- `{budget}` -- budget tier")
    lines.append("- `{option}` -- the specific choice being explained")
    lines.append("- `{reason}` -- the underlying reason")
    lines.append("")
    lines.append("## Pipeline position")
    lines.append("")
    lines.append("    Goals (knowledge/goals/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    Strategies (knowledge/strategies/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    Objects (knowledge/objects/)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    Reasoning (THIS library)")
    lines.append("      |")
    lines.append("      v")
    lines.append("    Proposal (output to client)")
    lines.append("")
    lines.append("Reasoning is the bridge between the internal decision chain and the client's understanding.")
    lines.append("")
    lines.append("## Maintenance Rules")
    lines.append("")
    lines.append("1. Reason_ID is **stable**. Never rename an existing ID; add a new one if needed.")
    lines.append("2. Each Reason must have at least one Required_Factor and a Template_Chinese.")
    lines.append("3. `Uses_Goals` and `Uses_Strategies` reference existing IDs in those libraries.")
    lines.append("4. Templates use `{variable}` placeholders, never hardcoded values.")
    lines.append("5. Example_Output is mandatory; it anchors the abstract template.")
    lines.append("6. Every change updates `_index.yaml` (regenerated by this renderer).")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- `REASON.*.yaml` -- one per Reasoning pattern.")
    lines.append("- `_index.yaml` -- machine-readable list.")
    lines.append("- `_data.json` -- source data.")
    lines.append("- `README.md` -- this file.")
    lines.append("")
    return "\n".join(lines)


def render_index(reasons):
    out = []
    out.append("Schema_Version: 1")
    out.append("Generated_At: \"2026-07-29\"")
    out.append("Reason_Count: " + str(len(reasons)))
    out.append("Reasons:")
    for r in reasons:
        out.append("  - Reason_ID: " + r["Reason_ID"])
        out.append("    Name: " + r["Name"])
        out.append("    Name_EN: " + r["Name_EN"])
        out.append("    Priority: " + str(parse_priority(r["Priority"])))
        if r.get("Required_Factors"):
            out.append("    Required_Factors:")
            for f in r["Required_Factors"]:
                out.append("      - " + f)
        if r.get("Uses_Goals"):
            out.append("    Uses_Goals:")
            for g in r["Uses_Goals"]:
                out.append("      - " + g)
        if r.get("Uses_Strategies"):
            out.append("    Uses_Strategies:")
            for s in r["Uses_Strategies"]:
                out.append("      - " + s)
        out.append("    File: " + r["Reason_ID"] + ".yaml")
    return "\n".join(out) + "\n"


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    reasons = data["reasoning_patterns"]

    for r in reasons:
        path = GOALS_DIR / (r["Reason_ID"] + ".yaml")
        path.write_text(render_reasoning(r), encoding="utf-8")
        print("wrote", path.name)

    (GOALS_DIR / "README.md").write_text(render_readme(reasons), encoding="utf-8")
    print("wrote README.md")

    (GOALS_DIR / "_index.yaml").write_text(render_index(reasons), encoding="utf-8")
    print("wrote _index.yaml")


if __name__ == "__main__":
    main()
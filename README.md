# claude-skills

### Agent skills for Claude that actually do things.

[![Skills: 3](https://img.shields.io/badge/skills-3-blue)](skills/)
[![agentskills.io](https://img.shields.io/badge/spec-agentskills.io-informational)](https://agentskills.io/specification)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-blueviolet?logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)

Custom skills for Claude.ai and Claude Code. Each skill follows the [agentskills.io specification](https://agentskills.io/specification) — drop a folder in and Claude gains a new capability.

| Skill | What it does | Triggers |
|-------|-------------|----------|
| [`mckinsey-deck-check`](skills/mckinsey-deck-check/SKILL.md) | Audits a PPTX against McKinsey's Hypothesis-Driven Framework across 11 dimensions, then fixes issues in-place | "check my deck", "is this McKinsey-ready" |
| [`rimworld-log-check`](skills/rimworld-log-check/SKILL.md) | Diagnoses mod conflicts, crashes, and redundancies from HugsLib logs — names the responsible mods | "check my log", sharing a HugsLib Gist URL |
| [`data-dictionary`](skills/data-dictionary/SKILL.md) | Drafts and iterates a per-field data dictionary from any tabular file through structured review passes | "build a data dictionary", "document my columns" |

---

## Skills

### mckinsey-deck-check

Audits a PowerPoint presentation against McKinsey's Hypothesis-Driven Framework and Pyramid Principle across 11 dimensions:

1. Fact Foundation
2. Initial Hypothesis
3. Issue Tree Integrity (MECE)
4. Big Picture Synthesis
5. SPQA Stage-Setting
6. Pyramid Principle
7. Impact Clarity
8. Number Consistency
9. Data–Narrative Alignment
10. Language & Formatting Polish
11. Brevity & Simplicity

Produces a ranked issue plan (Critical / Important / Polish), waits for approval, then executes fixes directly in the PPTX.

### rimworld-log-check

Analyzes RimWorld HugsLib `output_log.txt` / `player.log` files to diagnose mod conflicts, crashes, exceptions, and warnings. Names the responsible mods wherever identifiable.

Performs the same core analysis as [Orion's rw-log-check tool](https://orionFive.github.io/rw-log-check/), and goes further with:

- Root-cause explanations tied to specific mods (not just error messages)
- **Redundancy detection** — identifies pairs of mods doing the same thing via three signal sources:
  - NQoL developer-confirmed overlap notices
  - Mod-authored COMPAT warnings (e.g. Job In Bar)
  - A curated static Known Redundancy Database (15+ common pairs)
- Priority-ordered fix list, grouped by impact

| Section | Content |
|---------|---------|
| 🔴 Exceptions | Code-halting errors with stack trace attribution |
| 🟠 Startup errors | Broken def references, XML issues, missing types |
| 🟡 Runtime warnings | NQoL patch failures, Harmony conflicts, version changes |
| 🔁 Redundant mods | Overlapping mod pairs with recommendations *(omitted if none)* |
| 📋 Priority actions | Numbered, specific, grouped by culprit mod |

Supports RimWorld 1.4, 1.5, and 1.6 log formats. Accepts HugsLib Gist URLs, Pastebin links, or direct paste.

### data-dictionary

Drafts and iterates a data dictionary from a raw dataset (CSV, Excel, or any tabular file). Produces a per-field reference covering name, label, type, values, source, notes, and transformations — then iterates with the user through structured review passes until every field is confirmed (not inferred).

Standard dictionary columns:

| Column | Purpose |
|--------|---------|
| `field_name` | Exact name as it appears in the data |
| `label` | Human-readable description — never the field name verbatim |
| `type` | `text`, `integer`, `decimal`, `date`, `boolean`, `categorical`, `identifier`, `json`/`array` |
| `values` | Enumerated categorical values, pulled from actual data (not documentation) |
| `source` | System or form the field comes from |
| `notes` | Nulls, mixed types, business rules, edge cases — never blank |
| `transformations` | Formula for derived fields only |

Four-phase workflow: assess inputs → draft v1 → iterate with review gates → final review with inferred-field validation targets.

---

## Install

Download the `.skill` file from [Releases](../../releases) or install by uploading the skill folder via **Claude.ai → Customize → Skills**.

To install from source:

```bash
git clone https://github.com/inire/claude-skills.git
# Point your Claude client at any skill directory, e.g. skills/rimworld-log-check/
```

---

## Built with Claude

These skills were built collaboratively with [Claude](https://claude.ai) (Anthropic). If you're curious what agent skill development looks like in practice, this is a reasonable example.

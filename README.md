# claude-skills

### Agent skills for Claude that actually do things.

[![Skills: 6](https://img.shields.io/badge/skills-6-blue)](skills/)
[![agentskills.io](https://img.shields.io/badge/spec-agentskills.io-informational)](https://agentskills.io/specification)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-blueviolet?logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)

Custom skills for Claude.ai and Claude Code. Each skill follows the [agentskills.io specification](https://agentskills.io/specification) — drop a folder in and Claude gains a new capability.

| Skill | What it does | Triggers |
|-------|-------------|----------|
| [`mckinsey-deck-check`](skills/mckinsey-deck-check/SKILL.md) | Audits a PPTX against McKinsey's Hypothesis-Driven Framework across 11 dimensions, then fixes issues in-place | "check my deck", "is this McKinsey-ready" |
| [`rimworld-log-check`](skills/rimworld-log-check/SKILL.md) | Diagnoses mod conflicts, crashes, and redundancies from HugsLib logs — names the responsible mods | "check my log", sharing a HugsLib Gist URL |
| [`data-dictionary`](skills/data-dictionary/SKILL.md) | Drafts and iterates a per-field data dictionary from any tabular file through structured review passes | "build a data dictionary", "document my columns" |
| [`continuation-prompt`](skills/continuation-prompt/SKILL.md) | Generates a structured handoff doc for the next Claude Code session at milestone close — TL;DR, state, recap, next-scope, open questions, references | "make a continuation prompt", "build a handoff doc", "save context for next session" |
| [`project-memory-update`](skills/project-memory-update/SKILL.md) | Reconciles a project's auto-memory file at milestone close — surgical edits per section, doesn't lose accumulated history | "update project memory", "reflect this session in memory", "sync project memory" |
| [`dictionary-pipeline`](skills/dictionary-pipeline/SKILL.md) | LLM-side companion for the [dictionary-pipeline](https://github.com/inire/dictionary-pipeline) tool — drives the four-pass workflow (pre-intake cleanup → dictionary draft → run → optional post-pipeline derivations) on any messy tabular file | "schema-validate this", "run the dictionary-pipeline", "validate and produce a 3-tab workbook" |

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

### continuation-prompt

Generates a structured handoff document for the next Claude Code session at the end of a milestone — so a fresh session can pick up immediately without re-reading the whole repo. Designed for multi-version software releases where each continuation prompt becomes the lead-in to the next session.

Saves a markdown file to the project's `docs/` folder structured in 14 sections covering: TL;DR with the next session's first-move A/B/C decision, current branch state, just-shipped recap, next-version scope, architectural new ground, future-versions roadmap, standards to carry forward, open questions, key references, resolved historical issues, what NOT to do, and CLAUDE.md hooks.

Different from a generic README (which describes the project) and different from the auto-memory system (which saves incremental facts). This is a milestone-bookended handoff with a specific shape — written by the session that has full context, read by the session that has none.

### project-memory-update

Reconciles a project's auto-memory file (`~/.claude/projects/<cwd>/memory/project_<name>.md`) at the end of a milestone so it accurately reflects current shipped state. Surgically updates the description frontmatter, current-state section (latest SHA, tag, what shipped), release plan progression, key docs list, architectural highlights, and important reminders — without losing existing content.

Per-section update strategy:

| Section | Strategy |
|---------|----------|
| Frontmatter `description` | Replace with new SHA + tag + 1-line summary |
| Key docs | Append new entries; demote prior "current handoff" to historical |
| Current state | Replace prior version's recap with the new one |
| Architectural highlights | Append new patterns; existing entries stay intact |
| Release plan | Mark just-shipped version as done (e.g., `⏳` → `✅`); add new future versions if scope shifted |
| Important reminders | Append new lessons (workspace gotchas, lint issues, spec errors caught) |

Distinguished from the auto-memory system (incremental fact-saves as work happens) and from `anthropic-skills:consolidate-memory` (cross-tree prune/merge). This skill scopes to one project's memory file at milestone close. Uses `Edit` (never `Write`) so accumulated history isn't lost.

### dictionary-pipeline

LLM-side companion for the [`dictionary-pipeline`](https://github.com/inire/dictionary-pipeline) tool — a pandas-first data-prep pipeline that turns a messy CSV/Excel into a validated 3-tab Excel deliverable (cleaned data + data dictionary + automated-changes log). Generic across any tabular domain: consumer purchases, financial exports, surveys, inventory, CRM, healthcare records, IoT telemetry. The data dictionary is a YAML contract that drives schema enforcement, cleaning, derivation, and the dictionary tab in the deliverable.

The pipeline itself runs as deterministic Python (Stages 0, 1, 4, 5, 7, 8, 9). This skill drives the four passes that *aren't* deterministic:

| Pass | Pipeline mapping | What this skill does |
|------|------------------|----------------------|
| **1 — Pre-intake cleanup** | Pre-Stage 0 | Closes small gaps in the pipeline's `scrub.py` — currency-string sentinels (`' $- '`, `$0`, `-`), column-name whitespace, empty `Unnamed:` columns. Backed by a TDD-tested `prestage_helper.py`. Skip entirely if the export is already clean. |
| **2 — Dictionary drafting** | Stages 2 + 3 | Drafts `dictionary.yaml` from the profile output, with a 13-question domain-agnostic checklist for ambiguous semantics (presence flags, scoring rubrics, currency periods, sentinel dates, parallel-column canonicality). Highest-leverage pause point in the workflow. |
| **3 — Run + interpret** | Stages 4–9 | Wraps install / run / per-stage re-run with a post-run review checklist (schema revalidation, drift columns, transformation log, deliverable open) and a common-failure → fix table mapped to the most frequent `SchemaError` patterns |
| **4 — Optional post-pipeline derivations** | Post-Stage 9 (custom) | Eight generic derivation patterns (presence flag, sentinel coalesce, ordinal map, days-since, picklist normalize, canonical domain, set-membership classify, composite score) for when YAML `derived_fields:` isn't expressive enough. Includes a transparent weighted-sum scoring framework and a Spearman/Kendall protocol for validating weights against any existing benchmark. |

Distinguished from `data-dictionary` (which produces a Markdown/Excel dictionary deliverable, not a pandera contract). When the user wants only a dictionary, `data-dictionary` is the right skill — this one fires when they want the dictionary plus the validated 3-tab workbook plus optional derived columns. The two skills compose: `data-dictionary` governs *how* to think about each field; this skill governs *what* to emit so pandera can consume it.

The skill also surfaces a set of cross-stream lessons (real data uncovers real bugs / don't bend the contract grammar — use Pass 4 / honest gaps beat phantom fixes / cross-dataset rollups need a separate taxonomy map / Excel header rows aren't auto-detected / workdir lives outside the repo) so future Claude sessions don't re-derive them.

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

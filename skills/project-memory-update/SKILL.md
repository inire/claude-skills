---
name: project-memory-update
description: >
  Reconciles a project's auto-memory file at the end of a milestone so it
  accurately reflects current shipped state. Updates the description frontmatter,
  current-state section (latest SHA, tag, what shipped), release plan progression,
  key docs list, architectural highlights, and important reminders — without
  losing existing content. Use this skill when the user says "update project
  memory", "reflect this session in memory", "save what we shipped to memory",
  "sync project memory", or has just shipped a release/milestone and wants the
  project's memory file to mirror current reality. Different from the auto-memory
  system: that handles incremental fact-saves as work happens; this handles
  structured reconciliation at major milestones. Especially valuable for
  multi-version projects where the memory file accumulates state over many
  sessions and the structure needs reconciling. Trigger on "project memory",
  "update memory", "reflect in memory", "sync memory", or after the user confirms
  a release/tag/merge has shipped.
---

# Project Memory Update

Reconcile a project's `project_<name>.md` memory file with current shipped state. Don't replace the file — surgically update specific sections so the file mirrors reality at the end of a milestone.

## Why this skill exists

The auto-memory system in CLAUDE.md handles "save this fact" as work happens. That's incremental and unstructured. After many sessions, the project memory file accumulates facts but its narrative structure (current state, release plan, what just shipped) drifts from reality.

This skill is the reconciliation pass. At a milestone bookend, surgically update the file's structure so it accurately reflects what's now true. The auto-memory system writes facts; this skill maintains the file as a coherent snapshot.

## When to use this skill

- A release just shipped (tag pushed, branch merged, deploy complete)
- A major architectural milestone landed (new pattern proven in prod, etc.)
- The user explicitly asks to "update project memory" or similar
- The auto-memory system has been incrementally adding facts but the file's structure hasn't been reconciled into a clean snapshot

Skip this skill if:
- No project memory file exists yet (write a new memory file via auto-memory instead)
- The session was orthogonal (no shipped work) — auto-memory's incremental saves are sufficient
- The "shipped state" is uncertain (don't reflect half-broken state into memory)

## Where the file lives

Standard location, per the auto-memory system in CLAUDE.md:

```
~/.claude/projects/<colon-encoded-cwd>/memory/project_<short-name>.md
```

Where `<colon-encoded-cwd>` is the current working directory with `:` and `\` replaced (e.g., `D:\AI\Claude` → `D--AI-Claude`).

If the file isn't there, ask the user — different projects might use different memory layouts.

## Sections this skill reconciles

The standard project memory structure has these sections. Your update should preserve the structure (work with what's there if it differs slightly).

| Section | Update strategy |
|---|---|
| **Frontmatter `description`** | Replace with new SHA + tag + version + 1-line summary of what just shipped |
| **What it is** | Rarely changes — leave alone unless project scope shifted |
| **Paths + tech** | Update only when paths change or new tooling lands |
| **Key docs** | **Append** new docs from the latest milestone (design specs, plans, phase results, continuation prompts). Mark superseded "current handoff" entries as historical, NOT removed. |
| **Current state** | Replace the previous milestone's recap with the new one. This is the biggest single edit. Include: SHA + tag + push status, acceptance test results, what just shipped (bullets), cumulative state count |
| **Architectural highlights** | **Append** new patterns from the latest milestone, leave old ones intact |
| **Release plan** | Update the just-shipped version to ✅, adjust future versions if scope shifted |
| **Important reminders for future sessions** | **Append** new lessons from this milestone (spec errors caught, workspace gotchas, lint issues, etc.) |

## Process

### 1. Read current project memory in full

Read the existing file. Identify the current section structure (it may differ slightly from the standard above). Don't restructure — work with what's there.

### 2. Identify what's changed this session

```bash
git log --oneline <last-tag-or-prior-state>..HEAD
git tag -l --sort=-v:refname | head -3
ls docs/ | grep -iE "<latest-version>" | head
```

- What commits landed since the last release?
- What tags were created?
- What new docs (design specs, plans, phase results, continuation prompts) shipped?
- What does the memory file currently claim vs. what's now true?

### 3. Surgically update each section

Use `Edit` (NOT `Write`) — the file accumulates value over time and full rewrites lose history.

For each section that needs updating:

- **Frontmatter description**: replace the whole line with new SHA + tag + version
- **Key docs**: append new entries, change the prior "CURRENT handoff" marker to "historical"
- **Current state**: replace the prior version's recap block. Include shipped items as bullets, acceptance summary, cumulative state count
- **Architectural highlights**: append new patterns, leave existing bullets intact
- **Release plan**: change the just-shipped version's marker from ⏳ to ✅, add scope notes
- **Important reminders**: append new lessons from this milestone

Don't restructure or rewrite sections that haven't changed.

### 4. Verify

Read the file back. Check:

- Does the description frontmatter match the new state (correct SHA, tag, version)?
- Does the release plan show the just-shipped version as ✅?
- Does "Important reminders" include any new gotchas surfaced this milestone?
- Are there any orphaned references to the old version's "current handoff" doc that should now be "historical"?
- Does the Key docs list include the new continuation prompt (if one was just generated)?

### 5. Surface to user

Tell the user what changed at section level — don't paste the full file, just the deltas. Example:

> Updated `project_<name>.md`:
> - Description frontmatter → new SHA + v0.5
> - Key docs: appended 5 v0.5 docs, marked v0.4 continuation prompt as historical
> - Current state: replaced v0.4 recap with v0.5 recap, cumulative count 17→19
> - Release plan: v0.5 marked ✅, v0.6 added with scope notes
> - Important reminders: added 2 new entries (workspace CRLF gotcha, decompile namespace layout)

## Style notes

- **Don't lose history.** Old version recaps in the Release plan stay (✅ markers + 1-line scope). The "Architectural highlights" list grows monotonically. The "Important reminders" list grows monotonically.
- **Trim only the "current" recap.** "Current state" is the one section where the new version's recap REPLACES the old one (since the old facts are now in past tense — release plan ✅ and Architectural highlights handle the history).
- **Append, don't restate.** When adding to a list (Key docs, Architectural highlights, Important reminders), don't rewrite the existing entries to "include" the new one. Just append a new bullet.
- **Match user voice.** If the existing file is terse, stay terse. If it's discursive, stay discursive. Don't impose a style template.
- **Don't auto-promote between memory types.** If a fact belongs in `feedback_*.md` or `reference_*.md` rather than `project_*.md`, save it there separately — don't cram everything into the project memory file.

## Anti-patterns

- **Don't `Write` the file.** Always `Edit`. The file accumulates value over many sessions; a full rewrite loses unstated context.
- **Don't reconcile sections that didn't change.** If "What it is" hasn't changed, leave it alone. Editing it without reason produces git noise and obscures what actually shifted.
- **Don't promote stale auto-memory entries.** This skill doesn't merge incremental auto-memory saves into the project memory — those are separate files with their own role. Use `anthropic-skills:consolidate-memory` for that.
- **Don't reflect uncertain state.** Half-shipped work, broken builds, unmerged branches — don't write these as "current state" facts. Memory should reflect facts, not in-progress state.

## Relationship to other memory skills

- **Auto-memory system** (CLAUDE.md "auto memory" section): writes incremental facts as work happens. Different files, different cadence.
- **`anthropic-skills:consolidate-memory`**: prunes/merges duplicates across the entire memory tree. Different scope.
- **This skill**: reconciles ONE project's memory file at a milestone. Surgical, structured.

These three coexist — they don't compete.

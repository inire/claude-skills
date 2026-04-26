---
name: continuation-prompt
description: >
  Generates a structured handoff document for the NEXT Claude Code session at
  the end of a milestone — captures git state, what just shipped, next-version
  scope, open questions, key references, and what NOT to do, so a fresh session
  can pick up immediately without re-reading the whole repo. Use this skill
  whenever the user says "make a continuation prompt", "build a handoff doc",
  "save context for next session", "create a session handoff", "wrap up for next
  time", or has just shipped a release/milestone and explicitly wants the next
  session prepped. Especially valuable for multi-version software releases where
  each continuation prompt becomes the lead-in to the next session and the prompt
  itself is the artifact a fresh Claude reads first. Trigger on "continuation
  prompt", "handoff doc", "next session", "session prep", or after the user
  confirms a release/tag/merge has shipped.
---

# Continuation Prompt

Generate a structured "next session" handoff document so a fresh Claude Code session can pick up the work immediately, without re-reading commit history or guessing at project state.

## Why this skill exists

Long, productive sessions accumulate context that the next session would have to reconstruct from scratch. A continuation prompt is a frozen snapshot of "where things stand and what's next" — written by the session that has full context, read by the session that has none. Done right, the next session reads ONE doc and is up to speed.

This isn't auto-memory (which saves incremental facts) and it isn't a generic README (which describes what the project is). It's a milestone-bookended handoff with a specific shape: TL;DR → state → recap → next-scope → open questions → references.

## When to use this skill

- The user has just shipped a milestone (release tag pushed, branch merged, deploy complete) and wants to set up the next session
- The user explicitly asks to "make a continuation prompt", "build a handoff doc", "save context for next session"
- A long working session is wrapping up and the next session would benefit from a curated context dump

Skip this skill if:
- The next session is for a totally different project (no continuity to capture)
- The current state is mid-broken-build / mid-debug (the prompt would mislead)
- The user wants a one-liner reminder, not a structured doc

## Output structure

The continuation prompt is a markdown file saved to the project's `docs/` folder (or wherever existing handoff docs live; check first). It follows this section structure:

1. **Title** — `# Continuation Prompt — vX SHIPPED, vY [next thing] Next` (or non-version equivalent: "Backend migration complete, frontend integration next")
2. **Lead-in instructions** — One paragraph telling the next Claude: "Read this first. It tells you exactly where the project landed, what's open, what to ask the user, and where to find context. You can act on the contents of this doc without reading any other file first."
3. **TL;DR (read this, then ask the user)** — 4 bullets: what just shipped (1 line, with SHA), current branch state, next milestone's scope, the FIRST MOVE (a/b/c options the next session should ask the user)
4. **Where things stand** — code block showing master SHA, tags, GitHub URL, any junctions/symlinks/external paths that affect launch behavior
5. **What [last version] ships (recap, for context only)** — bullets on items shipped, architecture that landed, cumulative state count
6. **[Next version] scope (what's next)** — table or bullets of items + types + what they suppress/add + new methodology under test
7. **Architectural new ground** — bullets on patch shapes / patterns / mechanics that don't exist in the codebase yet, each with a 1-line "Phase 0 verification target" framing
8. **[Future versions] roadmap (situational awareness, NOT current scope)** — bullets on what's after the next milestone
9. **Standards & patterns (carry forward to every release)** — bullets on conventions, idioms, gotchas. Include workspace-specific issues that bit the prior session.
10. **Open questions / known unknowns** — numbered list, action-driving, to be answered during brainstorming. Each item should clearly state what decision is open.
11. **Key references (in priority order)** — numbered list of files/dirs with one-line "what's in it" notes. Include both repo-internal (specs, plans, prior phase docs) and external (decompile, vendor docs, etc.).
12. **Resolved historical issues (situational awareness)** — bullets on bugs/spec errors caught and fixed in past sessions, so the next session doesn't re-investigate them. Include the WHY (what made the fix non-obvious).
13. **What NOT to do** — bullets on locked decisions, push-protect rules, anti-pattern reminders. Failure modes that cost real time belong here.
14. **Standards from CLAUDE.md / global memory worth re-checking** — pointers to user-level memory that influences this project (work style preferences, validated process feedback)

Sections 8–14 are situational. If a project doesn't have future versions or doesn't have a CLAUDE.md, drop those sections — but lean toward including them with brief content rather than omitting.

## Process

### 1. Detect project context

Auto-detect from the current working directory:

```bash
git log --oneline -10
git status --short
git tag -l --sort=-v:refname | head -5
git remote -v
ls docs/ | grep -iE "(continuation|handoff|design|plan|phase)" | head -10
```

Also check:
- `CLAUDE.md` in repo root for project-specific guidance
- `~/.claude/projects/<colon-encoded-cwd>/memory/project_*.md` for the project's auto-memory file
- The most recent existing handoff doc (if any) — read at least one prior continuation prompt to match style and section choices

If any of these are missing, ask the user before guessing.

### 2. Confirm the milestone framing

The continuation prompt is named for the version *just shipped* + the version *next in line*. Don't guess the next version — ask if the user hasn't articulated it. The next-version scope section drives the entire document.

Examples of milestone framings:
- `v0.4.0 SHIPPED, v0.5 T3 Archotech Buildings Next`
- `Backend migration complete, frontend integration next`
- `MVP shipped, beta scope next`

### 3. Compose the TL;DR's "first move" decision

The next session shouldn't dive into work — it should pause and ask the user a structured question. Always offer at least three options:

- **(a) brainstorm the next milestone's scope** via the brainstorming skill if available — recommended when the next milestone has open architectural questions
- **(b) jump to writing an implementation plan** if scope is clear and the user has decided
- **(c) do something orthogonal** — release notes, tech debt, infra cleanup, etc.

This A/B/C pattern keeps the next session honest about scope before committing to work.

### 4. Write the doc

Save to `docs/<YYYY-MM-DD>-continuation-prompt-<next-version>.md` (matching existing naming convention in the project). If the project uses a different docs location, follow that.

Match the project's existing prose style (terse vs. discursive) — read at least one prior continuation prompt as a style reference if any exists.

### 5. Commit + surface

Commit with: `docs: continuation prompt for <next-version> (post-<last-version> handoff)`.

If the user has explicitly authorized push, push the commit. Otherwise wait for confirmation — pushing is shared state.

Tell the user where the file lives and how to use it next session: "Tell the next Claude: *Read docs/<filename> and let's continue.*"

## Style notes

- **Section sizing**: TL;DR is 4 bullets, never more. "Where things stand" is a compact code block. Body sections favor bullets over prose paragraphs.
- **Honesty about uncertainty**: The "Open questions" section names what's NOT decided. Don't pretend everything's locked.
- **Reference paths**: Use absolute paths for filesystem references the next session will need to grep (decompile dirs, vendor docs, system Steam folders). Use repo-relative paths for files inside the working directory.
- **"What NOT to do" is load-bearing**: Locked decisions, push-protect rules, anti-pattern reminders, lint gotchas that cost real time. Don't underweight this section.
- **Resolved historical issues capture the WHY**: "Bug X was actually caused by Y, fix is Z" — future sessions skip re-investigating dead ends. Include enough context that the next session understands without reading commit messages.
- **Mirror project voice**: If a prior continuation prompt exists, read it. Match its structure, tone, level of formality, use of code blocks vs. prose.

## Anti-patterns

- **Don't restate the README.** This is a session handoff, not a project description. Skip the "what is this project" framing — the next session can read CLAUDE.md or the README for that.
- **Don't enumerate every commit.** The recap section summarizes what *shipped*, not the implementation history. Save granular detail for git log.
- **Don't bury the next move.** TL;DR's last bullet must be the A/B/C question. Anything else above the fold dilutes it.
- **Don't make the next session re-derive context.** Inline the SHAs, tags, paths, decisions. Saving 50 words by linking to a doc the next session has to re-read is a false economy.

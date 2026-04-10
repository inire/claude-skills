# Git hooks

Repo-local hooks that ship with the repo (rather than living in `.git/hooks/` where they'd be invisible to other clones).

## Install

Run once per clone:

```bash
git config core.hooksPath .githooks
```

That's it. Git 2.9+ will run hooks from this directory instead of `.git/hooks/`.

To uninstall:

```bash
git config --unset core.hooksPath
```

## What's here

### `pre-commit`

Blocks commits that change `skills/*/SKILL.md` without also updating the root `README.md`. The root README is the public index for every skill in the repo, and it drifts silently if SKILL.md changes aren't mirrored there.

**Bypass** (for typo-only changes, whitespace, internal comments — anything that doesn't affect skill behavior or description):

```bash
git commit --no-verify
```

Use the bypass sparingly. The whole point of the hook is to make drift expensive.

#### Optional: `skills-ref` spec validation

If [`skills-ref`](https://github.com/agentskills/agentskills) is installed, the hook also validates every changed `SKILL.md` against the agentskills.io specification (frontmatter schema, name/directory match, description length, etc.) and blocks the commit on any violation.

Install with pipx:

```bash
pipx install "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
```

Or with uv:

```bash
uv tool install "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
```

If `skills-ref` is not on `PATH`, the hook prints a warning and lets the commit through — so README-only changes still work on machines without the tool. Install it locally if you want the safety net, or rely on CI / another contributor to catch spec drift.

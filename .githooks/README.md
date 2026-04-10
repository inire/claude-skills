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

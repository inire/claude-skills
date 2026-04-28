# dictionary-pipeline skill

LLM-side companion for the [`dictionary-pipeline`](https://github.com/inire/dictionary-pipeline) tool. Drives the four passes of the workflow that aren't deterministic Python — pre-intake cleanup, dictionary drafting, run + interpret, optional post-pipeline derivations.

## When this skill fires

- "schema-validate this CSV / XLSX"
- "run the dictionary-pipeline on this"
- "validate and produce a 3-tab workbook"
- "build a documented + validated workbook"
- "produce a Phase 3 workbook with derived columns"

See [`SKILL.md`](SKILL.md) for the full trigger description and the seven-prompt manual checklist for verifying trigger correctness.

## When it stays silent

- "build me a data dictionary" — use the [`data-dictionary`](../data-dictionary/SKILL.md) skill instead. That one produces a Markdown/Excel dictionary deliverable; this one produces the dictionary plus a validated 3-tab workbook plus optional derived columns.
- "score these accounts" / "rank this list" with already-clean data — answer inline with pandas. This skill is not a generic scorer; it includes scoring as Pass 4 only when validation is also wanted.
- "what does this file look like" — exploratory profiling. Run `dictionary-pipeline intake + profile` and stop, no need to invoke the full skill.

## Relationship to other skills

| Skill | What it does | Overlap with this skill |
|-------|--------------|-------------------------|
| [`data-dictionary`](../data-dictionary/SKILL.md) | Drafts a per-field data dictionary as a Markdown/Excel deliverable | Pass 2 of this skill is the data-dictionary protocol applied to YAML output. The two skills *compose*: data-dictionary teaches *how* to think about each field; this skill teaches *what* to emit so pandera can consume it. |

## Asset inventory

| File | Purpose |
|------|---------|
| `SKILL.md` | The skill body — frontmatter description, four-pass workflow, Quick Start prompt, common pitfalls, manual trigger checklist |
| `assets/prestage_helper.py` | Pass-1 helper for messy real-world exports. Strips column-name whitespace, drops empty `Unnamed:` columns, normalizes currency-string sentinels, and globally normalizes whitespace-only / leading-trailing whitespace cells. CLI + library. 10 tests passing. |
| `assets/dictionary_template.yaml` | Annotated YAML template covering every type tag and optional field. Generic transaction-line-items shape. |
| `assets/field_types_reference.md` | Cheat sheet for `type` / `dtype` choices, including capitalized vs lowercase nullable extension dtypes, plus a "common gotchas" section. |
| `assets/phase3_patterns.py` | Pass-4 derivation pattern library: `flag_from_presence`, `coalesce_with_sentinel`, `ordinal_map`, `days_since`, `normalize_picklist`, `canonical_domain`, `classify_set_membership`, `composite_score`. 20 tests passing. |
| `assets/example_dataset.csv` | Synthetic transaction dataset (30 rows, 13 cols) deliberately messy — exercises every field type, currency sentinels, picklist hygiene, sentinel dates, PII. |
| `assets/example_dictionary.yaml` | Dictionary contract for the synthetic dataset; demonstrates every type tag and a derived field. Used in Phase 7.2 end-to-end verification. |
| `tests/test_prestage_helper.py` | 10 tests on `prestage_helper`. |
| `tests/test_phase3_patterns.py` | 20 tests on `phase3_patterns`. |

## Provenance

Built 2026-04-28 from a multi-session effort. Pre-conditions:

- The dictionary-pipeline repo's [PR #2](https://github.com/inire/dictionary-pipeline/pull/2) (5-fix bundle: nullable extension dtypes, test gating, fuzzy near-dupe ~30× speedup, profiling HTML report) merged into master at commit `c4fffac8`.
- The pipeline repo's `docs/workflow.md` and `project_files/new_dataset_prompt.md` exist and are the canonical pipeline docs — this skill complements them, doesn't duplicate them.

## How to update this skill

When `dictionary-pipeline` ships changes:

| Change in pipeline | Action here |
|-------------------|-------------|
| New stage added | Update the four-pass mapping table in SKILL.md and README.md if the new stage falls inside one of the four passes |
| New `derived_fields:` pattern family added in `contract.apply_derivations()` | Update Pass 4 to mention it as an alternative to `phase3_patterns.py` |
| New `--flag` on the CLI | Update Pass 3's full-run / per-stage commands |
| Stage 3 / Stage 6 stubs wired to a Claude entry point | Pass 2 + Pass 3 need to mention the LLM stages can now run via CLI; protocol shifts from "you draft inline" to "the pipeline calls Claude" |
| `scrub.py` gains the cleanup operations currently in `prestage_helper.py` | Mark `prestage_helper.py` as deprecated and point users to the pipeline's native handling |

When this skill ships changes:

- Run the full test suite from `D:\AI\Claude\claude-skills\skills\dictionary-pipeline\`: `python -m pytest tests/ -v`
- Re-run the live e2e against `assets/example_dataset.csv` to confirm pipeline + skill still cooperate
- Bump the description, asset inventory, and any per-pass details in both `SKILL.md` and the root `README.md` (the pre-commit hook enforces sync)

## Local development

The active load path on this machine is `~/.claude/skills/dictionary-pipeline/`. The authoring repo is `D:\AI\Claude\claude-skills\skills\dictionary-pipeline\`. After making changes here, deploy with:

```bash
bash deploy.sh
```

This copies `SKILL.md`, `README.md`, and `assets/` to the load path. Tests and the deploy script itself are dev-only and stay in the repo.

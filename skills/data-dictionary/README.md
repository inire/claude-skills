# data-dictionary

A Claude skill for drafting and iterating data dictionaries from raw datasets.

## What it does

Reads a CSV/Excel/tabular file, produces a per-field dictionary covering name, label, type, values, source, notes, and transformations. Iterates with the user through structured review passes until every field is confirmed (not inferred).

## Files

- `SKILL.md` — the skill itself; loaded by Claude when the user asks to build a data dictionary
- `eval/eval.json` — 15 binary-assertion test cases across 4 buckets (trigger discrimination, notes policy, label rule, output format gate)

## Status

- Skill: shipped
- Eval harness: cases written, runner not yet built, fixtures not yet generated

## Eval fixtures needed

The cases in `eval.json` reference six fixtures under `eval/fixtures/` that need to be created before the harness can run:

| Fixture | Purpose |
|---|---|
| `trigger_small.csv` | 5–10 clean fields, default case |
| `trigger_medium_30.csv` | Exercises the 16–50 output gate |
| `trigger_large.csv` | ~60 columns, exercises 51+ xlsx-only gate |
| `messy_status.csv` | Categorical with casing issues + typo for notes-policy test |
| `mixed_types.csv` | Integer column contaminated with `"N/A"` strings |
| `large_rowcount_100k.csv` | 100k+ rows, exercises sampling threshold |

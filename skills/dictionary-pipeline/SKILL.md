---
name: dictionary-pipeline
description: Use when the user wants to schema-validate a messy CSV/Excel file against a YAML contract AND produce a 3-tab Excel deliverable (cleaned data + data dictionary + automated-changes log), with optional post-pipeline derived columns. Generic across any tabular domain — consumer purchases, financial exports, survey instruments, inventory, CRM, healthcare records, IoT telemetry, etc. Triggers on phrases like "schema-validate this", "run the dictionary-pipeline", "validate and produce a 3-tab workbook", "I have a CSV/XLSX and want a documented validated workbook", "produce a Phase 3 workbook with derived columns", "do the full pipeline workflow on this", or when a user uploads a tabular file and asks for "a clean, documented, validated version". Do NOT use when (a) the user only wants a data dictionary as the deliverable — use the `data-dictionary` skill instead, which produces a Markdown/Excel dictionary without running the pipeline. (b) The user has already-clean data and only wants charting or analysis — answer inline with pandas. (c) The file is bound to a more domain-specific pipeline skill on this machine — use that skill instead. Installs dictionary-pipeline from github.com/inire/dictionary-pipeline at runtime if missing.
---

# dictionary-pipeline workflow

LLM-side companion for the [`dictionary-pipeline`](https://github.com/inire/dictionary-pipeline) tool. The pipeline runs as deterministic Python (Stages 0, 1, 4, 5, 7, 8, 9). This skill drives the four passes that aren't deterministic: pre-intake cleanup, dictionary drafting, run + interpret, and optional post-pipeline derivations.

## When to use

- User wants the **full deliverable**: validated data + data dictionary + change log, all in one 3-tab workbook
- User uploads a messy CSV/Excel and wants the "standard treatment"
- User wants to apply a YAML contract they already have to a new file
- User wants derived columns (Phase 3 / scoring / categorization) on top of validated data

## When NOT to use

- **User only wants a data dictionary** — use the `data-dictionary` skill. That skill produces a Markdown/Excel dictionary without running pandera, without producing the validated parquet checkpoints, and without the 3-tab Excel deliverable.
- **User has clean data and wants analysis** — just write pandas inline. The pipeline is overhead when there's nothing messy to validate.
- **User wants exploratory profiling only** — run `dictionary-pipeline intake` then `profile` and stop. The full skill is for the full workflow.
- **A more domain-specific skill applies** — if this machine has a pipeline skill bound to a particular export format (e.g. a forensic-export skill, a SOX-testing workpaper skill), let that one handle its own format.

## Quick start (just give me a prompt)

(written in task 4.1)

## The four-pass workflow

(written across tasks 2.2 / 3.2 / 4.1 / 5.2)

### Pass 1 — Pre-intake cleanup

(written in task 2.2)

### Pass 2 — Dictionary drafting

(written in task 3.2)

### Pass 3 — Run the pipeline

(written in task 4.1 / 4.2)

### Pass 4 — Optional post-pipeline derivations

(written in task 5.2)

## Common pitfalls

(written in task 6)

## Asset files

- `assets/prestage_helper.py` — fills the small gap left by the pipeline's `scrub.py` (currency-string normalization, column-name whitespace, drop empty `Unnamed:` columns)
- `assets/dictionary_template.yaml` — annotated YAML template covering every supported field type
- `assets/field_types_reference.md` — quick reference for `type` and `dtype` choices, including nullable extension dtypes
- `assets/phase3_patterns.py` — generic Pass-4 derivation patterns (presence flags, ordinal maps, days-since, picklist normalization, composite scoring)
- `assets/example_dataset.csv` — synthetic dataset that exercises every field-type pattern, end-to-end runnable

## Trigger-correctness manual checklist

(written in task 7.3)

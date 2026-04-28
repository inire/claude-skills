---
name: dictionary-pipeline
description: PLACEHOLDER — replaced in task 1.2 with the generic trigger description.
---

# dictionary-pipeline workflow

## When to use

(written in task 1.2)

## When NOT to use

(written in task 1.2)

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

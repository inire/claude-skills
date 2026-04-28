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

If the user wants the work done with minimal back-and-forth and isn't interested in the four-pass protocol, hand them this template — fill the blanks, paste back, done:

```
I have a new dataset to run through the dictionary-pipeline.

File:        <full path, e.g. D:\AI\Claude\datapipeline_2\export.csv>
What it is:  <one sentence — what the data represents and where it came from>
Grain:       <one row per WHAT? e.g. "one row per item per order">
PII:         <columns with personal data, or "none">
Quirks:      <preamble rows, footer rows, mixed-currency cols, sentinel dates, or "none that I noticed">
Workdir:     <a path OUTSIDE any git repo, e.g. D:\AI\Claude\runs\v1>

Run the dictionary-pipeline on this file using the four-pass workflow:
  1. Pre-intake cleanup if Stage 0 / Stage 4 fails on a raw run
  2. Intake + profile, then PAUSE and show me the draft dictionary
  3. After I approve: enforce -> clean -> derive -> validate -> export
  4. Optional: any Phase-3 derivations I asked for, run on the validated DataFrame

Show me the validation report and a sanity check on grain.
```

This expands into the protocol below. Anyone who'd rather drive it step-by-step can ignore the prompt and follow the four passes directly.

## The four-pass workflow

The pipeline runs as 11 stages (0–10). Most are deterministic Python; the LLM stages (2, 3, 6, 10) are where this skill earns its keep. Group them into four passes:

| Pass | Pipeline mapping | What this skill does |
|------|------------------|----------------------|
| 1 — Pre-intake cleanup | Pre-Stage 0 | Closes small gaps in `scrub.py` so Stage 0 / Stage 4 don't choke on currency sentinels or whitespace-padded column names |
| 2 — Dictionary drafting | Stages 2 + 3 | Composes the answer prompt from the Stage 1 profile, then drafts `dictionary.yaml` |
| 3 — Run + interpret | Stages 4–9 | Runs the full pipeline, interprets `validation_report.json`, fixes the dictionary and reruns when validation fails |
| 4 — Optional post-pipeline derivations | Post-Stage 9 | Generic Phase-3 derivation patterns when the YAML `derived_fields:` grammar isn't expressive enough |

Stage 10 (final compare) is a brief manual review on the delivered `.xlsx` — see [the pipeline's own workflow guide](https://github.com/inire/dictionary-pipeline/blob/master/docs/workflow.md#6-post-pipeline-review-stage-10--manual) rather than duplicating it here.

### Pass 1 — Pre-intake cleanup

**When to use:** Only when Stage 0 (intake) or Stage 4 (enforce) fails on a real export. A clean export with sane column headers and consistent dtypes does not need Pass 1.

**What `scrub.py` already does** (don't duplicate):
- Encoding detection (CSV / TSV)
- Header-row auto-detection (CSV / TSV) — Stage 0 wires this up via `--header-row auto` for delimited files
- Formula-injection scan
- Control-character strip

**What `assets/prestage_helper.py` adds** (the small gap):
- Whitespace strip on column names
- Drop empty `Unnamed: N` columns (Excel blank-index artifact)
- Currency-string normalization in object/string columns where the majority of non-null values are currency-parseable. Sentinels like ``""``, ``" "``, ``"$-"``, ``"$0"``, ``"-"`` become ``0.0`` so pandera can coerce to ``Float64`` / ``Int64`` in Stage 4.

**Excel header-row** is not auto-detected by the pipeline. If your Excel file has a title row above the headers, pass `--header-row 1` (or whatever the index is) to either the pipeline directly or to `prestage_helper.py`.

**Use it:**

```python
import sys
sys.path.insert(0, "/path/to/claude-skills/skills/dictionary-pipeline/assets")
from prestage_helper import prestage

log = prestage(
    "raw.xlsx",
    "cleaned.xlsx",
    header_row=1,                   # optional, defaults to 0
    currency_columns=["arr", "tcv"], # optional, force-normalize these even if auto-detection skips
)
print(log)
# {
#   "rows": 268,
#   "columns_after_strip": ["account_id", "account_name", "arr", ...],
#   "columns_dropped": ["Unnamed: 0"],
#   "header_row_used": 1,
#   "currency_normalizations": {
#     "arr": {"zero_sentinels": 142, "parsed": 126, "unparseable_to_null": 0},
#     "tcv": {"zero_sentinels": 89, "parsed": 179, "unparseable_to_null": 0}
#   }
# }
```

Or as a CLI:

```bash
python prestage_helper.py --input raw.xlsx --output cleaned.xlsx --header-row 1
```

**Then run the pipeline against the cleaned file:**

```bash
dictionary-pipeline run --input cleaned.xlsx --contract dictionary.yaml --workdir runs/v1
```

**Don't fight the helper.** If your column has 5 numeric values and 95 text values, auto-detection (correctly) skips it — the column isn't currency-shaped. Force-normalizing it with `currency_columns=["status"]` would null-out 95% of the values. Either decide that those 95% really are missing data (and accept the nulls), or don't normalize at all.

### Pass 2 — Dictionary drafting

**This is the highest-leverage point in the workflow.** Five minutes of careful drafting saves hours of iterating on schema failures. Pause here. Show the user the draft and your key decisions before running the rest of the pipeline.

**Prerequisite:** the file has been intaked and profiled. You have `intake_manifest.json` and `profile_summary.json` in the workdir. If not, run:

```bash
dictionary-pipeline intake  --input cleaned.csv --workdir runs/v1
dictionary-pipeline profile --workdir runs/v1
```

**Then hand-draft `dictionary.yaml`** using `assets/dictionary_template.yaml` as the structural reference and `assets/field_types_reference.md` for type/dtype choices. The pipeline's stage 3 is currently a stub — you (the LLM) do the drafting inline, not via a CLI call.

**The discipline (carry over from the [`data-dictionary`](../data-dictionary/SKILL.md) skill):**

1. **Sample 50+ distinct values** for each categorical before locking the `allowed_values` list. The profile's `top_values` only shows the top 5 — call `df['col'].value_counts()` on the full data if cardinality is unclear.
2. **Mark `review_status: draft`** on any field whose business semantics aren't certain. Never guess and mark `confirmed`. The user catches these on Pass-2 review.
3. **Notes must explain nulls, sentinels, and known issues.** A blank `notes:` is a code smell — at minimum say "no edge cases observed in sample of N rows."
4. **Document casing and picklist hygiene.** If you see `PROSPECT-Open` and `PROSPECT- Open` (with a stray space) in the same column, mention it. Don't silently normalize.
5. **State grain explicitly.** `dataset.grain` is the single most important line — "one row per WHAT?" — because every downstream count is wrong if grain is wrong.

#### Question checklist — ask the user when in doubt

These are domain-agnostic. For any column where the answer isn't obvious from the data:

| # | Pattern | Question |
|---|---------|----------|
| 1 | Presence-of-value flag (`X` or blank) | What does the flag mean — has the property, opted in, sent to system, etc.? |
| 2 | Grade / score / rating column | What's the rubric? Who assigns it? When? |
| 3 | Currency or amount column | Which currency? What period (annual / monthly / one-time)? Pre-tax or post-tax? |
| 4 | Count / measurement | Any overflow or floor sentinels (e.g. `10001+` capped at `10001`, `< 10` capped at `10`)? |
| 5 | Categorical (any cardinality) | What's the source taxonomy — system default, custom org list, external standard (NAICS, ISO, ICD)? Closed or open? |
| 6 | Column with `(U)`, `(R)`, `_v2` suffix | What does the suffix mean — enriched / redacted / version? |
| 7 | Two parallel columns disagreeing (raw vs enriched) | Which is canonical for downstream analysis? |
| 8 | Date column with old sentinel values (`1900-01-01`, `1970-01-01`, `1930-01-19`) | Real dates or epoch-style sentinels? |
| 9 | High null rate (>30%) | Does null mean "no data captured" or "no record applies here"? |
| 10 | Identifier-shaped column | Row-level primary key, or a grouping key (one value per N rows)? |
| 11 | Free text column | Could it contain PII (emails, names, addresses)? Any structured patterns worth pulling out? |
| 12 | Numeric column declared `Int64` but profile shows decimals | Was integer the intent, or should this be `decimal`? |
| 13 | Uncertain semantics | If the user can't answer, mark `review_status: draft` and add the question to `notes:` so it surfaces in the deliverable. |

**Don't ask what the user can't know.** If grain, type, or value range can be inferred from the data and the profile, infer it. Only ask when the data genuinely can't resolve the question (carries over from `data-dictionary`).

#### Skip the skill, just give me a prompt

The pipeline repo ships a copy-paste template for this exact handoff:

```
project_files/new_dataset_prompt.md
```

If the user prefers a one-shot prompt over a step-by-step skill walkthrough, point them at that file. The skill's Pass-2 protocol is what the prompt expands into when actually executed.

#### After drafting — pause for review

Before running the rest of the pipeline, present:

1. The complete `dictionary.yaml` (or the diff if you iterated)
2. A short list of the **decisions you made** — especially renames, derivations, and any guess-y `draft` fields
3. The **questions you flagged** that the user should answer before this becomes `confirmed`

Wait for explicit approval. Then run Pass 3.

### Pass 3 — Run the pipeline

After Pass-2 dictionary review and approval, run Stages 4–9 against the workdir from Pass 2.

#### Install (only if not already installed)

```bash
python -m pip show dictionary-pipeline >/dev/null 2>&1 \
  || python -m pip install "git+https://github.com/inire/dictionary-pipeline.git@master#egg=dictionary-pipeline[fuzzy,profiling]"
```

Optional extras:
- `[profiling]` — ydata-profiling for the richer Stage-1 HTML report
- `[fuzzy]` — rapidfuzz for fuzzy near-duplicate detection in Stage 5
- `[llm]` — Anthropic SDK for Stages 3 / 6 (currently unused — those are stubs; the LLM work happens via this skill instead)

#### Full run

```bash
dictionary-pipeline run \
  --input cleaned.xlsx \
  --contract dictionary.yaml \
  --workdir runs/v1
```

If your input is Excel with a non-zero header row, add `--header N`. If it's CSV/TSV, the pipeline auto-detects the header.

#### Per-stage commands (for re-running after a fix)

The pipeline checkpoints to parquet between stages, so a single stage can be re-run without replaying intake + profile:

```bash
dictionary-pipeline intake   --input file.xlsx --workdir runs/v1
dictionary-pipeline profile  --workdir runs/v1
dictionary-pipeline enforce  --workdir runs/v1 --contract dictionary.yaml
dictionary-pipeline derive   --workdir runs/v1 --contract dictionary.yaml
dictionary-pipeline export   --workdir runs/v1 --contract dictionary.yaml
```

Typical iteration loop after a Stage-4 failure:
1. Edit `dictionary.yaml` (the failure tells you which field and which constraint)
2. Re-run `enforce`
3. Re-run `export`

You only re-run `intake` / `profile` when the source file itself changed.

#### Post-run review checklist

Open `runs/v1/validation_report.json` after every successful run and check:

| Check | What to look at | Pass / fail signal |
|-------|-----------------|--------------------|
| Schema revalidation | `validation_report.json` → `schema_revalidation` | Must be `"passed"`. Anything else means a stage corrupted the data after Stage 4. |
| Drift columns | `validation_report.json` → `original_vs_final_diff` | Each entry is a column where rows changed. **Mismatches are expected** when cleaning ran. Look for surprises: columns that shouldn't change, mismatch counts wildly larger than the cleaning rule's intent, or `row_count_changed`. |
| Transformation log | `transformation_log.jsonl` | Skim for unexpected events. Whitespace strips and type coercions are fine. Aggressive normalization on a column you didn't expect is a flag. |
| Deliverable opens | `runs/v1/<dataset_name>.xlsx` | All three tabs render in Excel/Numbers/Sheets. Data tab has expected row count and column count. |

#### Common failures → fixes

| Failure (verbatim from `SchemaError` or terminal) | Probable cause | Fix |
|---------------------------------------------------|----------------|-----|
| `non-nullable series 'X' contains null values` | Field is `nullable: false` but data has nulls | Either set `nullable: true` with a `null_tolerance: 0.NN`, or add a Stage 5 fill rule, or fix the source |
| `column 'X' failed isin check` | A categorical value not in `allowed_values` | Add the value, or change `type: categorical` → `categorical_open` if the set is open, or add a Stage 5 lowercase/normalize rule |
| `dtype mismatch: expected Int64, got object` after coerce | Mixed string + number in a column declared numeric | Run `prestage_helper.py` (currency sentinels) or add a Stage 5 cleaning rule |
| `column 'X' not in DataFrame` | `source_column` in YAML doesn't match the actual header | Open `intake_manifest.json`, copy the exact header name, paste into `source_column` |
| `NotImplementedError: unsupported transformation pattern` | Stage 7 derivation uses a pattern outside arithmetic / groupby | Either rewrite to fit the pattern, or move it to Pass 4 (post-pipeline) |
| `ParserError` / `OutOfBoundsDatetime` on a date column | `parse_format` doesn't match the actual format, or sentinel dates | Inspect a few values; fix `parse_format` or document sentinels in `notes` |

For the full troubleshooting guide, see [`docs/workflow.md`](https://github.com/inire/dictionary-pipeline/blob/master/docs/workflow.md) in the pipeline repo — this skill summarizes; that doc is canonical.

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

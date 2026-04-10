---
name: data-dictionary
description: Use when a user explicitly wants to create, draft, or improve a data dictionary. Triggers on phrases like "build a data dictionary", "document my data", "describe my columns", "draft a dictionary for this dataset", "create a data dictionary from this file", or "I need a data dictionary". Do NOT trigger on generic data analysis, cleaning, or visualization requests, even if a CSV or Excel file is present.
---

# Data Dictionary Builder

## Overview

A data dictionary is a reference document that describes every field in a dataset — what it means, its type, valid values, and any quirks. Claude drafts one from raw files, then iterates with the user to clean it up in structured passes.

## When to Use

- User explicitly asks to document, describe, or dictionary-ify their fields
- User is preparing data for Claude to analyze and wants Claude to understand the schema first
- User needs a dictionary to guide data cleaning, validation, or instrument building

---

## Standard Dictionary Columns

| Column | Purpose |
|---|---|
| `field_name` | Exact name as it appears in the data (snake_case preferred) |
| `label` | Human-readable description of the field |
| `type` | See type definitions below |
| `values` | For categoricals: `{code}, {label} \| {code}, {label}` — see format note below |
| `source` | System or form this field comes from (e.g., CRM export, HRIS, manual entry) |
| `notes` | Nulls, known issues, business rules, edge cases — see notes policy below |
| `transformations` | Derived fields only: formula or logic used to compute the value. Example: `revenue_net = revenue_gross - refunds_total` |

Add or remove columns to match user-stated needs. If no template is provided, use these columns and state that you're doing so.

### Type Definitions

| Type | Use when | Edge cases |
|---|---|---|
| `text` | Free-form strings with no enumerable set of values | If a text field has <20 distinct values in the sample, flag it as possibly categorical |
| `integer` | Whole numbers only | If the column is 80%+ integers but contains strings like "N/A" or "—", type as `text` and note the mixed content in `notes` |
| `decimal` | Numbers with fractional parts | Includes currency, percentages stored as floats |
| `date` | Date or datetime values | Note the format (ISO, MM/DD/YYYY, epoch, etc.) and any timezone assumptions |
| `boolean` | Strictly two-state values | Covers true/false, 0/1, yes/no, y/n — note which encoding is used in `values` |
| `categorical` | Finite, enumerable set of values | Use when distinct count is low and values represent categories, codes, or statuses |
| `identifier` | Join keys, primary keys, external IDs (UUIDs, row numbers, foreign keys, external system IDs) | Never aggregate or analyze as text; note whether the ID is stable across exports and whether it joins to another table |
| `json` / `array` | Nested or multi-value fields | Note structure and whether values are ever null or malformed |

### Values Format

Use: `{code}, {label} | {code}, {label}`
Example: `0, Inactive | 1, Active | 2, Pending`

If values are too numerous to enumerate (continuous ranges, free IDs, open text): write `continuous — see notes` and put min/max/sample values in `notes`.

### Notes Policy

Never leave `notes` blank to signal "nothing wrong." Blank means "not yet reviewed." Use one of:
- `"No anomalies detected in sample"` — explicitly cleared
- `"Inferred — needs confirmation"` — Claude guessed; user must verify
- A specific observation: nulls, mixed types, unexpected values, business rule exceptions

The `notes` column is the highest-value column in the dictionary. Treat it accordingly.

---

## Examples

### Example A — messy categorical field

Raw column `status` in the source data contains: `Active`, `active`, `ACTIVE`, `Pendng`, `Inactive`, `null`.

| field_name | label | type | values | source | notes | transformations |
|---|---|---|---|---|---|---|
| `status` | Account lifecycle state | categorical | `Active \| Inactive \| Pending` | CRM export | Source data has mixed casing (`Active`/`active`/`ACTIVE`) — normalize to title case. Contains typo `Pendng` in 12 rows — **Inferred — needs confirmation** that this maps to `Pending`. 47 nulls present; unclear if structural or missing. |  |

Demonstrates: casing normalization, typo flagging with explicit "Inferred" marker, null ambiguity called out, `transformations` left blank because this is a raw field.

### Example B — derived numeric field

Field `quota_attainment_pct` is computed downstream, not in the source system.

| field_name | label | type | values | source | notes | transformations |
|---|---|---|---|---|---|---|
| `quota_attainment_pct` | Rep quota attainment as decimal percentage (0.0–1.0+ scale) | decimal | `continuous — see notes` | Derived | Range in sample: 0.0 to 1.47. Values >1.0 indicate over-attainment, not data errors. Period is rolling 12-month ending on export date — confirm with user whether quarterly alignment is needed. No nulls in sample. | `quota_attainment_pct = closed_won_arr / annual_quota` |

Demonstrates: `transformations` populated with formula, period assumption flagged for confirmation, `values` uses `continuous — see notes` per format rule, notes explain why >1.0 is valid.

---

## Workflow

### Phase 1 — Assess inputs

**If a data file is already provided:** proceed directly to Phase 2. Do not ask for it again.

**If no data file is present:** ask for it before proceeding.

**For each of the following, apply the default if not provided — do not ask:**
- No template → use standard columns above; state this at the top of the output
- No naming convention → use snake_case; note this assumption
- No existing documentation → skip validation; flag fields that need user confirmation in `notes`

Only ask questions when something is genuinely missing AND there is no reasonable default (e.g., ambiguous prefix rules that affect field names throughout the dictionary).

### Phase 2 — Draft v1

Generate the dictionary covering every column in the dataset. For each field:
- Assign `type` using the type definitions above
- Write a specific, plain-English `label` — never use the field name verbatim as the label
- For categoricals: enumerate all distinct values found in the actual data, not just documentation
- Populate `notes` per the notes policy — never leave blank
- Leave `transformations` empty for raw fields; only populate for derived/calculated fields

After delivering the draft, ask the user to review before proceeding to Phase 3.

#### Sampling large files

Row-count thresholds determine how much data to read. Apply these without asking the user; state the sample size at the top of the output.

| Row count | Strategy |
|---|---|
| <50k | Read the entire file |
| 50k–1M | Read first 10k rows + random 10k + last 10k (30k total) |
| >1M | Read first 10k + random 10k sample (20k total) and explicitly flag that cardinality may be underestimated |

When sampling is used:
1. State the sample size at the top of the output (e.g., `Dictionary drafted from 30k-row sample of 450k-row file`)
2. For every categorical field, append `"Values from N-row sample — cardinality may be underestimated"` to `notes`
3. For every numeric field, compute min/max from the sample and note that the range is sample-derived
4. Flag any field where the sample contains a single value — it may have more variation in the full file

### Phase 3 — Iterate

Run passes in response to user direction. Common passes:

- **Derived fields** — add calculated/composite fields (sum scores, attainment %, flags) with formula in `transformations`
- **Spec validation** — compare field names and values against an attached spec doc, codebook, or system guide; flag every mismatch explicitly
- **Naming cleanup** — apply prefix rules, abbreviation conventions, length limits; rename consistently across all fields

Each pass:
1. Make all changes
2. Summarize what changed and what was left unchanged (and why)
3. Flag anything still marked "Inferred — needs confirmation"
4. Ask for sign-off before the next pass

**Stopping condition:** Transition to Phase 4 when all of the following are true:
- Every field has a confirmed (not inferred) `type`
- Every categorical field has a fully enumerated `values` list
- No `notes` cell contains "Inferred" or "unclear"
- User has signed off on naming conventions

If the user keeps requesting passes beyond this point, note that the dictionary meets the done criteria and ask whether there's a specific remaining concern.

### Phase 4 — Final review and delivery

1. List every field where the value was inferred rather than confirmed — these are the user's validation targets
2. Flag any fields added or renamed since v1 that may affect downstream systems or reports
3. Deliver the final output per the output format rules below

---

## Output Format

| Dataset size | Format |
|---|---|
| ≤15 fields | Markdown table inline in chat |
| 16–50 fields | Markdown table inline + offer to produce an Excel file via the xlsx skill |
| 51+ fields | Always produce a downloadable Excel file via the xlsx skill — do not attempt an inline table |

When producing an Excel file: use one sheet per source system if the dictionary covers multiple systems. Include a `last_updated` cell and a `review_status` column (values: `confirmed`, `inferred`, `needs_review`).

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Blank `notes` cell | Use "No anomalies detected" or "Inferred — needs confirmation" — never truly blank |
| Vague labels ("date field", "id column") | Write a real description using field name + context + sample values |
| Listing expected values instead of actual values | Pull categoricals from the data; flag anything in the data not in the docs |
| One giant undivided pass | Phase 2 → user review → Phase 3 passes → Phase 4; never skip review gates |
| Treating null and zero as equivalent | Always note whether nulls are expected, structural, or meaningful |
| Reading full file when sampling was appropriate | Apply sampling thresholds from Phase 2 — do not load 1M+ rows when a 20k sample is sufficient |

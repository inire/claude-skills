# Field types reference

Quick reference for the `type` and `dtype` choices in `dictionary.yaml`. Ground-truth lives in [`dictionary_contract_format.md`](https://github.com/inire/dictionary-pipeline/blob/master/project_files/dictionary_contract_format.md) and [`contract.py`](https://github.com/inire/dictionary-pipeline/blob/master/src/dictionary_pipeline/contract.py) — this is the cheat sheet.

## Type tags

| `type` | When to use | Example |
|--------|-------------|---------|
| `categorical` | Closed value set, known in advance | order_status: [open, closed, refunded] |
| `categorical_open` | New values may appear over time; don't enforce a closed set | region, industry, product_family |
| `date` | Date or datetime column | order_date, last_login |
| `identifier` | Unique-ish key (UUID, primary key, account number) | order_id, account_id, sku |
| `integer` | Whole numbers | quantity, employee_count |
| `decimal` | Floating-point numbers | unit_price, conversion_rate |
| `text` | Free-form text | description, notes, url |
| `bool` | True/false | is_recurring, fedramp_certified |

## Dtype map

The `dtype` field is the pandas dtype string. **Capitalized = pandas nullable extension dtype** (supports NA). **Lowercase = numpy dtype** (does NOT support NA — coerce will fail on any null value).

| `dtype` | Backing pandas/numpy type | NA-safe? | Use when |
|---------|---------------------------|----------|----------|
| `string` | `pd.StringDtype()` | ✓ | All text and identifier fields |
| `Int64` | `pd.Int64Dtype()` | ✓ | Integer fields, especially nullable |
| `int64` | `pa.Int64` (numpy) | ✗ | Integer fields with `nullable: false` and you don't want pandera to permit any NA |
| `Float64` | `pd.Float64Dtype()` | ✓ | Decimal fields where you want explicit pd.NA semantics |
| `float64` | `pa.Float64` (numpy) | ✓ | Decimal fields — numpy float supports NaN natively, fine for most cases |
| `datetime64[ns]` | `pa.DateTime` | ✓ | All dates and timestamps |
| `boolean` | `pd.BooleanDtype()` | ✓ | Boolean fields, especially nullable |
| `bool` | `pa.Bool` (numpy) | ✗ | Boolean fields with `nullable: false` |

**Rule of thumb:** if `nullable: true`, use the capitalized dtype. If `nullable: false`, either form works but capitalized is safer (saves you a re-edit if you later flip to nullable).

## Per-type optional fields

| Field | Applies to | Effect |
|-------|------------|--------|
| `allowed_values: [...]` | `categorical` only | Pandera enforces closed set — fails Stage 4 on any value not listed |
| `min: <num>`, `max: <num>` | `integer`, `decimal` | Pandera range checks |
| `pattern: <regex>` | `text`, `identifier` | Pandera regex match check |
| `parse_format: <strftime>` | `date` | Pandas `to_datetime` format string for non-default formats |
| `null_tolerance: 0.0-1.0` | any (when `nullable: true`) | Max fraction of nulls allowed; exceeding fails Stage 4 |
| `pii: true` | any | Flagged in community-export; doesn't affect runtime |
| `reliability: unreliable` | any | Documents data quality concern; doesn't affect runtime |
| `review_status: draft \| confirmed` | any | Manual review marker; doesn't affect runtime but affects deliverable |
| `shareable: false` | any | Drop from community-export entirely |
| `community_notes: <str>` | any | Replaces `notes` in community-export |

## Common gotchas

### "non-nullable column has nulls"

`SchemaError: non-nullable series 'X' contains null values`. The fix is one of:
- Set `nullable: true` and add a `null_tolerance: 0.NN` matching observed null fraction
- Add a Stage 5 fill rule if nulls should default to a known value
- Investigate the source — sometimes nulls indicate a broken upstream

### "datatype coercion failed"

Common when an integer column has stray text like `"N/A"` or `" "` mixed in. The pipeline's intake doesn't normalize these because intake should be lossless. Two fixes:
- Run `prestage_helper.py` first if it's currency-string sentinels
- For categorical sentinels (e.g. "N/A" in a numeric column), add a Stage 5 cleaning rule that maps them to NA before Stage 4 enforce

### Categorical values failing `isin` check

`SchemaError: column 'X' failed isin check`. Either:
- A new value appeared that wasn't in your `allowed_values` — add it
- A casing variant slipped through (e.g. `REJECT` vs `reject`) — Stage 5 lowercase rule, OR widen `allowed_values` to include both forms
- The column is actually open-set, not closed — change `type: categorical` to `type: categorical_open` and remove `allowed_values`

### Date parse failures

`ParserError` or `OutOfBoundsDatetime`. Either:
- Wrong `parse_format` for your source — check the literal string
- Mixed formats in the same column — Stage 5 normalization
- Sentinel dates like `1900-01-01` or `2099-12-31` — keep them, but document in `notes`

## When the contract grammar isn't enough

The pipeline's `derived_fields:` only supports element-wise arithmetic and groupby aggregations. If you need:

- `isnull` / `notnull` flags
- `isin` set membership
- `fillna` / coalesce
- `lower()` / `upper()` / string ops
- Date arithmetic (days_since, etc.)
- Conditional logic
- Multi-column composite scoring

…use the Pass 4 patterns in [`phase3_patterns.py`](phase3_patterns.py) on the validated DataFrame post-Stage 9. Don't try to bend the contract grammar to do these — it's intentionally narrow.

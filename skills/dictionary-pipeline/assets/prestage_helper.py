"""
Pre-stage cleanup helper for dictionary-pipeline.

Closes the small gap between a real-world messy CSV/Excel export and
what the pipeline's Stage 0 / Stage 4 enforce can handle natively.
Three operations:

1. Strip whitespace from column names.
2. Drop columns matching `^Unnamed: \\d+$` whose values are all NA
   (artifact of Excel exports with a blank index column).
3. Normalize currency-string sentinels (`' $- '`, `'$0'`, `'-'`, ``''``)
   to ``0.0`` in object-dtype columns where >=50% of non-null values
   are currency-parseable. This lets pandera coerce to ``Float64`` /
   ``Int64`` in Stage 4 instead of raising a ``SchemaError``.

Header-row detection is *not* in scope here — the pipeline already
exposes ``--header-row N`` and ``scrub.detect_header_row``. If you
need a non-zero header row, pass ``header_row=N`` to this function
or to ``dictionary-pipeline run --header N`` directly.

Usage:
    from prestage_helper import prestage
    log = prestage("raw.xlsx", "cleaned.xlsx", header_row=1)
    # Now feed cleaned.xlsx to dictionary-pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

_UNNAMED_RE = re.compile(r"^Unnamed:\s*\d+$")
_EXCEL_SUFFIXES = {".xlsx", ".xls", ".xlsm", ".xlsb", ".ods"}
_CSV_SUFFIXES = {".csv"}
_TSV_SUFFIXES = {".tsv", ".tab"}

_ZERO_SENTINELS_RAW = {
    "",
    "-",
    "$-",
    "$0",
    "$0.00",
    "$0.0",
    "0",
    "0.0",
    "0.00",
}


def _normalize_currency_value(raw: Any) -> tuple[float | None, str | None]:
    """
    Try to parse a single cell as a currency-style number.

    Returns ``(value, sentinel_kind)`` where ``sentinel_kind`` is:
      - ``"zero_sentinels"`` for empty / dash-style values that mean zero
        (this includes NaN/None — in a currency column, missing means
        zero, not an unparseable error)
      - ``"parsed"`` for values that parsed as real numbers
      - ``None`` and value ``None`` if the input is a non-empty string
        that cannot parse (e.g. ``"ACTIVE"``)
    """
    if raw is None:
        return 0.0, "zero_sentinels"
    if isinstance(raw, float) and pd.isna(raw):
        return 0.0, "zero_sentinels"
    if isinstance(raw, (int, float)):
        return float(raw), "parsed"

    s = str(raw).strip()
    cleaned = s.replace("$", "").replace(",", "").replace("%", "").strip()

    if cleaned in _ZERO_SENTINELS_RAW or s in _ZERO_SENTINELS_RAW:
        return 0.0, "zero_sentinels"

    if not cleaned:
        return 0.0, "zero_sentinels"

    try:
        return float(cleaned), "parsed"
    except ValueError:
        return None, None


_EXPLICIT_CURRENCY_MARKERS = {"$-", "$0", "$0.0", "$0.00", "-"}


def _has_currency_marker(raw: Any) -> bool:
    """Return True if a cell contains an explicit currency marker."""
    if raw is None:
        return False
    if isinstance(raw, float) and pd.isna(raw):
        return False
    s = str(raw).strip()
    if not s:
        return False
    if "$" in s:
        return True
    return s in _EXPLICIT_CURRENCY_MARKERS


def _column_is_currency_like(series: pd.Series, threshold: float = 0.5) -> bool:
    """
    Decide whether a non-numeric column is a currency column.

    Detection requires explicit currency markers — at least one cell
    must contain a ``$`` or a recognized dash-style zero marker. This
    keeps the helper from claiming plain-numeric columns (percentages,
    counts, ratios) where empty just means "no value recorded".

    Returns True when ALL of these hold:
      - At least one value parses as a real number
      - At least one value has an explicit currency marker
      - (parsed + zero-sentinels) / (parsed + zero-sentinels + unparseable)
        is >= ``threshold``

    Already-numeric columns return False — nothing to clean. Pure
    numeric-with-empties columns return False — pandera coerce handles
    those without help.
    """
    if pd.api.types.is_numeric_dtype(series):
        return False
    non_null = series.dropna()
    if len(non_null) == 0:
        return False

    parsed = 0
    sentinel = 0
    unparseable = 0
    has_marker = False
    for v in non_null:
        val, kind = _normalize_currency_value(v)
        if _has_currency_marker(v):
            has_marker = True
        if val is None:
            unparseable += 1
        elif kind == "parsed":
            parsed += 1
        else:
            sentinel += 1

    if parsed == 0 or not has_marker:
        return False

    signal = parsed + sentinel
    total = signal + unparseable
    return (signal / total) >= threshold


def _normalize_currency_column(series: pd.Series) -> tuple[pd.Series, dict[str, int]]:
    """
    Apply ``_normalize_currency_value`` row-wise and return the new
    series plus a per-sentinel-kind count log.

    Counts include NaN-derived zero_sentinels — in a currency column,
    treating missing as zero is a deliberate behavior, and the count
    surfaces it in the log so the user can spot if the rate is high.
    """
    counts: dict[str, int] = {"zero_sentinels": 0, "parsed": 0, "unparseable_to_null": 0}
    out: list[float | None] = []
    for v in series:
        val, kind = _normalize_currency_value(v)
        if val is None:
            counts["unparseable_to_null"] += 1
        else:
            counts[kind or "parsed"] += 1
        out.append(val)
    return pd.Series(out, index=series.index, dtype="float64"), counts


def _read(input_path: Path, header_row: int | None) -> pd.DataFrame:
    suffix = input_path.suffix.lower()
    header = 0 if header_row is None else header_row

    if suffix in _CSV_SUFFIXES:
        return pd.read_csv(input_path, header=header)
    if suffix in _TSV_SUFFIXES:
        return pd.read_csv(input_path, header=header, sep="\t")
    if suffix in _EXCEL_SUFFIXES:
        return pd.read_excel(input_path, header=header)
    raise ValueError(
        f"Unsupported file extension {suffix!r}. "
        f"Supported: {sorted(_CSV_SUFFIXES | _TSV_SUFFIXES | _EXCEL_SUFFIXES)}"
    )


def _write(df: pd.DataFrame, output_path: Path) -> None:
    suffix = output_path.suffix.lower()
    if suffix in _CSV_SUFFIXES:
        df.to_csv(output_path, index=False)
    elif suffix in _TSV_SUFFIXES:
        df.to_csv(output_path, index=False, sep="\t")
    elif suffix in _EXCEL_SUFFIXES:
        df.to_excel(output_path, index=False)
    else:
        raise ValueError(
            f"Unsupported output extension {suffix!r}. "
            f"Supported: {sorted(_CSV_SUFFIXES | _TSV_SUFFIXES | _EXCEL_SUFFIXES)}"
        )


def prestage(
    input_path: str | Path,
    output_path: str | Path,
    *,
    header_row: int | None = None,
    currency_columns: list[str] | None = None,
) -> dict[str, Any]:
    """
    Clean a messy CSV / TSV / Excel file for dictionary-pipeline intake.

    Args:
        input_path: source file
        output_path: destination file (extension determines format; can be
            different from the input format, e.g. xlsx -> csv)
        header_row: zero-based index of the header row; defaults to 0
        currency_columns: list of column names to force-normalize even
            if auto-detection wouldn't (useful when a column has many
            text sentinels that should become null)

    Returns:
        Log dict with keys ``rows``, ``columns_after_strip``,
        ``columns_dropped``, ``header_row_used``, ``currency_normalizations``.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    header_used = 0 if header_row is None else header_row

    df = _read(input_path, header_row)

    df.columns = [str(c).strip() for c in df.columns]
    columns_after_strip = list(df.columns)

    # Cell-level whitespace cleanup. For each string-typed cell:
    #   - strip leading/trailing whitespace
    #   - if stripped result is empty, become NaN
    # Pandera's Stage-4 coerce can't handle " FALSE" -> bool or " 49.99" ->
    # float. The pipeline's Stage 5 strips whitespace AFTER enforcement and
    # only for text-type columns. Doing this globally pre-Stage-0 is safe:
    # leading/trailing whitespace is almost never analytically meaningful.
    def _strip_or_nan(v: Any) -> Any:
        if isinstance(v, str):
            stripped = v.strip()
            return pd.NA if stripped == "" else stripped
        return v

    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].map(_strip_or_nan)

    columns_dropped: list[str] = []
    for col in list(df.columns):
        if _UNNAMED_RE.match(col) and df[col].isna().all():
            df = df.drop(columns=[col])
            columns_dropped.append(col)

    explicit = set(currency_columns or [])
    currency_log: dict[str, dict[str, int]] = {}
    for col in df.columns:
        force = col in explicit
        is_currency = force or _column_is_currency_like(df[col])
        if is_currency:
            df[col], counts = _normalize_currency_column(df[col])
            currency_log[col] = counts

    _write(df, output_path)

    return {
        "rows": int(len(df)),
        "columns_after_strip": columns_after_strip,
        "columns_dropped": columns_dropped,
        "header_row_used": header_used,
        "currency_normalizations": currency_log,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Pre-stage cleanup for dictionary-pipeline")
    parser.add_argument("--input", required=True, help="path to messy source file")
    parser.add_argument("--output", required=True, help="path to write cleaned file")
    parser.add_argument(
        "--header-row",
        type=int,
        default=None,
        help="zero-based row index of the header (default: 0)",
    )
    parser.add_argument(
        "--currency-columns",
        nargs="*",
        default=None,
        help="explicit list of columns to force-normalize as currency",
    )
    args = parser.parse_args()

    log = prestage(
        args.input,
        args.output,
        header_row=args.header_row,
        currency_columns=args.currency_columns,
    )
    print(json.dumps(log, indent=2))

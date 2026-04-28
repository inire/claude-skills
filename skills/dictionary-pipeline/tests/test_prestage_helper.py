"""
Tests for assets/prestage_helper.py.

The helper closes the small gap between a messy real-world export and
what dictionary-pipeline Stage 0 / Stage 4 can handle directly:
- Strip whitespace from column names
- Drop empty `Unnamed: N` columns (artifact of Excel exports with a
  blank index column)
- Normalize currency-string sentinels (' $- ', '$0', '-', '') to 0.0
  in object-dtype columns where >=50% of non-null values are
  currency-parseable, so pandera can coerce to Float64 in Stage 4.

Header-row detection is NOT in scope here; the pipeline's
`--header-row N` flag and `scrub.detect_header_row` already handle it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ASSETS_DIR = Path(__file__).parent.parent / "assets"
sys.path.insert(0, str(ASSETS_DIR))

from prestage_helper import prestage  # noqa: E402


@pytest.fixture
def tmp_workdir(tmp_path: Path) -> Path:
    return tmp_path


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_clean_file_passes_through_unchanged(tmp_workdir: Path) -> None:
    raw = tmp_workdir / "clean.csv"
    out = tmp_workdir / "clean_out.csv"
    _write_csv(raw, "id,name,price\n1,Apple,1.50\n2,Banana,0.50\n")

    log = prestage(raw, out)

    df = pd.read_csv(out)
    assert list(df.columns) == ["id", "name", "price"]
    assert len(df) == 2
    assert log["rows"] == 2
    assert log["columns_dropped"] == []
    assert log["currency_normalizations"] == {}


def test_strips_whitespace_from_column_names(tmp_workdir: Path) -> None:
    raw = tmp_workdir / "padded.csv"
    out = tmp_workdir / "padded_out.csv"
    # Headers padded with leading/trailing spaces — common SFDC export artifact
    _write_csv(raw, "  id  , name ,  price\n1,Apple,1.50\n")

    log = prestage(raw, out)

    df = pd.read_csv(out)
    assert list(df.columns) == ["id", "name", "price"]
    assert log["columns_after_strip"] == ["id", "name", "price"]


def test_drops_empty_unnamed_columns(tmp_workdir: Path) -> None:
    raw = tmp_workdir / "unnamed.csv"
    out = tmp_workdir / "unnamed_out.csv"
    # Excel exports with a blank index column become "Unnamed: 0"
    _write_csv(raw, ",id,name\n,1,Apple\n,2,Banana\n")

    log = prestage(raw, out)

    df = pd.read_csv(out)
    assert "Unnamed: 0" not in df.columns
    assert list(df.columns) == ["id", "name"]
    assert "Unnamed: 0" in log["columns_dropped"]


def test_does_not_drop_unnamed_with_real_data(tmp_workdir: Path) -> None:
    raw = tmp_workdir / "unnamed_with_data.csv"
    out = tmp_workdir / "unnamed_with_data_out.csv"
    # An "Unnamed:" column that has actual values should be preserved —
    # the user can rename it in their dictionary YAML.
    _write_csv(raw, ",id,name\nval,1,Apple\n,2,Banana\n")

    log = prestage(raw, out)

    df = pd.read_csv(out)
    assert "Unnamed: 0" in df.columns
    assert log["columns_dropped"] == []


def test_normalizes_currency_sentinels_to_zero(tmp_workdir: Path) -> None:
    raw = tmp_workdir / "currency.csv"
    out = tmp_workdir / "currency_out.csv"
    # Common SFDC currency export artifacts: empty, space, ' $- ', '$0',
    # '-' all mean zero. Real numbers parse normally.
    _write_csv(
        raw,
        "id,arr\n"
        "1,1500.00\n"
        "2, $- \n"
        "3,$0\n"
        "4,-\n"
        "5,\n"
        "6, \n"
        "7,$0.00\n"
        "8,750.50\n",
    )

    log = prestage(raw, out)

    df = pd.read_csv(out)
    # arr column should now be numeric, with sentinels turned into 0.0
    assert pd.api.types.is_numeric_dtype(df["arr"])
    assert df["arr"].iloc[0] == 1500.00
    assert df["arr"].iloc[1] == 0.0
    assert df["arr"].iloc[2] == 0.0
    assert df["arr"].iloc[3] == 0.0
    assert df["arr"].iloc[4] == 0.0
    assert df["arr"].iloc[5] == 0.0
    assert df["arr"].iloc[6] == 0.0
    assert df["arr"].iloc[7] == 750.50
    # Log should record what was normalized
    assert "arr" in log["currency_normalizations"]
    assert log["currency_normalizations"]["arr"]["zero_sentinels"] >= 5


def test_does_not_touch_text_columns(tmp_workdir: Path) -> None:
    raw = tmp_workdir / "mixed.csv"
    out = tmp_workdir / "mixed_out.csv"
    _write_csv(
        raw,
        "id,name,arr\n"
        "1,Apple Inc,1500\n"
        "2,Banana Co, $- \n"
        "3,Cherry Ltd,750\n",
    )

    log = prestage(raw, out)

    df = pd.read_csv(out)
    # name should still be text, with values intact
    assert df["name"].iloc[0] == "Apple Inc"
    assert df["name"].iloc[1] == "Banana Co"
    # arr should be numeric (>50% parse)
    assert pd.api.types.is_numeric_dtype(df["arr"])
    assert "name" not in log["currency_normalizations"]


def test_skips_normalization_when_majority_unparseable(tmp_workdir: Path) -> None:
    """If <50% of non-null values are currency-parseable, leave the column alone."""
    raw = tmp_workdir / "mostly_text.csv"
    out = tmp_workdir / "mostly_text_out.csv"
    _write_csv(
        raw,
        "id,status\n"
        "1,ACTIVE\n"
        "2,1500\n"  # one numeric value
        "3,CLOSED\n"
        "4,PENDING\n",
    )

    log = prestage(raw, out)

    df = pd.read_csv(out)
    # status should still be non-numeric, untouched (object on pandas 2.x,
    # StringDtype on pandas 3.x — both are "not numeric")
    assert not pd.api.types.is_numeric_dtype(df["status"])
    assert df["status"].iloc[0] == "ACTIVE"
    assert "status" not in log["currency_normalizations"]


def test_handles_excel_with_explicit_header_row(tmp_workdir: Path) -> None:
    """Excel input with header on row 1 (not row 0) — common SFDC artifact."""
    raw = tmp_workdir / "with_preamble.xlsx"
    out = tmp_workdir / "with_preamble_out.xlsx"
    # Row 0: a title row; row 1: real headers; rows 2+: data
    df_input = pd.DataFrame(
        [
            ["Q1 2026 Pipeline Report", None, None],
            ["account_id", "account_name", "arr"],
            [1, "Apple Inc", 1500],
            [2, "Banana Co", 750],
        ]
    )
    df_input.to_excel(raw, header=False, index=False)

    log = prestage(raw, out, header_row=1)

    df = pd.read_excel(out)
    assert list(df.columns) == ["account_id", "account_name", "arr"]
    assert len(df) == 2
    assert log["rows"] == 2
    assert log["header_row_used"] == 1


def test_skips_columns_without_currency_markers(tmp_workdir: Path) -> None:
    """A plain percentage column (numbers + empties, no $ markers) should be left alone.

    Without this check, the detection would falsely flag any column where
    most cells are empty/numeric as currency-like, which would convert
    legitimate NaN-meaning-missing into 0.0.
    """
    raw = tmp_workdir / "percentage.csv"
    out = tmp_workdir / "percentage_out.csv"
    _write_csv(
        raw,
        "id,discount_pct\n"
        "1,15.0\n"
        "2,\n"
        "3,5.5\n"
        "4,\n"
        "5,10.0\n"
        "6,\n"
        "7,12.5\n",
    )

    log = prestage(raw, out)

    # discount_pct has no $ markers, so prestage should skip it.
    # Empties stay as NaN; pandera coerce will handle the column natively.
    assert "discount_pct" not in log["currency_normalizations"]


def test_explicit_currency_columns_override_detection(tmp_workdir: Path) -> None:
    """If the user passes currency_columns explicitly, normalize even when <50% parses."""
    raw = tmp_workdir / "explicit.csv"
    out = tmp_workdir / "explicit_out.csv"
    # arr column has only 1 numeric value out of 4 — auto-detection would skip it,
    # but explicit hint forces normalization
    _write_csv(
        raw,
        "id,arr\n"
        "1,ACTIVE\n"  # would-be sentinel after explicit — kept null
        "2,1500\n"
        "3, $- \n"
        "4,CLOSED\n",  # would-be sentinel after explicit — kept null
    )

    log = prestage(raw, out, currency_columns=["arr"])

    df = pd.read_csv(out)
    # 1500 parses to 1500.0, ' $- ' parses to 0.0, ACTIVE/CLOSED stay null
    assert df["arr"].iloc[1] == 1500.0
    assert df["arr"].iloc[2] == 0.0
    assert pd.isna(df["arr"].iloc[0])
    assert pd.isna(df["arr"].iloc[3])
    assert log["currency_normalizations"]["arr"]["unparseable_to_null"] == 2

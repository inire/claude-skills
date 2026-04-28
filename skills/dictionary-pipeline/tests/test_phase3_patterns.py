"""
Tests for assets/phase3_patterns.py.

The pattern library is what you reach for when the pipeline's
``derived_fields:`` grammar isn't expressive enough — flag-from-presence,
ordinal mapping, days-since, picklist normalization, domain canonicalization,
set-membership classification, and weighted composite scoring.

These run on the validated DataFrame *after* Stage 9 (post-pipeline), not
inside the contract.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ASSETS_DIR = Path(__file__).parent.parent / "assets"
sys.path.insert(0, str(ASSETS_DIR))

from phase3_patterns import (  # noqa: E402
    canonical_domain,
    classify_set_membership,
    coalesce_with_sentinel,
    composite_score,
    days_since,
    flag_from_presence,
    normalize_picklist,
    ordinal_map,
)


# ---------- flag_from_presence ----------------------------------------


def test_flag_from_presence_strings() -> None:
    s = pd.Series(["X", "", " ", None, "Y", np.nan])
    out = flag_from_presence(s)
    assert out.tolist() == [True, False, False, False, True, False]


def test_flag_from_presence_numeric() -> None:
    s = pd.Series([1, 0, np.nan, 5, -1])
    out = flag_from_presence(s)
    # Numeric: nonzero non-null is True. Zero and NaN are False.
    assert out.tolist() == [True, False, False, True, True]


# ---------- coalesce_with_sentinel ------------------------------------


def test_coalesce_treats_sentinel_as_missing() -> None:
    primary = pd.Series([10, 20, 10001, np.nan, 50])
    fallback = pd.Series([100, 200, 999, 400, 500])
    out = coalesce_with_sentinel(primary, fallback, sentinel=10001)
    # Position 0,1: primary wins. Position 2: sentinel -> fallback. Position 3:
    # NaN -> fallback. Position 4: primary wins.
    assert out.tolist() == [10, 20, 999, 400, 50]


def test_coalesce_no_sentinel_just_nan() -> None:
    primary = pd.Series([10.0, np.nan, 30.0])
    fallback = pd.Series([100.0, 200.0, 300.0])
    out = coalesce_with_sentinel(primary, fallback)
    assert out.tolist() == [10.0, 200.0, 30.0]


# ---------- ordinal_map -----------------------------------------------


def test_ordinal_map_basic() -> None:
    s = pd.Series(["none", "quarantine", "reject", "none"])
    out = ordinal_map(s, {"none": 0, "quarantine": 1, "reject": 2})
    assert out.tolist() == [0, 1, 2, 0]


def test_ordinal_map_missing_uses_default() -> None:
    s = pd.Series(["high", "medium", "unknown_value", None])
    out = ordinal_map(s, {"low": 1, "medium": 2, "high": 3}, default=-1)
    # 'unknown_value' and None both fall to default
    assert out.tolist() == [3, 2, -1, -1]


def test_ordinal_map_default_is_nan() -> None:
    s = pd.Series(["A", "Z"])
    out = ordinal_map(s, {"A": 1})
    assert out.iloc[0] == 1
    assert pd.isna(out.iloc[1])


# ---------- days_since -------------------------------------------------


def test_days_since_basic() -> None:
    s = pd.to_datetime(pd.Series(["2026-01-01", "2026-04-01", "2026-04-28"]))
    out = days_since(s, snapshot=date(2026, 4, 28))
    assert out.tolist() == [117, 27, 0]


def test_days_since_handles_nat() -> None:
    s = pd.to_datetime(pd.Series(["2026-01-01", None, "2026-04-28"]))
    out = days_since(s, snapshot=date(2026, 4, 28))
    assert out.iloc[0] == 117
    assert pd.isna(out.iloc[1])
    assert out.iloc[2] == 0


def test_days_since_excludes_sentinels() -> None:
    s = pd.to_datetime(pd.Series(["2026-01-01", "1900-01-01", "1970-01-01"]))
    out = days_since(
        s,
        snapshot=date(2026, 4, 28),
        sentinel_dates=[date(1900, 1, 1), date(1970, 1, 1)],
    )
    assert out.iloc[0] == 117
    assert pd.isna(out.iloc[1])
    assert pd.isna(out.iloc[2])


# ---------- normalize_picklist ----------------------------------------


def test_normalize_picklist_basic() -> None:
    s = pd.Series(["PROSPECT- Open", "PROSPECT-Open", "Closed", "  closed  "])
    out = normalize_picklist(
        s,
        replacements={"PROSPECT- Open": "PROSPECT-Open"},
        strip=True,
    )
    # Replacement applies to first; second stays; third gets stripped only;
    # fourth gets whitespace stripped.
    assert out.tolist() == ["PROSPECT-Open", "PROSPECT-Open", "Closed", "closed"]


def test_normalize_picklist_lowercase() -> None:
    s = pd.Series(["REJECT", "Reject", "reject"])
    out = normalize_picklist(s, replacements={}, lowercase=True)
    assert out.tolist() == ["reject", "reject", "reject"]


# ---------- canonical_domain ------------------------------------------


def test_canonical_domain_strips_scheme_and_path() -> None:
    s = pd.Series(
        [
            "https://www.example.com/path?query",
            "WWW.EXAMPLE.COM",
            "example.com",
            "http://sub.example.org",
            "",
            None,
        ]
    )
    out = canonical_domain(s)
    assert out.iloc[0] == "example.com"
    assert out.iloc[1] == "example.com"
    assert out.iloc[2] == "example.com"
    assert out.iloc[3] == "sub.example.org"
    assert pd.isna(out.iloc[4]) or out.iloc[4] == ""
    assert pd.isna(out.iloc[5])


# ---------- classify_set_membership -----------------------------------


def test_classify_set_membership_basic() -> None:
    s = pd.Series(["GMAIL", "OUTLOOK", "PROOFPOINT", "MIMECAST", "WEIRD"])
    sets = {
        "native": {"GMAIL", "OUTLOOK"},
        "competitor": {"PROOFPOINT", "MIMECAST"},
    }
    out = classify_set_membership(s, sets, default="unknown")
    assert out.tolist() == [
        "native",
        "native",
        "competitor",
        "competitor",
        "unknown",
    ]


def test_classify_handles_nan() -> None:
    s = pd.Series(["A", None, "B"])
    sets = {"set1": {"A"}, "set2": {"B"}}
    out = classify_set_membership(s, sets, default="other")
    assert out.tolist() == ["set1", "other", "set2"]


def test_classify_first_match_wins() -> None:
    s = pd.Series(["A", "B"])
    sets = {"first": {"A", "B"}, "second": {"B"}}
    # Dict insertion order — 'first' wins for B
    out = classify_set_membership(s, sets, default="x")
    assert out.tolist() == ["first", "first"]


# ---------- composite_score -------------------------------------------


def test_composite_score_weighted_sum() -> None:
    df = pd.DataFrame(
        {
            "is_industry_match": [1, 0, 1],
            "is_recent": [1, 1, 0],
            "size_score": [3, 1, 2],
        }
    )
    out = composite_score(
        df,
        weights={"is_industry_match": 2.0, "is_recent": 1.5, "size_score": 1.0},
    )
    # Row 0: 1*2.0 + 1*1.5 + 3*1.0 = 6.5
    # Row 1: 0*2.0 + 1*1.5 + 1*1.0 = 2.5
    # Row 2: 1*2.0 + 0*1.5 + 2*1.0 = 4.0
    assert out.tolist() == [6.5, 2.5, 4.0]


def test_composite_score_missing_columns_count_as_zero() -> None:
    df = pd.DataFrame({"a": [1, 2, 3]})
    out = composite_score(df, weights={"a": 1.0, "b_does_not_exist": 5.0})
    # Missing column 'b_does_not_exist' contributes 0
    assert out.tolist() == [1.0, 2.0, 3.0]


def test_composite_score_handles_nan() -> None:
    df = pd.DataFrame({"a": [1, np.nan, 3], "b": [1, 1, np.nan]})
    out = composite_score(df, weights={"a": 1.0, "b": 1.0})
    # NaN treated as 0
    assert out.tolist() == [2.0, 1.0, 3.0]


def test_composite_score_returns_named_series() -> None:
    df = pd.DataFrame({"a": [1, 2]})
    out = composite_score(df, weights={"a": 1.0}, name="priority_score")
    assert out.name == "priority_score"

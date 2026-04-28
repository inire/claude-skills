"""
Pass-4 derivation patterns for dictionary-pipeline.

These run on the *validated* DataFrame after Stage 9 (post-pipeline),
not inside the pipeline's contract grammar. Use them when ``derived_fields:``
in the YAML can't express what you need — for example: presence flags,
fillna / coalesce, ordinal mapping, days-since computations, picklist
normalization, domain canonicalization, set-membership classification,
composite weighted scoring.

Each function returns a new ``pd.Series`` (or applies in place) and
documents its semantics. Behavior on NaN is explicit per function — read
the docstrings before using on data with high null rates.

Importable as a module:

    from phase3_patterns import flag_from_presence, composite_score, ...
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

import numpy as np
import pandas as pd


# ---------- flag_from_presence ----------------------------------------


def flag_from_presence(series: pd.Series) -> pd.Series:
    """
    Return a boolean series: True where the value is "present and meaningful".

    Rules:
      - NaN / None / NA -> False
      - Numeric 0 -> False (zero is the absence of a count)
      - Empty string and whitespace-only string -> False
      - Anything else -> True

    Useful for SFDC-style "X" or "" presence-flag columns and for
    numeric columns where 0 means "no signal" (e.g. ARR, employee count).
    """
    if pd.api.types.is_numeric_dtype(series):
        return (series.fillna(0) != 0)
    return series.apply(
        lambda v: False if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "" else True
    )


# ---------- coalesce_with_sentinel ------------------------------------


def coalesce_with_sentinel(
    primary: pd.Series,
    fallback: pd.Series,
    sentinel: Any = None,
) -> pd.Series:
    """
    Return ``primary`` where it has a real value, ``fallback`` otherwise.

    A "real value" means: not NaN AND not equal to ``sentinel``.

    Use case: an enriched count column with an overflow sentinel
    (e.g. employee_count_enriched=10001 means "10000+", real value lives
    in employee_count_raw).

    If ``sentinel`` is None, only NaN values fall through to fallback.
    """
    out = primary.copy()
    mask = primary.isna()
    if sentinel is not None:
        mask = mask | (primary == sentinel)
    out[mask] = fallback[mask]
    return out


# ---------- ordinal_map -----------------------------------------------


def ordinal_map(
    series: pd.Series,
    mapping: dict[Any, int | float],
    default: Any = np.nan,
) -> pd.Series:
    """
    Map categorical values to a numeric ordinal ranking.

    Values not in ``mapping`` (and NaN) become ``default``. To make the
    output strictly numeric, set ``default=-1`` or similar; otherwise it
    contains NaN.

    Example: DMARC strength
        ordinal_map(s, {"none": 0, "quarantine": 1, "reject": 2})
    """
    return series.map(mapping).where(series.isin(mapping), default)


# ---------- days_since -------------------------------------------------


def days_since(
    date_series: pd.Series,
    snapshot: date | datetime | str,
    sentinel_dates: Iterable[date | datetime | str] | None = None,
) -> pd.Series:
    """
    Return integer days between ``snapshot`` and each row's date.

    NaT and any date in ``sentinel_dates`` (e.g. ``date(1900, 1, 1)``,
    ``date(1970, 1, 1)`` for epoch sentinels) become NaN. Output is a
    nullable Int64 series.

    Negative values mean the row's date is in the future relative to
    ``snapshot`` — that's allowed.
    """
    snapshot_ts = pd.Timestamp(snapshot)
    series = pd.to_datetime(date_series, errors="coerce")

    sentinels: set[pd.Timestamp] = set()
    if sentinel_dates:
        sentinels = {pd.Timestamp(d) for d in sentinel_dates}

    delta = (snapshot_ts - series).dt.days
    if sentinels:
        sentinel_mask = series.isin(sentinels)
        delta = delta.where(~sentinel_mask, np.nan)
    return delta.astype("Int64")


# ---------- normalize_picklist ----------------------------------------


def normalize_picklist(
    series: pd.Series,
    replacements: dict[str, str],
    *,
    strip: bool = True,
    lowercase: bool = False,
) -> pd.Series:
    """
    Apply replacement rules + optional whitespace strip + optional lowercasing.

    Order of operations:
      1. Replace per ``replacements`` mapping (exact match)
      2. Strip whitespace if ``strip=True``
      3. Lowercase if ``lowercase=True``

    Use case: cleaning up picklist hygiene issues like
    ``"PROSPECT- Open"`` (stray space) -> ``"PROSPECT-Open"`` without
    silently doing it inside the contract.
    """
    s = series.astype("object").map(lambda v: replacements.get(v, v) if isinstance(v, str) else v)
    if strip:
        s = s.map(lambda v: v.strip() if isinstance(v, str) else v)
    if lowercase:
        s = s.map(lambda v: v.lower() if isinstance(v, str) else v)
    return s


# ---------- canonical_domain ------------------------------------------


_DOMAIN_RE = re.compile(r"^(?:https?://)?(?:www\.)?([^/\s?#]+)", re.IGNORECASE)


def canonical_domain(series: pd.Series) -> pd.Series:
    """
    Lowercase, strip scheme + ``www.`` + path, return just the host.

    ``"https://www.Example.com/path?q"`` -> ``"example.com"``
    Empty strings stay empty. NaN stays NaN.
    """
    def _one(v: Any) -> Any:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return v
        s = str(v).strip()
        if not s:
            return s
        m = _DOMAIN_RE.match(s)
        host = m.group(1) if m else s
        return host.lower()

    return series.map(_one)


# ---------- classify_set_membership -----------------------------------


def classify_set_membership(
    series: pd.Series,
    sets: dict[str, Iterable[Any]],
    default: Any = np.nan,
) -> pd.Series:
    """
    Categorize each value into a named bucket.

    ``sets`` is a mapping of category name -> set of valid values.
    First-match wins (dict insertion order). Values matching no set
    become ``default``.

    Example:
        classify_set_membership(
            series,
            {"native": {"GMAIL", "OUTLOOK"}, "competitor": {"PROOFPOINT"}},
            default="unknown",
        )
    """
    frozen_sets: dict[str, frozenset] = {k: frozenset(v) for k, v in sets.items()}

    def _classify(v: Any) -> Any:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return default
        for name, members in frozen_sets.items():
            if v in members:
                return name
        return default

    return series.map(_classify)


# ---------- composite_score -------------------------------------------


def composite_score(
    df: pd.DataFrame,
    weights: dict[str, float],
    *,
    name: str = "composite_score",
) -> pd.Series:
    """
    Weighted sum across columns. Missing columns count as zero. NaN
    cells count as zero.

    Use when you want a transparent additive priority score —
    ``weights`` makes the rubric inspectable. Don't try to bake the
    rubric into a black-box machine-learning model when a weighted sum
    of explicit signals does the job.

    Returns a series named ``name`` (default ``"composite_score"``).
    """
    score = pd.Series(0.0, index=df.index)
    for col, w in weights.items():
        if col in df.columns:
            score = score + df[col].fillna(0).astype(float) * w
    score.name = name
    return score

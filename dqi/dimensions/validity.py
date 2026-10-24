"""
Validity dimension: measures how many field values conform to their declared type and rules.

Each FieldType has specific validation logic:
  TEXT      : non-empty string with length > 1
  INTEGER   : numeric, coercible to int, within min/max if set
  FLOAT     : numeric, within min/max if set
  DATE      : parseable as a date, within min/max if set
  PHONE     : matches E.164-like pattern
  EMAIL     : matches RFC-like email pattern
  LATITUDE  : float in [-90, 90]
  LONGITUDE : float in [-180, 180]
  ENUM      : value in allowed_values list
  ID        : non-empty value
  BOOLEAN   : one of the accepted boolean representations

Score = (valid cells across all fields) / (total non-null cells across all fields) * 100
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import Any
import pandas as pd
from ..schema import Schema, FieldType, FieldDefinition

_PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,15}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_BOOL_VALUES = {"true", "false", "1", "0", "yes", "no"}


def _validate_value(value: Any, fdef: FieldDefinition) -> tuple[bool, str]:
    """
    Validate a single value against a FieldDefinition.

    Returns (is_valid, reason_string). reason_string is empty when valid.
    """
    str_val = str(value).strip()

    if fdef.type == FieldType.TEXT:
        if len(str_val) < 2:
            return False, "text_too_short"
        if fdef.pattern and not re.match(fdef.pattern, str_val):
            return False, "pattern_mismatch"
        return True, ""

    if fdef.type == FieldType.ID:
        if not str_val or str_val.lower() in ("nan", "none", ""):
            return False, "id_empty"
        return True, ""

    if fdef.type == FieldType.BOOLEAN:
        if str_val.lower() not in _BOOL_VALUES:
            return False, f"invalid_boolean_value: {str_val!r}"
        return True, ""

    if fdef.type == FieldType.EMAIL:
        if not _EMAIL_RE.match(str_val):
            return False, "invalid_email_format"
        return True, ""

    if fdef.type == FieldType.PHONE:
        if not _PHONE_RE.match(str_val):
            return False, "invalid_phone_format"
        return True, ""

    if fdef.type == FieldType.ENUM:
        if fdef.allowed_values and str_val not in fdef.allowed_values:
            return False, f"value_not_in_allowed_list: {str_val!r}"
        return True, ""

    if fdef.type == FieldType.DATE:
        parsed = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(str_val, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            return False, "unparseable_date"
        if fdef.min is not None:
            try:
                min_dt = datetime.strptime(str(fdef.min), "%Y-%m-%d")
                if parsed < min_dt:
                    return False, f"date_before_min: {fdef.min}"
            except ValueError:
                pass
        if fdef.max is not None:
            try:
                max_dt = datetime.strptime(str(fdef.max), "%Y-%m-%d")
                if parsed > max_dt:
                    return False, f"date_after_max: {fdef.max}"
            except ValueError:
                pass
        return True, ""

    if fdef.type in (FieldType.INTEGER, FieldType.FLOAT, FieldType.LATITUDE, FieldType.LONGITUDE):
        try:
            num = float(str_val)
        except ValueError:
            return False, "not_numeric"

        if fdef.type == FieldType.LATITUDE:
            lo, hi = -90.0, 90.0
        elif fdef.type == FieldType.LONGITUDE:
            lo, hi = -180.0, 180.0
        else:
            lo = float(fdef.min) if fdef.min is not None else None
            hi = float(fdef.max) if fdef.max is not None else None

        if lo is not None and num < lo:
            return False, f"below_min: {lo}"
        if hi is not None and num > hi:
            return False, f"above_max: {hi}"

        if fdef.type == FieldType.INTEGER:
            if num != int(num):
                return False, "not_an_integer"

        return True, ""

    # Fallback for unknown types
    return True, ""


def score(df: pd.DataFrame, schema: Schema) -> dict:
    """
    Compute the validity score for a DataFrame against a Schema.

    Returns
    -------
    dict with keys:
        score          : float, 0-100
        field_scores   : dict mapping field name to its individual validity score
        issues         : list of dicts, each {row_index, field, reason, value}
    """
    issues: list[dict] = []
    field_scores: dict[str, float] = {}

    total_checked = 0
    total_valid = 0

    for col, fdef in schema.fields.items():
        if col not in df.columns:
            field_scores[col] = 0.0
            continue

        series = df[col]
        non_null_mask = series.notna() & (series.astype(str).str.strip() != "")
        non_null_series = series[non_null_mask]

        if len(non_null_series) == 0:
            field_scores[col] = 100.0
            continue

        valid_count = 0
        for idx, val in non_null_series.items():
            is_valid, reason = _validate_value(val, fdef)
            if is_valid:
                valid_count += 1
            else:
                issues.append({
                    "row_index": int(idx),
                    "field": col,
                    "reason": reason,
                    "value": str(val),
                })

        field_score = valid_count / len(non_null_series) * 100.0
        field_scores[col] = round(field_score, 2)
        total_checked += len(non_null_series)
        total_valid += valid_count

    overall = (total_valid / total_checked * 100.0) if total_checked > 0 else 100.0

    return {
        "score": round(overall, 2),
        "field_scores": field_scores,
        "issues": issues,
    }

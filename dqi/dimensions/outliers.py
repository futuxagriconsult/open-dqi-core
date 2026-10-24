"""
Outlier detection dimension: IQR-based outlier flagging for numeric fields.

For each numeric field:
    Q1, Q3 = 25th and 75th percentiles
    IQR    = Q3 - Q1
    lower  = Q1 - 1.5 * IQR
    upper  = Q3 + 1.5 * IQR

Any record with a value outside [lower, upper] is flagged as an outlier.

Score = (records with zero outlier fields) / total_records * 100
"""
from __future__ import annotations
import pandas as pd
from ..schema import Schema


def score(df: pd.DataFrame, schema: Schema) -> dict:
    """
    Compute the outlier score for a DataFrame against a Schema.

    Returns
    -------
    dict with keys:
        score          : float, 0-100
        outlier_counts : dict mapping field name to number of outlier rows
        bounds         : dict mapping field name to {lower, upper, q1, q3, iqr}
        issues         : list of {row_index, field, value, lower_bound, upper_bound}
    """
    numeric_fields = schema.numeric_fields()
    present = [f for f in numeric_fields if f in df.columns]

    if not present:
        return {
            "score": 100.0,
            "outlier_counts": {},
            "bounds": {},
            "issues": [],
        }

    issues: list[dict] = []
    outlier_counts: dict[str, int] = {}
    bounds: dict[str, dict] = {}
    flagged_rows: set[int] = set()

    for col in present:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 4:
            outlier_counts[col] = 0
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        bounds[col] = {
            "lower": round(lower, 4),
            "upper": round(upper, 4),
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
        }

        numeric_full = pd.to_numeric(df[col], errors="coerce")
        outlier_mask = (numeric_full < lower) | (numeric_full > upper)
        outlier_mask = outlier_mask & numeric_full.notna()
        col_outlier_count = int(outlier_mask.sum())
        outlier_counts[col] = col_outlier_count

        for idx in df.index[outlier_mask]:
            flagged_rows.add(int(idx))
            issues.append({
                "row_index": int(idx),
                "field": col,
                "value": float(numeric_full.loc[idx]),
                "lower_bound": round(lower, 4),
                "upper_bound": round(upper, 4),
            })

    total = len(df)
    clean_rows = total - len(flagged_rows)
    outlier_score = (clean_rows / total * 100.0) if total > 0 else 100.0

    return {
        "score": round(outlier_score, 2),
        "outlier_counts": outlier_counts,
        "bounds": bounds,
        "issues": issues,
    }

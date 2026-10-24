"""
Completeness dimension: measures what fraction of required fields are populated.

Score = (filled required fields across all records) / (total required fields across all records)
Scaled to 0-100.
"""
import pandas as pd
from ..schema import Schema


def score(df: pd.DataFrame, schema: Schema) -> dict:
    """
    Compute the completeness score for a DataFrame against a Schema.

    Returns
    -------
    dict with keys:
        score           : float, 0-100
        required_fields : list of field names that are required
        null_rates      : dict mapping field name to null rate (0.0-1.0)
        issues          : list of dicts, each {row_index, field, reason}
    """
    required = schema.required_fields()
    if not required:
        return {"score": 100.0, "required_fields": [], "null_rates": {}, "issues": []}

    # Only check fields that exist in the dataframe
    present = [f for f in required if f in df.columns]
    missing_from_df = [f for f in required if f not in df.columns]

    null_rates: dict[str, float] = {}
    issues: list[dict] = []

    total_cells = len(df) * len(present) if present else 0
    filled_cells = 0

    for col in present:
        null_mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        null_count = int(null_mask.sum())
        null_rates[col] = float(null_count / len(df)) if len(df) > 0 else 0.0
        filled_cells += len(df) - null_count
        for idx in df.index[null_mask]:
            issues.append({"row_index": int(idx), "field": col, "reason": "required_field_empty"})

    # Columns entirely absent from the dataframe count as 100% missing
    for col in missing_from_df:
        null_rates[col] = 1.0
        issues.append({"row_index": -1, "field": col, "reason": "column_missing_from_dataset"})

    total_cells += len(df) * len(missing_from_df)
    completeness_score = (filled_cells / total_cells * 100.0) if total_cells > 0 else 100.0

    return {
        "score": round(completeness_score, 2),
        "required_fields": required,
        "null_rates": null_rates,
        "issues": issues,
    }

"""
Uniqueness dimension: detects duplicate records via exact and fuzzy matching.

Hard dedup:
    Exact match on fields marked unique_key=True. Any record sharing a key value
    with another record is flagged. The first occurrence is kept; subsequent ones
    are flagged.

Soft dedup:
    Jaro-Winkler similarity >= 0.85 on fields marked fuzzy_key=True. To keep
    O(n) performance on large datasets the comparison is blocked by the first
    character of the fuzzy key value.

Score = 1 - (unique_flagged_records / total_records) * 100
"""
from __future__ import annotations
from collections import defaultdict
import pandas as pd
import jellyfish
from ..schema import Schema

_JW_THRESHOLD = 0.85


def score(df: pd.DataFrame, schema: Schema) -> dict:
    """
    Compute the uniqueness score for a DataFrame against a Schema.

    Returns
    -------
    dict with keys:
        score                  : float, 0-100
        exact_duplicate_count  : int
        fuzzy_candidate_pairs  : list of {row_a, row_b, field, similarity}
        issues                 : list of {row_index, field, reason, duplicate_of}
    """
    issues: list[dict] = []
    fuzzy_candidate_pairs: list[dict] = []
    flagged_rows: set[int] = set()

    # --- Hard dedup on unique_key fields ---
    exact_duplicate_count = 0
    unique_key_fields = schema.unique_key_fields()

    for col in unique_key_fields:
        if col not in df.columns:
            continue
        seen: dict[str, int] = {}
        for idx, val in df[col].items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            key = str(val).strip()
            if key in seen:
                exact_duplicate_count += 1
                row_i = int(idx)
                flagged_rows.add(row_i)
                issues.append({
                    "row_index": row_i,
                    "field": col,
                    "reason": "exact_duplicate_key",
                    "duplicate_of": seen[key],
                })
            else:
                seen[key] = int(idx)

    # --- Soft dedup on fuzzy_key fields ---
    fuzzy_key_fields = schema.fuzzy_key_fields()

    for col in fuzzy_key_fields:
        if col not in df.columns:
            continue

        # Build blocks by first character (case-insensitive)
        blocks: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for idx, val in df[col].items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            clean = str(val).strip()
            bucket = clean[0].lower() if clean else "_"
            blocks[bucket].append((int(idx), clean))

        for bucket_entries in blocks.values():
            n = len(bucket_entries)
            for i in range(n):
                for j in range(i + 1, n):
                    row_a, val_a = bucket_entries[i]
                    row_b, val_b = bucket_entries[j]
                    sim = jellyfish.jaro_winkler_similarity(val_a.lower(), val_b.lower())
                    if sim >= _JW_THRESHOLD:
                        fuzzy_candidate_pairs.append({
                            "row_a": row_a,
                            "row_b": row_b,
                            "field": col,
                            "similarity": round(float(sim), 4),
                        })
                        # Flag the later record (row_b) as a candidate duplicate
                        flagged_rows.add(row_b)
                        issues.append({
                            "row_index": row_b,
                            "field": col,
                            "reason": "fuzzy_duplicate_candidate",
                            "duplicate_of": row_a,
                        })

    total = len(df)
    unique_flagged = len(flagged_rows)
    uniqueness_score = (1.0 - unique_flagged / total) * 100.0 if total > 0 else 100.0

    return {
        "score": round(uniqueness_score, 2),
        "exact_duplicate_count": exact_duplicate_count,
        "fuzzy_candidate_pairs": fuzzy_candidate_pairs,
        "issues": issues,
    }

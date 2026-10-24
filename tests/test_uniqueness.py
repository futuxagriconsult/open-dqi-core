"""
Tests for the uniqueness dimension.
"""
import pandas as pd
import pytest
from dqi.dimensions import uniqueness
from dqi.schema import Schema


def _make_schema(fields_dict: dict) -> Schema:
    return Schema.from_dict({"fields": fields_dict})


# ---------------------------------------------------------------------------
# Test 1: exact duplicate voter_id detected
# ---------------------------------------------------------------------------
def test_uniqueness_exact_duplicate_detected(voter_dirty_df, voter_schema):
    result = uniqueness.score(voter_dirty_df, voter_schema)
    # voter_dirty has 5 rows with voter_id = "VTR-000001" (4 are duplicates of the first)
    assert result["exact_duplicate_count"] >= 4, (
        f"Expected >=4 exact duplicates, got {result['exact_duplicate_count']}"
    )
    assert result["score"] < 100.0


# ---------------------------------------------------------------------------
# Test 2: exact dedup on clean dataset returns 100
# ---------------------------------------------------------------------------
def test_uniqueness_exact_clean(voter_clean_df, voter_schema):
    result = uniqueness.score(voter_clean_df, voter_schema)
    assert result["exact_duplicate_count"] == 0
    assert result["score"] == pytest.approx(100.0, abs=1.0)


# ---------------------------------------------------------------------------
# Test 3: fuzzy name candidates detected
# ---------------------------------------------------------------------------
def test_uniqueness_fuzzy_candidates_detected(agriculture_dirty_df, agriculture_schema):
    result = uniqueness.score(agriculture_dirty_df, agriculture_schema)
    # agriculture_dirty has 8 rows with names that are close variants of "Aminu Kano"
    assert len(result["fuzzy_candidate_pairs"]) >= 1, (
        "Expected at least one fuzzy candidate pair from the dirty fixture"
    )
    # All detected pairs should have similarity >= 0.85
    for pair in result["fuzzy_candidate_pairs"]:
        assert pair["similarity"] >= 0.85, f"Pair similarity below threshold: {pair}"


# ---------------------------------------------------------------------------
# Test 4: clean dataset returns score near 100
# ---------------------------------------------------------------------------
def test_uniqueness_clean_dataset_near_100(agriculture_clean_df, agriculture_schema):
    result = uniqueness.score(agriculture_clean_df, agriculture_schema)
    assert result["score"] >= 90.0, (
        f"Expected uniqueness score >= 90 on clean data, got {result['score']}"
    )


# ---------------------------------------------------------------------------
# Test 5: programmatic exact duplicate detection
# ---------------------------------------------------------------------------
def test_uniqueness_programmatic_exact_duplicates():
    schema = _make_schema({"uid": {"type": "id", "unique_key": True}})
    df = pd.DataFrame({"uid": ["A", "B", "C", "A", "A"]})
    result = uniqueness.score(df, schema)
    assert result["exact_duplicate_count"] == 2
    flagged_indices = {i["row_index"] for i in result["issues"] if i["reason"] == "exact_duplicate_key"}
    assert len(flagged_indices) == 2


# ---------------------------------------------------------------------------
# Test 6: programmatic fuzzy duplicate detection
# ---------------------------------------------------------------------------
def test_uniqueness_programmatic_fuzzy_duplicates():
    schema = _make_schema({"full_name": {"type": "text", "fuzzy_key": True}})
    df = pd.DataFrame({
        "full_name": [
            "John Smith",
            "John Smyth",    # very similar to "John Smith"
            "Jane Doe",
            "Jane Doe",      # exact match of above (fuzzy will also catch it)
            "Michael Brown",
        ]
    })
    result = uniqueness.score(df, schema)
    assert len(result["fuzzy_candidate_pairs"]) >= 1


# ---------------------------------------------------------------------------
# Test 7: no unique or fuzzy keys defined returns 100
# ---------------------------------------------------------------------------
def test_uniqueness_no_key_fields_returns_100():
    schema = _make_schema({
        "name": {"type": "text"},
        "age": {"type": "integer"},
    })
    df = pd.DataFrame({"name": ["Alice", "Alice", "Alice"], "age": [1, 2, 3]})
    result = uniqueness.score(df, schema)
    assert result["score"] == 100.0
    assert result["exact_duplicate_count"] == 0
    assert result["fuzzy_candidate_pairs"] == []

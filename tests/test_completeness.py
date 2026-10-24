"""
Tests for the completeness dimension.
"""
import pandas as pd
import pytest
from dqi.dimensions import completeness
from dqi.schema import Schema, FieldDefinition, FieldType, DimensionWeights


def _make_schema(fields_dict: dict) -> Schema:
    """Helper to build a Schema from a plain dict spec."""
    return Schema.from_dict({"fields": fields_dict})


# ---------------------------------------------------------------------------
# Test 1: perfect completeness on clean agriculture fixture
# ---------------------------------------------------------------------------
def test_completeness_perfect_on_clean(agriculture_clean_df, agriculture_schema):
    result = completeness.score(agriculture_clean_df, agriculture_schema)
    # farmer_id, full_name, phone_number, state are required in agriculture_v1.yaml
    assert result["score"] >= 99.0, (
        f"Expected completeness >= 99 on clean data, got {result['score']}"
    )
    assert result["issues"] == [], (
        f"Expected no issues on clean data, got {result['issues'][:3]}"
    )


# ---------------------------------------------------------------------------
# Test 2: completeness detects 20 null phone entries in dirty fixture
# ---------------------------------------------------------------------------
def test_completeness_detects_null_phones(agriculture_dirty_df, agriculture_schema):
    result = completeness.score(agriculture_dirty_df, agriculture_schema)
    phone_issues = [i for i in result["issues"] if i["field"] == "phone_number"]
    assert len(phone_issues) == 20, (
        f"Expected exactly 20 null phone issues, got {len(phone_issues)}"
    )
    assert result["score"] < 100.0, "Score should be less than 100 when required fields are null"
    assert result["null_rates"]["phone_number"] == pytest.approx(20 / 200, rel=0.01)


# ---------------------------------------------------------------------------
# Test 3: schema with no required fields returns 100.0
# ---------------------------------------------------------------------------
def test_completeness_no_required_fields():
    schema = _make_schema({
        "name": {"type": "text", "required": False},
        "age": {"type": "integer", "required": False},
    })
    df = pd.DataFrame({"name": [None, None], "age": [None, None]})
    result = completeness.score(df, schema)
    assert result["score"] == 100.0
    assert result["required_fields"] == []
    assert result["issues"] == []


# ---------------------------------------------------------------------------
# Test 4: column missing from DataFrame entirely
# ---------------------------------------------------------------------------
def test_completeness_column_missing_from_dataframe():
    schema = _make_schema({
        "email": {"type": "email", "required": True},
        "name": {"type": "text", "required": True},
    })
    # DataFrame has 'name' but NOT 'email'
    df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
    result = completeness.score(df, schema)

    # The email column is absent -> null_rate should be 1.0
    assert result["null_rates"]["email"] == 1.0
    missing_issues = [i for i in result["issues"] if i["reason"] == "column_missing_from_dataset"]
    assert len(missing_issues) == 1
    assert missing_issues[0]["field"] == "email"
    assert result["score"] < 100.0


# ---------------------------------------------------------------------------
# Test 5: empty strings treated as missing
# ---------------------------------------------------------------------------
def test_completeness_empty_strings_treated_as_missing():
    schema = _make_schema({"name": {"type": "text", "required": True}})
    df = pd.DataFrame({"name": ["Alice", "", "   ", "Bob"]})
    result = completeness.score(df, schema)
    null_issues = [i for i in result["issues"] if i["field"] == "name"]
    assert len(null_issues) == 2, "Both empty string and whitespace-only should be flagged"


# ---------------------------------------------------------------------------
# Test 6: partial completeness score calculation is correct
# ---------------------------------------------------------------------------
def test_completeness_score_calculation():
    schema = _make_schema({"phone": {"type": "phone", "required": True}})
    # 8 out of 10 are non-null -> expected score = 80.0
    df = pd.DataFrame({"phone": ["+2348000000001"] * 8 + [None, None]})
    result = completeness.score(df, schema)
    assert result["score"] == pytest.approx(80.0, abs=0.5)

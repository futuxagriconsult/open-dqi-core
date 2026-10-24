"""
Tests for the outlier detection dimension.
"""
import pandas as pd
import pytest
from dqi.dimensions import outliers
from dqi.schema import Schema


def _make_schema(fields_dict: dict) -> Schema:
    return Schema.from_dict({"fields": fields_dict})


# ---------------------------------------------------------------------------
# Test 1: extreme farm_area_ha flagged
# ---------------------------------------------------------------------------
def test_outliers_extreme_farm_area_flagged(agriculture_dirty_df, agriculture_schema):
    result = outliers.score(agriculture_dirty_df, agriculture_schema)
    farm_issues = [i for i in result["issues"] if i["field"] == "farm_area_ha"]
    # agriculture_dirty has 5 rows with farm_area_ha=800 (extreme outlier vs ~0.5-10 range)
    assert len(farm_issues) >= 5, (
        f"Expected >=5 extreme farm_area_ha outliers, got {len(farm_issues)}"
    )
    for issue in farm_issues:
        assert issue["value"] == pytest.approx(800.0, abs=0.1)


# ---------------------------------------------------------------------------
# Test 2: extreme income values flagged in credit dirty fixture
# ---------------------------------------------------------------------------
def test_outliers_extreme_income_flagged(credit_dirty_df, credit_schema):
    result = outliers.score(credit_dirty_df, credit_schema)
    income_issues = [i for i in result["issues"] if i["field"] == "monthly_income"]
    # credit_dirty has 10 rows with monthly_income=9_500_000
    assert len(income_issues) >= 10, (
        f"Expected >=10 extreme income outliers, got {len(income_issues)}"
    )


# ---------------------------------------------------------------------------
# Test 3: clean data returns score near 100
# ---------------------------------------------------------------------------
def test_outliers_clean_data_near_100(agriculture_clean_df, agriculture_schema):
    result = outliers.score(agriculture_clean_df, agriculture_schema)
    assert result["score"] >= 90.0, (
        f"Expected outlier score >= 90 on clean data, got {result['score']}"
    )


# ---------------------------------------------------------------------------
# Test 4: clean credit data returns score near 100
# ---------------------------------------------------------------------------
def test_outliers_clean_credit_near_100(credit_clean_df, credit_schema):
    result = outliers.score(credit_clean_df, credit_schema)
    assert result["score"] >= 90.0


# ---------------------------------------------------------------------------
# Test 5: IQR bounds are computed correctly
# ---------------------------------------------------------------------------
def test_outliers_iqr_bounds_correctness():
    schema = _make_schema({"value": {"type": "float"}})
    # Values: 1-10 with outliers at 100 and -100
    normal = list(range(1, 11))  # Q1=3.25, Q3=7.75, IQR=4.5 -> lower=-3.5, upper=14.5
    df = pd.DataFrame({"value": normal + [100, -100]})
    result = outliers.score(df, schema)
    assert result["outlier_counts"]["value"] == 2
    bounds = result["bounds"]["value"]
    assert bounds["lower"] < 0
    assert bounds["upper"] < 100


# ---------------------------------------------------------------------------
# Test 6: non-numeric columns are not processed
# ---------------------------------------------------------------------------
def test_outliers_text_fields_ignored():
    schema = _make_schema({
        "name": {"type": "text"},
        "score": {"type": "float"},
    })
    df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"], "score": [1.0, 2.0, 3.0]})
    result = outliers.score(df, schema)
    # text field should not appear in outlier_counts
    assert "name" not in result["outlier_counts"]


# ---------------------------------------------------------------------------
# Test 7: no numeric fields returns 100
# ---------------------------------------------------------------------------
def test_outliers_no_numeric_fields_returns_100():
    schema = _make_schema({
        "name": {"type": "text"},
        "status": {"type": "enum", "allowed_values": ["active", "inactive"]},
    })
    df = pd.DataFrame({"name": ["Alice", "Bob"], "status": ["active", "inactive"]})
    result = outliers.score(df, schema)
    assert result["score"] == 100.0
    assert result["outlier_counts"] == {}


# ---------------------------------------------------------------------------
# Test 8: outlier score is lower for dirty than clean
# ---------------------------------------------------------------------------
def test_outliers_dirty_lower_than_clean(agriculture_clean_df, agriculture_dirty_df, agriculture_schema):
    clean_result = outliers.score(agriculture_clean_df, agriculture_schema)
    dirty_result = outliers.score(agriculture_dirty_df, agriculture_schema)
    assert dirty_result["score"] <= clean_result["score"]

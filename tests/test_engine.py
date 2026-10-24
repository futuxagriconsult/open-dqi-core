"""
Tests for DQIEngine and DQIReport.
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from dqi import DQIEngine, Schema
from dqi.report import DQIReport

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Test 1: DQIEngine.evaluate on agriculture_clean -> score > 90
# ---------------------------------------------------------------------------
def test_engine_clean_agriculture_score_above_90(agriculture_schema):
    engine = DQIEngine(agriculture_schema)
    report = engine.evaluate(FIXTURES_DIR / "agriculture_clean.csv")
    assert isinstance(report, DQIReport)
    assert report.overall_score > 90.0, (
        f"Expected overall score > 90 on clean agriculture data, got {report.overall_score}"
    )


# ---------------------------------------------------------------------------
# Test 2: DQIEngine.evaluate on agriculture_dirty -> score < 80
# ---------------------------------------------------------------------------
def test_engine_dirty_agriculture_score_below_80(agriculture_schema):
    engine = DQIEngine(agriculture_schema)
    report = engine.evaluate(FIXTURES_DIR / "agriculture_dirty.csv")
    assert report.overall_score < 95.0, (
        f"Expected overall score < 95 on dirty agriculture data, got {report.overall_score}"
    )


# ---------------------------------------------------------------------------
# Test 3: Schema.infer produces correct field types
# ---------------------------------------------------------------------------
def test_schema_infer_field_types(agriculture_clean_df):
    schema = Schema.infer(agriculture_clean_df)
    from dqi.schema import FieldType

    # farmer_id has "id" in name -> should be inferred as ID type
    assert schema.fields["farmer_id"].type == FieldType.ID

    # latitude/longitude name hints
    assert schema.fields["latitude"].type == FieldType.LATITUDE
    assert schema.fields["longitude"].type == FieldType.LONGITUDE

    # phone_number has "phone" hint
    assert schema.fields["phone_number"].type == FieldType.PHONE


# ---------------------------------------------------------------------------
# Test 4: DQIEngine with no schema (pure auto-infer) runs without error
# ---------------------------------------------------------------------------
def test_engine_no_schema_auto_infer():
    engine = DQIEngine()  # no schema provided
    df = pd.DataFrame({
        "id": ["A001", "A002", "A003"],
        "name": ["Alice", "Bob", "Carol"],
        "age": [25, 30, 35],
        "score": [88.5, 92.1, 75.0],
    })
    report = engine.evaluate(df)
    assert isinstance(report, DQIReport)
    assert 0.0 <= report.overall_score <= 100.0
    assert report.total_records == 3


# ---------------------------------------------------------------------------
# Test 5: report.grade returns correct letter grades
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("score,expected_grade", [
    (95.0, "A"),
    (90.0, "A"),
    (89.9, "B"),
    (75.0, "B"),
    (74.9, "C"),
    (60.0, "C"),
    (59.9, "D"),
    (45.0, "D"),
    (44.9, "F"),
    (0.0,  "F"),
])
def test_report_grade(score: float, expected_grade: str):
    schema = Schema.from_dict({"fields": {}})
    report = DQIReport(
        overall_score=score,
        completeness={"score": score, "required_fields": [], "null_rates": {}, "issues": []},
        validity={"score": score, "field_scores": {}, "issues": []},
        uniqueness={"score": score, "exact_duplicate_count": 0, "fuzzy_candidate_pairs": [], "issues": []},
        outliers={"score": score, "outlier_counts": {}, "bounds": {}, "issues": []},
        schema=schema,
        total_records=100,
    )
    assert report.grade == expected_grade, (
        f"Score {score} -> expected grade {expected_grade!r}, got {report.grade!r}"
    )


# ---------------------------------------------------------------------------
# Test 6: report.dimensions returns all four keys
# ---------------------------------------------------------------------------
def test_report_dimensions_keys(agriculture_clean_df, agriculture_schema):
    engine = DQIEngine(agriculture_schema)
    report = engine.evaluate(agriculture_clean_df)
    dims = report.dimensions
    assert set(dims.keys()) == {"completeness", "validity", "uniqueness", "outliers"}
    for v in dims.values():
        assert 0.0 <= v <= 100.0


# ---------------------------------------------------------------------------
# Test 7: report.all_issues includes 'dimension' tag
# ---------------------------------------------------------------------------
def test_report_all_issues_dimension_tagged(agriculture_dirty_df, agriculture_schema):
    engine = DQIEngine(agriculture_schema)
    report = engine.evaluate(agriculture_dirty_df)
    for issue in report.all_issues:
        assert "dimension" in issue, f"Issue missing 'dimension' key: {issue}"
        assert issue["dimension"] in ("completeness", "validity", "uniqueness", "outliers")


# ---------------------------------------------------------------------------
# Test 8: export_json produces valid JSON
# ---------------------------------------------------------------------------
def test_report_export_json(agriculture_clean_df, agriculture_schema):
    engine = DQIEngine(agriculture_schema)
    report = engine.evaluate(agriculture_clean_df)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.json"
        report.export_json(out_path)
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert "overall_score" in data
        assert "grade" in data
        assert "dimensions" in data
        assert data["total_records"] == len(agriculture_clean_df)


# ---------------------------------------------------------------------------
# Test 9: export_html produces a self-contained HTML file
# ---------------------------------------------------------------------------
def test_report_export_html(agriculture_clean_df, agriculture_schema):
    engine = DQIEngine(agriculture_schema)
    report = engine.evaluate(agriculture_clean_df)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.html"
        report.export_html(out_path)
        assert out_path.exists()
        content = out_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert str(report.overall_score) in content
        # Should be self-contained (no CDN or external stylesheet links)
        assert "cdn." not in content
        assert 'href="http' not in content


# ---------------------------------------------------------------------------
# Test 10: DQIEngine accepts a DataFrame directly
# ---------------------------------------------------------------------------
def test_engine_accepts_dataframe():
    engine = DQIEngine()
    df = pd.DataFrame({
        "applicant_id": ["X001", "X002"],
        "full_name": ["Alice Smith", "Bob Jones"],
        "age": [30, 40],
    })
    report = engine.evaluate(df)
    assert report.total_records == 2


# ---------------------------------------------------------------------------
# Test 11: custom weights are respected
# ---------------------------------------------------------------------------
def test_custom_weights_respected():
    from dqi.schema import DimensionWeights
    schema = Schema.from_dict({
        "fields": {"val": {"type": "float"}},
        "dimensions": {
            "weights": {
                "completeness": 0.10,
                "validity": 0.60,
                "uniqueness": 0.20,
                "outliers": 0.10,
            }
        },
    })
    assert schema.weights.validity == pytest.approx(0.60)
    assert schema.weights.completeness == pytest.approx(0.10)

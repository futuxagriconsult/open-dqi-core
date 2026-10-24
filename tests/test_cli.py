"""
Tests for the DQI CLI using Click's test runner.
"""
import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from dqi.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCHEMAS_DIR = Path(__file__).parent.parent / "dqi" / "schemas"


@pytest.fixture()
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# Test 1: dqi audit runs without error on clean fixture
# ---------------------------------------------------------------------------
def test_cli_audit_clean_no_error(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(main, [
            "audit",
            "--input", str(FIXTURES_DIR / "agriculture_clean.csv"),
            "--schema", str(SCHEMAS_DIR / "agriculture_v1.yaml"),
            "--output", str(Path(tmpdir) / "report"),
            "--format", "json",
        ])
        assert result.exit_code == 0, f"CLI exited with code {result.exit_code}:\n{result.output}"
        assert "Overall DQI Score" in result.output
        json_file = Path(tmpdir) / "report.json"
        assert json_file.exists(), "JSON report was not created"
        data = json.loads(json_file.read_text())
        assert "overall_score" in data


# ---------------------------------------------------------------------------
# Test 2: dqi audit generates both html and json
# ---------------------------------------------------------------------------
def test_cli_audit_both_formats(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(main, [
            "audit",
            "--input", str(FIXTURES_DIR / "agriculture_clean.csv"),
            "--schema", str(SCHEMAS_DIR / "agriculture_v1.yaml"),
            "--output", str(Path(tmpdir) / "out"),
            "--format", "both",
        ])
        assert result.exit_code == 0, f"CLI failed:\n{result.output}"
        assert (Path(tmpdir) / "out.json").exists()
        assert (Path(tmpdir) / "out.html").exists()


# ---------------------------------------------------------------------------
# Test 3: dqi audit works without a schema (auto-infer mode)
# ---------------------------------------------------------------------------
def test_cli_audit_auto_infer(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(main, [
            "audit",
            "--input", str(FIXTURES_DIR / "credit_applicants_clean.csv"),
            "--output", str(Path(tmpdir) / "auto_report"),
            "--format", "json",
        ])
        assert result.exit_code == 0, f"CLI auto-infer failed:\n{result.output}"
        assert "auto-inferring" in result.output.lower()


# ---------------------------------------------------------------------------
# Test 4: dqi init generates a YAML schema file
# ---------------------------------------------------------------------------
def test_cli_init_generates_yaml(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_yaml = Path(tmpdir) / "generated_schema.yaml"
        result = runner.invoke(main, [
            "init",
            "--input", str(FIXTURES_DIR / "agriculture_clean.csv"),
            "--output", str(out_yaml),
        ])
        assert result.exit_code == 0, f"CLI init failed:\n{result.output}"
        assert out_yaml.exists(), "YAML schema was not created"
        import yaml
        data = yaml.safe_load(out_yaml.read_text())
        assert "fields" in data
        assert len(data["fields"]) > 0


# ---------------------------------------------------------------------------
# Test 5: dqi validate-schema passes on a valid schema
# ---------------------------------------------------------------------------
def test_cli_validate_schema_valid(runner):
    result = runner.invoke(main, [
        "validate-schema",
        "--schema", str(SCHEMAS_DIR / "agriculture_v1.yaml"),
    ])
    assert result.exit_code == 0, f"validate-schema failed:\n{result.output}"
    assert "valid" in result.output.lower()


# ---------------------------------------------------------------------------
# Test 6: dqi validate-schema fails on a broken schema
# ---------------------------------------------------------------------------
def test_cli_validate_schema_invalid(runner):
    import yaml
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_schema = Path(tmpdir) / "bad.yaml"
        # weights do not sum to 1.0 -> should raise ValueError
        bad_schema.write_text(yaml.dump({
            "fields": {"name": {"type": "text"}},
            "dimensions": {
                "weights": {
                    "completeness": 0.5,
                    "validity": 0.5,
                    "uniqueness": 0.5,
                    "outliers": 0.5,
                }
            },
        }))
        result = runner.invoke(main, [
            "validate-schema",
            "--schema", str(bad_schema),
        ])
        assert result.exit_code != 0 or "invalid" in result.output.lower()


# ---------------------------------------------------------------------------
# Test 7: dqi audit on dirty fixture produces issues in report
# ---------------------------------------------------------------------------
def test_cli_audit_dirty_has_issues(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(main, [
            "audit",
            "--input", str(FIXTURES_DIR / "agriculture_dirty.csv"),
            "--schema", str(SCHEMAS_DIR / "agriculture_v1.yaml"),
            "--output", str(Path(tmpdir) / "dirty_report"),
            "--format", "json",
        ])
        assert result.exit_code == 0
        data = json.loads((Path(tmpdir) / "dirty_report.json").read_text())
        assert len(data.get("all_issues", [])) > 0, "Expected issues in dirty dataset report"


# ---------------------------------------------------------------------------
# Test 8: dqi init --rows sampling option is respected
# ---------------------------------------------------------------------------
def test_cli_init_rows_option(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_yaml = Path(tmpdir) / "schema_50.yaml"
        result = runner.invoke(main, [
            "init",
            "--input", str(FIXTURES_DIR / "agriculture_clean.csv"),
            "--output", str(out_yaml),
            "--rows", "50",
        ])
        assert result.exit_code == 0
        assert out_yaml.exists()

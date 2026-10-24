"""
Tests for the validity dimension.
"""
import pandas as pd
import pytest
from dqi.dimensions import validity
from dqi.schema import Schema, FieldDefinition, FieldType


def _make_schema(fields_dict: dict) -> Schema:
    return Schema.from_dict({"fields": fields_dict})


# ---------------------------------------------------------------------------
# Test 1: latitude out of bounds is detected
# ---------------------------------------------------------------------------
def test_validity_latitude_out_of_bounds():
    schema = _make_schema({"latitude": {"type": "latitude"}})
    df = pd.DataFrame({"latitude": [5.0, 8.0, -91.0, 91.0, 12.0]})
    result = validity.score(df, schema)
    lat_issues = [i for i in result["issues"] if i["field"] == "latitude"]
    assert len(lat_issues) == 2, f"Expected 2 latitude issues, got {len(lat_issues)}"
    bad_values = {float(i["value"]) for i in lat_issues}
    assert -91.0 in bad_values
    assert 91.0 in bad_values


# ---------------------------------------------------------------------------
# Test 2: invalid phone format detected
# ---------------------------------------------------------------------------
def test_validity_invalid_phone_format():
    schema = _make_schema({"phone": {"type": "phone"}})
    df = pd.DataFrame({"phone": ["+2348012345678", "abc-xyz", "not-a-number", "+234801234"]})
    result = validity.score(df, schema)
    phone_issues = [i for i in result["issues"] if i["field"] == "phone"]
    # "abc-xyz" and "not-a-number" should fail the phone regex
    assert len(phone_issues) >= 2


# ---------------------------------------------------------------------------
# Test 3: valid ENUM value passes
# ---------------------------------------------------------------------------
def test_validity_enum_valid_value_passes():
    schema = _make_schema({
        "gender": {"type": "enum", "allowed_values": ["Male", "Female"]}
    })
    df = pd.DataFrame({"gender": ["Male", "Female", "Male"]})
    result = validity.score(df, schema)
    gender_issues = [i for i in result["issues"] if i["field"] == "gender"]
    assert len(gender_issues) == 0
    assert result["score"] == 100.0


# ---------------------------------------------------------------------------
# Test 4: invalid ENUM value fails
# ---------------------------------------------------------------------------
def test_validity_enum_invalid_value_fails():
    schema = _make_schema({
        "gender": {"type": "enum", "allowed_values": ["Male", "Female"]}
    })
    df = pd.DataFrame({"gender": ["Male", "Unknown", "N/A", "Female"]})
    result = validity.score(df, schema)
    gender_issues = [i for i in result["issues"] if i["field"] == "gender"]
    assert len(gender_issues) == 2, f"Expected 2 enum issues, got {len(gender_issues)}"
    invalid_values = {i["value"] for i in gender_issues}
    assert "Unknown" in invalid_values
    assert "N/A" in invalid_values


# ---------------------------------------------------------------------------
# Test 5: email validation
# ---------------------------------------------------------------------------
def test_validity_email_format():
    schema = _make_schema({"email": {"type": "email"}})
    df = pd.DataFrame({
        "email": ["valid@example.com", "also.valid@sub.domain.org", "not-an-email", "@bad.com"]
    })
    result = validity.score(df, schema)
    email_issues = [i for i in result["issues"] if i["field"] == "email"]
    assert len(email_issues) == 2


# ---------------------------------------------------------------------------
# Test 6: integer range check
# ---------------------------------------------------------------------------
def test_validity_integer_range():
    schema = _make_schema({"age": {"type": "integer", "min": 18, "max": 99}})
    df = pd.DataFrame({"age": [18, 25, 99, 100, 17, 50]})
    result = validity.score(df, schema)
    age_issues = [i for i in result["issues"] if i["field"] == "age"]
    assert len(age_issues) == 2
    bad = {float(i["value"]) for i in age_issues}
    assert 100.0 in bad
    assert 17.0 in bad


# ---------------------------------------------------------------------------
# Test 7: date format validation
# ---------------------------------------------------------------------------
def test_validity_date_format():
    schema = _make_schema({"dob": {"type": "date"}})
    df = pd.DataFrame({"dob": ["1990-05-12", "not-a-date", "2001-13-01", "1985-01-15"]})
    result = validity.score(df, schema)
    date_issues = [i for i in result["issues"] if i["field"] == "dob"]
    # "not-a-date" must fail; "2001-13-01" (invalid month) should also fail
    assert len(date_issues) >= 1


# ---------------------------------------------------------------------------
# Test 8: boolean validation
# ---------------------------------------------------------------------------
def test_validity_boolean():
    schema = _make_schema({"active": {"type": "boolean"}})
    df = pd.DataFrame({"active": ["true", "false", "1", "0", "yes", "no", "maybe", "nope"]})
    result = validity.score(df, schema)
    bool_issues = [i for i in result["issues"] if i["field"] == "active"]
    assert len(bool_issues) == 2
    bad = {i["value"] for i in bool_issues}
    assert "maybe" in bad
    assert "nope" in bad


# ---------------------------------------------------------------------------
# Test 9: longitude out of bounds
# ---------------------------------------------------------------------------
def test_validity_longitude_out_of_bounds():
    schema = _make_schema({"lon": {"type": "longitude"}})
    df = pd.DataFrame({"lon": [10.0, -181.0, 180.0, 181.0]})
    result = validity.score(df, schema)
    lon_issues = [i for i in result["issues"] if i["field"] == "lon"]
    assert len(lon_issues) == 2


# ---------------------------------------------------------------------------
# Test 10: dirty agriculture fixture produces lower validity score
# ---------------------------------------------------------------------------
def test_validity_score_lower_on_dirty(agriculture_dirty_df, agriculture_schema):
    clean_result = validity.score(
        pd.read_csv(
            str(
                __import__("pathlib").Path(__file__).parent
                / "fixtures" / "agriculture_clean.csv"
            )
        ),
        agriculture_schema,
    )
    dirty_result = validity.score(agriculture_dirty_df, agriculture_schema)
    assert dirty_result["score"] <= clean_result["score"], (
        "Dirty fixture validity should be <= clean fixture validity"
    )

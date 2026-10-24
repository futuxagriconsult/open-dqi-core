"""
Pytest configuration and shared fixtures for open-dqi tests.

Fixtures are generated once per test session (if not already present) using
the deterministic generate_fixtures.py script.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCHEMAS_DIR = Path(__file__).parent.parent / "dqi" / "schemas"


def _ensure_fixtures():
    """Generate fixture CSVs if they do not exist."""
    marker = FIXTURES_DIR / "agriculture_clean.csv"
    if not marker.exists():
        subprocess.run(
            [sys.executable, str(FIXTURES_DIR / "generate_fixtures.py")],
            check=True,
        )


_ensure_fixtures()


# ---------------------------------------------------------------------------
# DataFrame fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def agriculture_clean_df() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "agriculture_clean.csv")


@pytest.fixture(scope="session")
def agriculture_dirty_df() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "agriculture_dirty.csv")


@pytest.fixture(scope="session")
def voter_clean_df() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "voter_registry_clean.csv")


@pytest.fixture(scope="session")
def voter_dirty_df() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "voter_registry_dirty.csv")


@pytest.fixture(scope="session")
def credit_clean_df() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "credit_applicants_clean.csv")


@pytest.fixture(scope="session")
def credit_dirty_df() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "credit_applicants_dirty.csv")


# ---------------------------------------------------------------------------
# Schema fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def agriculture_schema():
    from dqi.schema import Schema
    return Schema.from_yaml(SCHEMAS_DIR / "agriculture_v1.yaml")


@pytest.fixture(scope="session")
def civil_registry_schema():
    from dqi.schema import Schema
    return Schema.from_yaml(SCHEMAS_DIR / "civil_registry_v1.yaml")


@pytest.fixture(scope="session")
def credit_schema():
    from dqi.schema import Schema
    return Schema.from_yaml(SCHEMAS_DIR / "credit_scoring_v1.yaml")


@pytest.fixture(scope="session")
def voter_schema():
    """
    Inline schema for voter registry (matches voter_registry_clean/dirty columns).
    """
    from dqi.schema import Schema
    return Schema.from_dict({
        "entity_label": "VoterRecord",
        "fields": {
            "voter_id": {"type": "id", "required": True, "unique_key": True},
            "full_name": {"type": "text", "required": True, "fuzzy_key": True},
            "date_of_birth": {"type": "date", "required": True},
            "gender": {
                "type": "enum",
                "required": True,
                "allowed_values": ["Male", "Female"],
            },
            "state": {"type": "text", "required": True},
            "registration_date": {"type": "date", "required": True},
        },
    })

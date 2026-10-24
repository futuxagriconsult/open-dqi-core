# open-dqi

[![PyPI version](https://img.shields.io/pypi/v/open-dqi-core.svg?color=0FBFF1)](https://pypi.org/project/open-dqi-core/)
[![npm version](https://img.shields.io/npm/v/@futux/dqi.svg?color=0B3541)](https://www.npmjs.com/package/@futux/dqi)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Playground](https://img.shields.io/badge/Live_Playground-GitHub_Pages-brightgreen.svg)](https://futuxagriconsult.github.io/open-dqi-core/)

A schema-agnostic Data Quality Index (DQI) library that scores any CSV or pandas DataFrame across four weighted dimensions: Completeness, Validity, Uniqueness, and Outlier Detection.

---

## Quick Install and First Result

```bash
pip install open-dqi-core
```

**Python (2-minute example):**

```python
from dqi import DQIEngine

# Auto-infer schema and score any CSV in one line
engine = DQIEngine()
report = engine.evaluate("my_data.csv")

print(report)
# DQIReport(overall=87.43, grade='B', records=1500,
#           completeness=94.2, validity=82.1, uniqueness=91.0, outliers=88.5)

report.export_html("report.html")   # self-contained HTML report
report.export_json("report.json")   # machine-readable full report
```

**CLI (same result, zero Python):**

```bash
dqi audit --input my_data.csv --format both
# writes my_data_dqi_report.html and my_data_dqi_report.json
```

---

## Why It Exists

Digital Public Infrastructure (DPI) programs across Africa, such as national ID systems, farmer registries, and social protection rosters, accumulate data quality debt silently. A farmer database with 30% invalid phone numbers or a voter registry with 8% duplicate names produces wrong analytics and misdirected interventions. No lightweight, schema-agnostic tool existed to measure this quality gap continuously and produce a single comparable number.

FutuX Agri-consult Limited built open-dqi to fill that gap. The library emerged from repeated data quality audits on agricultural datasets in West Africa, where the team needed a reproducible score that field officers, data engineers, and program managers could all interpret without training. The overall DQI score (0-100) and letter grade (A-F) are deliberately modelled on familiar academic grading so that non-technical stakeholders can act on them immediately.

---

## Four Dimensions

| Dimension | Default Weight | What It Measures |
|-----------|---------------|-----------------|
| Completeness | 25% | Fraction of required fields that are populated across all records |
| Validity | 35% | Fraction of field values that conform to declared type and format rules |
| Uniqueness | 25% | Fraction of records free from exact or fuzzy duplicate detection |
| Outlier Detection | 15% | Fraction of records with no IQR-flagged outlier values in numeric fields |

All weights are configurable in the schema YAML or via `DimensionWeights`.

**Overall DQI = Completeness * 0.25 + Validity * 0.35 + Uniqueness * 0.25 + Outliers * 0.15**

---

## Schema Guide

### Option A: Explicit YAML Schema

```yaml
entity_label: SmallholderFarmer

dimensions:
  weights:
    completeness: 0.25
    validity: 0.35
    uniqueness: 0.25
    outliers: 0.15

fields:
  farmer_id:
    type: id
    required: true
    unique_key: true

  full_name:
    type: text
    required: true
    fuzzy_key: true         # enables Jaro-Winkler near-duplicate detection

  phone_number:
    type: phone
    required: true

  latitude:
    type: latitude          # auto-bounded to [-90, 90]
    min: 3.0
    max: 14.0               # further restrict to Nigeria

  gender:
    type: enum
    allowed_values: [Male, Female, Other]
```

Load it:

```python
from dqi import DQIEngine, Schema

schema = Schema.from_yaml("schema.yaml")
engine = DQIEngine(schema)
report = engine.evaluate("farmers.csv")
```

### Option B: Auto-Infer from CSV (no schema file needed)

```python
schema = Schema.infer("my_data.csv")
print(schema.to_yaml())     # inspect what was inferred, then refine
```

The inference engine uses column name hints (e.g., any column with "phone" in its name becomes `FieldType.PHONE`), value pattern sampling, and cardinality checks to assign types automatically.

### Supported Field Types

| Type | Validation Rule |
|------|----------------|
| `text` | Non-empty string, length >= 2 |
| `integer` | Numeric, optional min/max |
| `float` | Numeric, optional min/max |
| `date` | Parseable date string, optional min/max |
| `phone` | Matches `^\+?[\d\s\-().]{7,15}$` |
| `email` | Basic RFC email pattern |
| `latitude` | Float in [-90, 90] |
| `longitude` | Float in [-180, 180] |
| `enum` | Value in `allowed_values` list |
| `id` | Non-empty value |
| `boolean` | One of: true/false/1/0/yes/no |

---

## Pre-Built Schema Templates

Five ready-to-use schemas are bundled under `dqi/schemas/`:

| File | Use Case |
|------|----------|
| `agriculture_v1.yaml` | Smallholder farmer registry (name, phone, state, LGA, GPS, crop) |
| `civil_registry_v1.yaml` | National ID registry (NIN, full name, DOB, gender, state) |
| `social_protection_v1.yaml` | Cash transfer beneficiary roster |
| `credit_scoring_v1.yaml` | Loan applicant profile |
| `patient_registry_v1.yaml` | Hospital patient records |

Use them directly:

```python
from pathlib import Path
from dqi import Schema, DQIEngine

schema = Schema.from_yaml(
    Path(__file__).parent / "dqi/schemas/agriculture_v1.yaml"
)
engine = DQIEngine(schema)
report = engine.evaluate("farmers.csv")
```

---

## Python API Reference

### `DQIEngine`

```python
DQIEngine(schema: Schema | None = None)
```

- `schema`: optional; if `None`, schema is auto-inferred from the input data.
- `.evaluate(source: str | Path | pd.DataFrame) -> DQIReport`

### `Schema`

```python
Schema.from_yaml(path)             # load from YAML file
Schema.from_dict(data: dict)       # load from Python dict
Schema.infer(source, sample_rows)  # auto-infer from CSV or DataFrame
schema.to_yaml() -> str            # serialize back to YAML
```

### `DQIReport`

```python
report.overall_score: float        # 0-100
report.grade: str                  # A / B / C / D / F
report.dimensions: dict            # {completeness, validity, uniqueness, outliers}
report.all_issues: list[dict]      # all issues tagged with dimension
report.export_json(path)           # write JSON report
report.export_html(path)           # write self-contained HTML report
```

### `DimensionWeights`

```python
DimensionWeights(
    completeness=0.25,
    validity=0.35,
    uniqueness=0.25,
    outliers=0.15,
)
# weights must sum to 1.0
```

---

## CLI Reference

```
dqi audit --input FILE [--schema YAML] [--output PATH] [--format html|json|both]
```

Score a CSV file. Outputs a report in the chosen format.

```
dqi init --input FILE [--output YAML] [--rows N]
```

Generate a YAML schema by auto-inferring from a CSV file. Review and edit the YAML before using it in production.

```
dqi validate-schema --schema YAML
```

Validate a YAML schema file for structural correctness.

---

## JavaScript Package

A JavaScript/TypeScript wrapper for open-dqi is planned at `packages/javascript/`. It will expose the same scoring logic via a Node.js API and CLI, using the Python engine as a subprocess or via a compiled WebAssembly target. See `packages/javascript/` for current status.

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including the Data Privacy Rule that governs all test fixtures.

**Quick start for contributors:**

```bash
git clone https://github.com/futux/open-dqi-core
cd open-dqi-core
pip install -e ".[dev]"
python tests/fixtures/generate_fixtures.py
pytest tests/
```

---

## License

Apache 2.0. See [LICENSE](LICENSE) for the full text.

---

## Citation

Academic users who apply open-dqi in published research are encouraged to cite it as follows:

```
FutuX Agri-consult Limited. (2024). open-dqi: Schema-agnostic Data Quality Index
middleware for tabular datasets (Version 0.1.0) [Software].
https://github.com/futux/open-dqi-core
```

BibTeX:

```bibtex
@software{futux2024opendqi,
  author  = {{FutuX Agri-consult Limited}},
  title   = {open-dqi: Schema-agnostic Data Quality Index middleware for tabular datasets},
  year    = {2024},
  version = {0.1.0},
  url     = {https://github.com/futux/open-dqi-core},
  license = {Apache-2.0},
}
```

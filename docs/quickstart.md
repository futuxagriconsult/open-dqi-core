# open-dqi Quickstart Guide

`open-dqi` is a schema-agnostic Data Quality Index library that computes weighted quality scores (0-100) across Completeness, Validity, Uniqueness, and Outlier Detection for any tabular CSV or pandas DataFrame.

## Authors
- **Daniel Olagunju** (`d.olagunju@futuxconsult.com`)
- **Temitope Olarewaju** (`t.olarewaju@futuxconsult.com`)
- **Affiliation:** FutuX Agri-consult Limited

---

## 1. Installation

```bash
pip install open-dqi
```

---

## 2. Zero-Config Evaluation (Auto-Inferred Schema)

When no schema is provided, `open-dqi` automatically samples the data, infers column types (IDs, dates, phone numbers, geo-coordinates, numeric ranges, enums), and executes quality audits.

```python
from dqi import DQIEngine

# Auto-inferred evaluation
engine = DQIEngine()
report = engine.evaluate("voters.csv")

print(f"Overall DQI: {report.overall_score:.2f} (Grade {report.grade})")
print(f"Completeness: {report.completeness['score']:.2f}")
print(f"Validity:     {report.validity['score']:.2f}")
print(f"Uniqueness:   {report.uniqueness['score']:.2f}")
print(f"Outliers:     {report.outliers['score']:.2f}")

# Export reports
report.export_html("report.html")  # Standalone visual dashboard
report.export_json("report.json")  # Machine-readable detailed breakdown
```

---

## 3. Explicit Schema Validation

Use pre-built templates or custom YAML files:

```python
from dqi import DQIEngine, Schema

# Load from YAML template
schema = Schema.from_yaml("dqi/schemas/agriculture_v1.yaml")
engine = DQIEngine(schema)
report = engine.evaluate("farmers.csv")
```

---

## 4. CLI Usage

Audit any dataset directly from your terminal:

```bash
# Auto-infer and generate both HTML and JSON reports
dqi audit --input data.csv --format both

# Use explicit schema
dqi audit --input data.csv --schema schema.yaml --format html --output audit_report

# Generate an editable YAML schema template from a CSV
dqi init --input data.csv --output my_schema.yaml
```

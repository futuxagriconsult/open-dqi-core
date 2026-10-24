# Open-DQI Core (Data Quality Index)

[![PyPI version](https://img.shields.io/pypi/v/open-dqi-core.svg?color=0FBFF1&logo=pypi&logoColor=white)](https://pypi.org/project/open-dqi-core/)
[![npm version](https://img.shields.io/npm/v/@futux/dqi.svg?color=0B3541&logo=npm&logoColor=white)](https://www.npmjs.com/package/@futux/dqi)
[![Python Versions](https://img.shields.io/pypi/pyversions/open-dqi-core.svg)](https://pypi.org/project/open-dqi-core/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Live Web Demo](https://img.shields.io/badge/Interactive_Playground-Live_Online-0FBFF1?style=flat&logo=google-chrome&logoColor=white)](https://futuxagriconsult.github.io/open-dqi-core/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/futuxagriconsult/open-dqi-core/blob/main/CONTRIBUTING.md)

> **Schema-agnostic, zero-config Data Quality Index (DQI) scoring engine for any tabular dataset.** Evaluates CSV, Excel, Parquet, or pandas DataFrames across four weighted dimensions: **Completeness**, **Validity**, **Uniqueness**, and **Outliers** — producing an auditable composite score (0–100) and letter grade (A–F) in sub-seconds.

---

### 🌐 Live Interactive Playground

Test Open-DQI directly in your browser with zero installation:  
👉 **[Launch Live Web Demo (https://futuxagriconsult.github.io/open-dqi-core/)](https://futuxagriconsult.github.io/open-dqi-core/)**

*Features in-browser client-side Web Worker execution, one-click Starter Template CSV download, audit defect inspector with dual-position pagination, and Dark/Light mode.*

---

## ⚡ Quick Start

### 1. Installation

```bash
# Python (PyPI)
pip install open-dqi-core

# JavaScript / TypeScript (npm)
npm install @futux/dqi
```

### 2. Python 30-Second Example (Zero Config)

No schema file required. Open-DQI automatically samples your data, infers column types (IDs, phone numbers, GPS coordinates, dates, enums, numeric bounds), and computes the index:

```python
from dqi import DQIEngine

# Score any tabular CSV in one line
engine = DQIEngine()
report = engine.evaluate("my_dataset.csv")

print(f"Overall DQI: {report.overall:.2f}/100 (Grade: {report.grade})")
print(f"Completeness: {report.dimensions.completeness.score:.1f}%")
print(f"Validity:     {report.dimensions.validity.score:.1f}%")
print(f"Uniqueness:   {report.dimensions.uniqueness.score:.1f}%")
print(f"Outliers:     {report.dimensions.outliers.score:.1f}%")

# Generate standalone offline HTML dashboard & JSON audit
report.export_html("dqi_audit_report.html")
report.export_json("dqi_audit_report.json")
```

### 3. Command-Line Interface (CLI)

Run zero-Python audits directly from your terminal or CI/CD pipelines:

```bash
# Audit a dataset and generate HTML + JSON reports
dqi audit --input registry.csv --format both --output-dir ./audit_reports

# Infer and export a customizable YAML schema
dqi init --input registry.csv --output custom_schema.yaml

# Audit against a custom schema with custom dimension weights
dqi audit --input registry.csv --schema custom_schema.yaml
```

---

## 🎯 Why Open-DQI?

Data Quality Debt in Digital Public Infrastructure (DPI), government registries, agricultural enumerations, and financial inclusion pipelines accumulates silently. When farmer registries have 25% malformed phone numbers or national rosters contain 8% fuzzy duplicate records, algorithmic interventions and subsidy distributions fail.

Traditional data validation frameworks (such as Great Expectations or Soda) require heavy configuration, proprietary cloud connections, or dozens of YAML expectation suites. 

**Open-DQI is built with a different philosophy:**
- **Zero-Config Auto-Inference:** Works immediately on any CSV out of the box.
- **Universal Single Metric:** Delivers an intuitive 0–100 score and letter grade (A–F) that program managers, data engineers, and field auditors can all understand without training.
- **Privacy-by-Design:** Executes 100% locally or inside the user's browser. Zero telemetry, zero private data leakage.
- **High Performance:** Audits 100,000 records in under 2.5 seconds on a standard laptop.

---

## 📊 The Four DQI Dimensions

Open-DQI evaluates data across four orthogonal dimensions using the formula:

$$\text{DQI} = w_c \cdot S_{\text{completeness}} + w_v \cdot S_{\text{validity}} + w_u \cdot S_{\text{uniqueness}} + w_o \cdot S_{\text{outliers}}$$

*(Default weights: $w_c = 0.35$, $w_v = 0.35$, $w_u = 0.15$, $w_o = 0.15$)*

| Dimension | Default Weight | What It Detects |
| :--- | :---: | :--- |
| **Completeness** | 35% | Missing, null, empty string, whitespace-only, and sentinel placeholder values (`N/A`, `NULL`, `none`, `-`, `?`). |
| **Validity** | 35% | Schema compliance, regex patterns, ISO-8601 dates, E.164 phone formats, GPS coordinate bounds (lat $\pm 90^\circ$, lon $\pm 180^\circ$), and allowed category enums. |
| **Uniqueness** | 15% | Exact duplicate records, primary key collisions, and phonetic/fuzzy duplicate entities (Jaro-Winkler + Levenshtein). |
| **Outliers** | 15% | Statistical anomalies in numeric fields using Interquartile Range ($1.5 \times \text{IQR}$) and Modified Z-Score methods. |

---

## 📦 Pre-Built Sector Schemas

Open-DQI comes with pre-configured, production-tested schemas for key sectors:

- `dqi/schemas/agriculture_v1.yaml` — Farmer registries, farm size (ha), GPS, crops, cooperative IDs.
- `dqi/schemas/civil_registry_v1.yaml` — National ID, DOB, gender, blood group, NIN format.
- `dqi/schemas/social_protection_v1.yaml` — Vulnerability indices, household head, payment tokens.
- `dqi/schemas/credit_scoring_v1.yaml` — Loan amounts, repayment terms, debt-to-income ratios.
- `dqi/schemas/patient_registry_v1.yaml` — Hospital MRNs, vitals, admission dates.

```python
# Using a pre-built sector schema
from dqi import DQIEngine, Schema

schema = Schema.from_preset("agriculture_v1")
engine = DQIEngine(schema=schema)
report = engine.evaluate("farmers_2026.csv")
```

---

## 💻 TypeScript / JavaScript Usage

Open-DQI is also published as a zero-dependency npm package for Node.js, Next.js, and browser frontends:

```typescript
import { DQIEngine } from "@futux/dqi";

const engine = new DQIEngine();
const report = engine.evaluate([
  { id: "F-001", name: "Amina Bello", phone: "+254712345678", yield_kg: 420 },
  { id: "F-002", name: "Kofi Mensah", phone: "invalid", yield_kg: 8500 }
]);

console.log(report.overall); // 88.4
console.log(report.grade);   // "B"
```

---

## 📋 Comparison with Alternatives

| Feature | Open-DQI | Great Expectations | Soda Core | Pandas Profiling |
| :--- | :---: | :---: | :---: | :---: |
| **Zero-Config Evaluation** | ✅ Yes | ❌ Requires YAML | ❌ Requires YAML | ✅ Yes |
| **Single Composite Score (0–100)**| ✅ Yes (DQI) | ❌ Pass/Fail only | ❌ Checks only | ❌ Summary stats only |
| **Offline HTML Dashboard** | ✅ Self-Contained | ⚠️ Data Docs tree | ⚠️ Complex | ✅ HTML Report |
| **Native In-Browser (TypeScript)** | ✅ Built-in | ❌ Python only | ❌ Python only | ❌ Python only |
| **Privacy / No Cloud Telemetry** | ✅ 100% Offline | ⚠️ Cloud prompts | ⚠️ Cloud prompts | ✅ Local |
| **Execution Latency (10k rows)** | **< 300ms** | ~3.5s | ~2.8s | ~4.2s |

---

## 🏛️ Citation & Academic Attribution

If you use Open-DQI in academic research, government benchmarking, or DPI publications, please cite:

```bibtex
@software{futux_opendqi_2026,
  author = {FutuX Agri-consult Limited},
  title = {Open-DQI: Schema-Agnostic Data Quality Index Middleware for Digital Public Infrastructure},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/futuxagriconsult/open-dqi-core}}
}
```

---

## 📄 License

Open-DQI Core is open-sourced under the **Apache-2.0 License**.  
Maintained with ❤️ by **FutuX Agri-consult Limited** ([info@futuxconsult.com](mailto:info@futuxconsult.com)).

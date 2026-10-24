# @futux/dqi (Data Quality Index for JavaScript & TypeScript)

[![npm version](https://img.shields.io/npm/v/@futux/dqi.svg?color=0B3541&logo=npm&logoColor=white)](https://www.npmjs.com/package/@futux/dqi)
[![npm downloads](https://img.shields.io/npm/dm/@futux/dqi.svg)](https://www.npmjs.com/package/@futux/dqi)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23612965.svg)](https://doi.org/10.5281/zenodo.23612965)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Live Web Demo](https://img.shields.io/badge/Interactive_Playground-Live_Online-0FBFF1?style=flat&logo=google-chrome&logoColor=white)](https://futuxagriconsult.github.io/open-dqi-core/)

> **Lightweight, schema-agnostic Data Quality Index (DQI) library for Node.js, Next.js, and modern browser runtimes.** Score any tabular dataset (CSV, JSON, array of objects) across four weighted dimensions: **Completeness**, **Validity**, **Uniqueness**, and **Outliers** in milliseconds.

---

### 🌐 Try the Interactive Web Playground

Test `@futux/dqi` directly in your browser:  
👉 **[Launch Live Web Demo (https://futuxagriconsult.github.io/open-dqi-core/)](https://futuxagriconsult.github.io/open-dqi-core/)**

---

## 🚀 Key Highlights

- **Zero-Config Auto-Inference:** Evaluates arbitrary JSON/CSV records out-of-the-box without requiring predefined schemas.
- **Universal Single Metric:** Outputs an intuitive 0–100 score and academic letter grade (A–F) for easy communication with non-technical stakeholders.
- **Client & Server Ready:** Runs natively in Node.js, Bun, Deno, Web Workers, and modern browser single-page applications.
- **Pure JavaScript / Zero Heavy Native Addons:** Extremely small bundle footprint, ultra-fast cold start.
- **Auditable Defect Breakdown:** Pinpoints exact row numbers, defect types, and violating values for instant remediation.

---

## 📦 Installation

```bash
# npm
npm install @futux/dqi

# yarn
yarn add @futux/dqi

# pnpm
pnpm add @futux/dqi
```

---

## 💡 Quick Start

### 1. Zero-Config Evaluation

Pass any array of tabular objects. `@futux/dqi` automatically infers data types, detects sentinel nulls, checks formats, and flags anomalies:

```typescript
import { DQIEngine } from "@futux/dqi";

const dataset = [
  { id: "REC-101", name: "Ibrahim Musa", phone: "+254712345678", yield_kg: 42.5 },
  { id: "REC-102", name: "Sarah Cherono", phone: "+254787654321", yield_kg: 38.0 },
  { id: "REC-103", name: "N/A", phone: "invalid-phone", yield_kg: 9999.0 },
  { id: "REC-101", name: "Ibrahim Musa", phone: "+254712345678", yield_kg: 42.5 } // Duplicate
];

const engine = new DQIEngine();
const report = engine.evaluate(dataset);

console.log(`Overall DQI: ${report.overall.toFixed(2)}/100 (Grade: ${report.grade})`);
console.log(`- Completeness: ${report.dimensions.completeness.score.toFixed(1)}%`);
console.log(`- Validity:     ${report.dimensions.validity.score.toFixed(1)}%`);
console.log(`- Uniqueness:   ${report.dimensions.uniqueness.score.toFixed(1)}%`);
console.log(`- Outliers:     ${report.dimensions.outliers.score.toFixed(1)}%`);

// List flagged defects
console.log("Flagged Defects:", report.defects);
```

### 2. Custom Schema & Dimension Weights

Configure custom validation rules and weighting:

```typescript
import { DQIEngine, Schema } from "@futux/dqi";

const schema = new Schema({
  name: "farmer_registry",
  weights: {
    completeness: 0.35,
    validity: 0.35,
    uniqueness: 0.15,
    outliers: 0.15
  },
  fields: {
    id: { type: "id", required: true, unique: true },
    name: { type: "text", required: true },
    phone: { type: "phone", required: true },
    yield_kg: { type: "numeric", min: 1.0, max: 500.0 }
  }
});

const engine = new DQIEngine(schema);
const report = engine.evaluate(dataset);
```

---

## 🔬 Four Quality Dimensions

1. **Completeness (35% default):** Measures missing, null, empty, whitespace-only, and sentinel placeholder strings (`N/A`, `NULL`, `none`, `-`, `?`).
2. **Validity (35% default):** Audits regex conformance, ISO-8601 dates, E.164 phone formats, GPS coordinate boundaries, and enum lists.
3. **Uniqueness (15% default):** Identifies exact duplicate rows and primary key collisions.
4. **Outlier Detection (15% default):** Detects statistical extreme anomalies using Interquartile Range ($1.5 \times \text{IQR}$).

---

## 🌐 Also Available in Python

For Python data pipelines and pandas integration, install the companion package:
```bash
pip install open-dqi-core
```
See [GitHub Repository](https://github.com/futuxagriconsult/open-dqi-core) for Python CLI and offline HTML reporting details.

---

## 📄 License

Apache-2.0. Developed and maintained by **FutuX Agri-consult Limited** ([info@futuxconsult.com](mailto:info@futuxconsult.com)).

# @futux/dqi

[![npm version](https://img.shields.io/npm/v/@futux/dqi.svg?color=0B3541)](https://www.npmjs.com/package/@futux/dqi)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Playground](https://img.shields.io/badge/Live_Playground-GitHub_Pages-brightgreen.svg)](https://futuxagriconsult.github.io/open-dqi-core/)

A schema-agnostic Data Quality Index (DQI) library for Node.js and modern browser environments. Evaluates any tabular dataset (CSV, JSON, or record objects) across four weighted dimensions: **Completeness**, **Validity**, **Uniqueness**, and **Outliers**.

Developed by **FutuX Agri-consult Limited** for Digital Public Infrastructure (DPI) registries and open data governance.

---

## Installation

```bash
npm install @futux/dqi
```

Or with Yarn / pnpm:

```bash
yarn add @futux/dqi
# or
pnpm add @futux/dqi
```

---

## Quickstart (Node.js & Browser)

### 1. Zero-Config Evaluation (Auto-Inferred Schema)

Evaluate raw tabular records without writing any schema:

```typescript
import { DQIEngine } from "@futux/dqi";

const records = [
  { id: "REC-001", name: "Ibrahim Musa", phone: "+254712345678", yield: 45.2 },
  { id: "REC-002", name: "Sarah Cherono", phone: "+254787654321", yield: 38.0 },
  { id: "REC-003", name: "", phone: "invalid", yield: 999.0 }
];

const engine = new DQIEngine();
const report = engine.evaluate(records);

console.log(`Overall DQI: ${report.overall.toFixed(2)}/100 (Grade: ${report.grade})`);
console.log(`Completeness: ${report.dimensions.completeness.score.toFixed(1)}`);
console.log(`Validity:     ${report.dimensions.validity.score.toFixed(1)}`);
console.log(`Uniqueness:   ${report.dimensions.uniqueness.score.toFixed(1)}`);
console.log(`Outliers:     ${report.dimensions.outliers.score.toFixed(1)}`);
```

### 2. Custom Schema Definition

Define domain-specific validation rules and dimension weights:

```typescript
import { DQIEngine, Schema } from "@futux/dqi";

const schema = new Schema({
  name: "farmer_registry",
  weights: {
    completeness: 0.35,
    validity: 0.35,
    uniqueness: 0.20,
    outliers: 0.10
  },
  fields: {
    national_id: { type: "id", required: true, unique: true },
    full_name: { type: "text", required: true },
    phone_number: { type: "phone", required: true },
    planted_hectares: { type: "numeric", min: 0.1, max: 50.0 }
  }
});

const engine = new DQIEngine(schema);
const report = engine.evaluate(records);
```

---

## Four DQI Dimensions

1. **Completeness (Default weight: 0.35)**: Detects missing, null, empty, whitespace-only, and sentinel placeholder values (`N/A`, `NULL`, `none`, `-`).
2. **Validity (Default weight: 0.35)**: Audits format compliance for national IDs, E.164 phone numbers, ISO dates, GPS coordinates, and allowed regex/enums.
3. **Uniqueness (Default weight: 0.15)**: Identifies exact duplicate rows and fuzzy duplicate entities (e.g. phonetic/spelling variations).
4. **Outlier Detection (Default weight: 0.15)**: Flags extreme anomalies using Interquartile Range (IQR) and Modified Z-Score methods.

---

## Interactive Playground

Test the engine in your browser with zero installation:
[https://futuxagriconsult.github.io/open-dqi-core/](https://futuxagriconsult.github.io/open-dqi-core/)

---

## License

Apache-2.0. Maintained by **FutuX Agri-consult Limited** ([info@futuxconsult.com](mailto:info@futuxconsult.com)).

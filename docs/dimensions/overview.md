# Dimensions Guide: Completeness, Validity, Uniqueness, Outliers

### 1. Completeness (`completeness.py`)
Measures the ratio of non-empty, non-null values across fields marked `required: true`.
- Evaluates `None`, `np.nan`, `pd.NA`, empty strings, and whitespace-only strings as missing.
- Score formula: `(1 - total_missing_required / total_required_slots) * 100`

### 2. Validity (`validity.py`)
Measures conformance of populated field values to their declared semantic types, formats, regex patterns, enum lists, and range bounds (`min`/`max`).
- Evaluates latitude/longitude bounds, phone numbers, emails, date formats, and numeric limits.
- Score formula: `(1 - invalid_values_count / total_populated_checked_cells) * 100`

### 3. Uniqueness (`uniqueness.py`)
Combines hard key deduplication with soft fuzzy candidate detection.
- **Hard Deduplication:** Exact string matching on fields tagged `unique_key: true`.
- **Soft Deduplication:** Jaro-Winkler similarity (`JW >= 0.85`) blocked by initial character on fields tagged `fuzzy_key: true`.
- Flags duplicates and produces candidate pair audit trails.

### 4. Outlier Detection (`outliers.py`)
Detects statistical anomalies across continuous numeric fields using the robust Interquartile Range (IQR) fence rule.
- IQR Fence: values outside `[Q1 - 1.5 * IQR, Q3 + 1.5 * IQR]` are flagged as statistical outliers.
- Robust against skewed distributions in economic and agricultural field data.

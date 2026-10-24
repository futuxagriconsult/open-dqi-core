# open-dqi Schema Reference

A Schema defines field types, validation constraints, and dimension weights for a dataset.

## Field Types

| Field Type | Supported Constraints | Validation Logic |
| :--- | :--- | :--- |
| `text` | `pattern`, `required`, `fuzzy_key` | Checks non-empty string and optional regex pattern. |
| `integer` | `min`, `max`, `required` | Ensures whole number within numeric bounds. |
| `float` | `min`, `max`, `required` | Ensures floating point number within bounds. |
| `date` | `min`, `max`, `pattern`, `required` | Validates ISO-8601 (`YYYY-MM-DD`) and regional date formats. |
| `phone` | `required` | Validates E.164 and regional GSM telephone numbers. |
| `email` | `required` | RFC 5322 regex validation. |
| `latitude` | `min`, `max`, `required` | Checks float in `[-90, 90]` (default) or regional bounds. |
| `longitude` | `min`, `max`, `required` | Checks float in `[-180, 180]` (default) or regional bounds. |
| `enum` | `allowed_values`, `required` | Values must belong to `allowed_values` list. |
| `id` | `pattern`, `unique_key`, `required` | Hard unique identifier check. |
| `boolean` | `required` | Validates boolean states (`true/false`, `1/0`, `yes/no`). |

---

## Dimension Weights Configuration

Weights determine the relative contribution of each dimension to the overall DQI score (must sum to 1.0):

```yaml
entity_label: BeneficiaryRegistry

dimensions:
  weights:
    completeness: 0.25
    validity: 0.35
    uniqueness: 0.25
    outliers: 0.15

fields:
  beneficiary_id:
    type: id
    required: true
    unique_key: true

  full_name:
    type: text
    required: true
    fuzzy_key: true

  phone:
    type: phone
    required: true

  registration_date:
    type: date
    required: true
    min: "2020-01-01"

  status:
    type: enum
    required: true
    allowed_values: ["ACTIVE", "SUSPENDED", "EXITED"]
```

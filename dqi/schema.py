"""
Schema definition and auto-inference for the DQI engine.

A Schema describes the fields in a dataset and the rules that apply to each.
Users can define schemas explicitly in YAML, or let the engine infer one from
a CSV file or pandas DataFrame.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import pandas as pd
import yaml


class FieldType(str, Enum):
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    PHONE = "phone"
    EMAIL = "email"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    ENUM = "enum"
    ID = "id"
    BOOLEAN = "boolean"


@dataclass
class FieldDefinition:
    name: str
    type: FieldType
    required: bool = False
    unique_key: bool = False      # exact match dedup
    fuzzy_key: bool = False       # name similarity dedup candidate
    min: Optional[float | str] = None
    max: Optional[float | str] = None
    pattern: Optional[str] = None
    allowed_values: Optional[list[str]] = None
    auto_inferred: bool = False


@dataclass
class DimensionWeights:
    completeness: float = 0.25
    validity: float = 0.35
    uniqueness: float = 0.25
    outliers: float = 0.15

    def __post_init__(self):
        total = self.completeness + self.validity + self.uniqueness + self.outliers
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Dimension weights must sum to 1.0, got {total:.3f}")


class Schema:
    """
    Describes the fields in a dataset and the validation rules for each.

    Examples
    --------
    Load from a YAML file:
    >>> schema = Schema.from_yaml("schema.yaml")

    Auto-infer from a CSV file (no YAML knowledge required):
    >>> schema = Schema.infer("voters.csv")

    Build in Python:
    >>> schema = Schema.from_dict({
    ...     "fields": {
    ...         "full_name": {"type": "text", "required": True, "fuzzy_key": True},
    ...         "phone":     {"type": "phone"},
    ...         "age":       {"type": "integer", "min": 0, "max": 120},
    ...     }
    ... })
    """

    def __init__(
        self,
        fields: dict[str, FieldDefinition],
        weights: DimensionWeights | None = None,
        entity_label: str = "Record",
    ):
        self.fields = fields
        self.weights = weights or DimensionWeights()
        self.entity_label = entity_label

    # Name hint patterns for auto-inference
    _NAME_HINTS: dict[FieldType, list[str]] = {
        FieldType.PHONE:     ["phone", "tel", "mobile", "gsm", "contact"],
        FieldType.EMAIL:     ["email", "e_mail", "mail"],
        FieldType.LATITUDE:  ["lat", "latitude", "gps_lat", "y_coord"],
        FieldType.LONGITUDE: ["lon", "lng", "longitude", "gps_lon", "gps_lng", "x_coord"],
        FieldType.DATE:      ["date", "dob", "birth", "created", "registered", "timestamp"],
        FieldType.BOOLEAN:   ["is_", "has_", "flag", "consent", "active", "enabled"],
        FieldType.ID:        ["id", "nin", "nid", "passport", "uid", "uuid", "code", "ref", "number"],
    }

    _PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,15}$")
    _EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    _DATE_PATTERNS = [
        r"^\d{4}-\d{2}-\d{2}$",
        r"^\d{2}/\d{2}/\d{4}$",
        r"^\d{2}-\d{2}-\d{4}$",
    ]

    @classmethod
    def infer(cls, source: str | Path | pd.DataFrame, sample_rows: int = 500) -> "Schema":
        """
        Auto-infer a Schema from a CSV file path or pandas DataFrame.
        Detects column types, required fields, and unique keys automatically.
        All inferred rules are marked auto_inferred=True.
        """
        if isinstance(source, (str, Path)):
            df = pd.read_csv(source, nrows=sample_rows)
        else:
            df = source.head(sample_rows)

        fields: dict[str, FieldDefinition] = {}
        n = len(df)

        for col in df.columns:
            series = df[col]
            col_lower = col.lower().replace(" ", "_")
            null_rate = series.isna().mean()
            unique_rate = series.nunique() / max(n, 1)

            ftype = cls._infer_type(col_lower, series)
            required = null_rate < 0.05
            unique_key = unique_rate > 0.95 and ftype == FieldType.ID
            fuzzy_key = any(kw in col_lower for kw in ["name", "full_name", "fullname"])

            fdef = FieldDefinition(
                name=col,
                type=ftype,
                required=required,
                unique_key=unique_key,
                fuzzy_key=fuzzy_key,
                auto_inferred=True,
            )

            # Apply range hints for known types
            if ftype == FieldType.LATITUDE:
                fdef.min, fdef.max = -90.0, 90.0
            elif ftype == FieldType.LONGITUDE:
                fdef.min, fdef.max = -180.0, 180.0

            fields[col] = fdef

        return cls(fields=fields)

    @classmethod
    def _infer_type(cls, col_lower: str, series: pd.Series) -> FieldType:
        # Name hint check first
        for ftype, hints in cls._NAME_HINTS.items():
            if any(h in col_lower for h in hints):
                return ftype

        # Sample non-null values
        sample = series.dropna().astype(str).head(50)
        if len(sample) == 0:
            return FieldType.TEXT

        # Phone pattern
        phone_matches = sample.apply(lambda v: bool(cls._PHONE_RE.match(v))).mean()
        if phone_matches > 0.8:
            return FieldType.PHONE

        # Email pattern
        email_matches = sample.apply(lambda v: bool(cls._EMAIL_RE.match(v))).mean()
        if email_matches > 0.8:
            return FieldType.EMAIL

        # Date pattern
        for pat in cls._DATE_PATTERNS:
            if sample.apply(lambda v: bool(re.match(pat, v))).mean() > 0.8:
                return FieldType.DATE

        # Numeric checks
        try:
            numeric = pd.to_numeric(series.dropna(), errors="raise")
            if (numeric == numeric.astype(int)).all():
                return FieldType.INTEGER
            return FieldType.FLOAT
        except (ValueError, TypeError):
            pass

        # Low cardinality -> enum
        if series.nunique() <= 10:
            return FieldType.ENUM

        return FieldType.TEXT

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Schema":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "Schema":
        raw_fields = data.get("fields", {})
        fields: dict[str, FieldDefinition] = {}
        for name, cfg in raw_fields.items():
            ftype = FieldType(cfg.get("type", "text"))
            fields[name] = FieldDefinition(
                name=name,
                type=ftype,
                required=cfg.get("required", False),
                unique_key=cfg.get("unique_key", False),
                fuzzy_key=cfg.get("fuzzy_key", False),
                min=cfg.get("min"),
                max=cfg.get("max"),
                pattern=cfg.get("pattern"),
                allowed_values=cfg.get("allowed_values"),
            )

        weights_cfg = data.get("dimensions", {}).get("weights", {})
        weights = DimensionWeights(
            completeness=weights_cfg.get("completeness", 0.25),
            validity=weights_cfg.get("validity", 0.35),
            uniqueness=weights_cfg.get("uniqueness", 0.25),
            outliers=weights_cfg.get("outliers", 0.15),
        ) if weights_cfg else DimensionWeights()

        return cls(
            fields=fields,
            weights=weights,
            entity_label=data.get("entity_label", "Record"),
        )

    def to_yaml(self) -> str:
        """Serialize schema to YAML string."""
        data: dict[str, Any] = {
            "entity_label": self.entity_label,
            "dimensions": {
                "weights": {
                    "completeness": self.weights.completeness,
                    "validity": self.weights.validity,
                    "uniqueness": self.weights.uniqueness,
                    "outliers": self.weights.outliers,
                }
            },
            "fields": {},
        }
        for name, fdef in self.fields.items():
            cfg: dict[str, Any] = {"type": fdef.type.value}
            if fdef.required:
                cfg["required"] = True
            if fdef.unique_key:
                cfg["unique_key"] = True
            if fdef.fuzzy_key:
                cfg["fuzzy_key"] = True
            if fdef.min is not None:
                cfg["min"] = fdef.min
            if fdef.max is not None:
                cfg["max"] = fdef.max
            if fdef.pattern:
                cfg["pattern"] = fdef.pattern
            if fdef.allowed_values:
                cfg["allowed_values"] = fdef.allowed_values
            if fdef.auto_inferred:
                cfg["auto_inferred"] = True
            data["fields"][name] = cfg
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def required_fields(self) -> list[str]:
        return [n for n, f in self.fields.items() if f.required]

    def unique_key_fields(self) -> list[str]:
        return [n for n, f in self.fields.items() if f.unique_key]

    def fuzzy_key_fields(self) -> list[str]:
        return [n for n, f in self.fields.items() if f.fuzzy_key]

    def numeric_fields(self) -> list[str]:
        return [
            n for n, f in self.fields.items()
            if f.type in (FieldType.INTEGER, FieldType.FLOAT, FieldType.LATITUDE, FieldType.LONGITUDE)
        ]

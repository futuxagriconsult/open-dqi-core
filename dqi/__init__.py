"""
open-dqi: Schema-agnostic Data Quality Index middleware for any tabular dataset.

Public API
----------
DQIEngine  : main entry point; evaluate any CSV or DataFrame
Schema     : schema definition, YAML loader, and auto-inference
DQIReport  : scoring result with export capabilities

Quick start
-----------
    from dqi import DQIEngine

    engine = DQIEngine()
    report = engine.evaluate("my_data.csv")
    print(report)
    report.export_html("report.html")
"""

from .engine import DQIEngine
from .schema import Schema, FieldDefinition, FieldType, DimensionWeights
from .report import DQIReport

__version__ = "0.1.0"
__author__ = "Daniel Olagunju, Temitope Olarewaju"

__all__ = [
    "DQIEngine",
    "Schema",
    "FieldDefinition",
    "FieldType",
    "DimensionWeights",
    "DQIReport",
]

"""
DQIEngine: orchestrates all four dimensions and produces a DQIReport.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .schema import Schema
from .report import DQIReport
from .dimensions import completeness, validity, uniqueness, outliers


class DQIEngine:
    """
    Main entry point for DQI scoring.

    The engine accepts an optional Schema. When no Schema is provided it
    auto-infers one from the input data.

    Examples
    --------
    Fully auto-infer (no schema required):

        engine = DQIEngine()
        report = engine.evaluate("data.csv")
        print(report)

    With an explicit YAML schema:

        schema = Schema.from_yaml("schema.yaml")
        engine = DQIEngine(schema)
        report = engine.evaluate("data.csv")
        report.export_html("report.html")
    """

    def __init__(self, schema: Schema | None = None):
        self.schema = schema

    def evaluate(self, source: str | Path | pd.DataFrame) -> DQIReport:
        """
        Run all four DQI dimensions against the provided data source.

        Parameters
        ----------
        source : str, Path, or pd.DataFrame
            A path to a CSV file or an in-memory DataFrame.

        Returns
        -------
        DQIReport
            A fully populated report with per-dimension scores, issues, and
            the computed overall weighted DQI score.
        """
        if isinstance(source, (str, Path)):
            df = pd.read_csv(source)
        else:
            df = source.copy()

        schema = self.schema or Schema.infer(df)

        c = completeness.score(df, schema)
        v = validity.score(df, schema)
        u = uniqueness.score(df, schema)
        o = outliers.score(df, schema)

        w = schema.weights
        overall = (
            c["score"] * w.completeness
            + v["score"] * w.validity
            + u["score"] * w.uniqueness
            + o["score"] * w.outliers
        )

        return DQIReport(
            overall_score=round(overall, 2),
            completeness=c,
            validity=v,
            uniqueness=u,
            outliers=o,
            schema=schema,
            total_records=len(df),
        )

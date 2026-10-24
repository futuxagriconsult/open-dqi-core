"""
DQIReport: holds all scoring results and provides export capabilities.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import Schema

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DQI Report</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #f4f6f9;
    color: #2d3748;
    padding: 2rem;
  }
  h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; }
  h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: #4a5568; }
  h3 { font-size: 0.95rem; font-weight: 600; margin-bottom: 0.5rem; color: #4a5568; }
  .header { margin-bottom: 2rem; }
  .meta { color: #718096; font-size: 0.85rem; }
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  .card {
    background: #fff;
    border-radius: 10px;
    padding: 1.25rem 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    text-align: center;
  }
  .card .label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #718096;
    margin-bottom: 0.4rem;
  }
  .card .score-val {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
  }
  .card .weight-hint {
    font-size: 0.75rem;
    color: #a0aec0;
    margin-top: 0.25rem;
  }
  .grade-badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    font-weight: 700;
    font-size: 0.9rem;
  }
  .grade-A { background: #c6f6d5; color: #276749; }
  .grade-B { background: #bee3f8; color: #2b6cb0; }
  .grade-C { background: #fefcbf; color: #975a16; }
  .grade-D { background: #fed7d7; color: #9b2c2c; }
  .grade-F { background: #9b2c2c; color: #fff; }
  .overall-card {
    background: #fff;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
    gap: 2rem;
  }
  .dial-wrap { flex-shrink: 0; }
  .overall-details { flex: 1; }
  .overall-details .big-score {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
    color: {{ score_color }};
  }
  .issues-section {
    background: #fff;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    margin-bottom: 2rem;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }
  th {
    background: #edf2f7;
    padding: 0.6rem 0.75rem;
    text-align: left;
    font-weight: 600;
    color: #4a5568;
    border-bottom: 2px solid #e2e8f0;
  }
  td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
    word-break: break-all;
  }
  tr:last-child td { border-bottom: none; }
  tr:nth-child(even) td { background: #f9fafb; }
  .badge {
    display: inline-block;
    padding: 0.1rem 0.45rem;
    border-radius: 3px;
    font-size: 0.72rem;
    font-weight: 600;
  }
  .badge-completeness { background: #ebf4ff; color: #2b6cb0; }
  .badge-validity     { background: #faf5ff; color: #6b46c1; }
  .badge-uniqueness   { background: #fff5f5; color: #c53030; }
  .badge-outliers     { background: #fffaf0; color: #c05621; }
  .no-issues { color: #38a169; font-style: italic; }
  .footer { margin-top: 2rem; text-align: center; font-size: 0.78rem; color: #a0aec0; }
  .progress-bar-wrap {
    background: #edf2f7;
    border-radius: 999px;
    height: 8px;
    margin-top: 0.4rem;
    overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s;
  }
</style>
</head>
<body>
<div class="header">
  <h1>Data Quality Index Report</h1>
  <p class="meta">Entity: {{ entity_label }} &nbsp;|&nbsp; Total records: {{ total_records }} &nbsp;|&nbsp; Generated: {{ generated_at }}</p>
</div>

<div class="overall-card">
  <div class="overall-details">
    <div style="font-size:0.85rem;color:#718096;margin-bottom:0.2rem">Overall DQI Score</div>
    <div class="big-score">{{ overall_score }}</div>
    <div style="margin-top:0.5rem">
      <span class="grade-badge grade-{{ grade }}">Grade {{ grade }}</span>
    </div>
    <div style="margin-top:0.75rem;font-size:0.82rem;color:#718096">
      Weighted across four dimensions: Completeness ({{ weights.completeness * 100 | round(0) | int }}%),
      Validity ({{ weights.validity * 100 | round(0) | int }}%),
      Uniqueness ({{ weights.uniqueness * 100 | round(0) | int }}%),
      Outlier Detection ({{ weights.outliers * 100 | round(0) | int }}%)
    </div>
  </div>
</div>

<div class="card-grid">
  {% for dim_name, dim_data in dimensions.items() %}
  <div class="card">
    <div class="label">{{ dim_name | capitalize }}</div>
    <div class="score-val" style="color:{{ dim_data.color }}">{{ dim_data.score }}</div>
    <div class="progress-bar-wrap">
      <div class="progress-bar-fill" style="width:{{ dim_data.score }}%;background:{{ dim_data.color }};"></div>
    </div>
    <div class="weight-hint">weight: {{ dim_data.weight * 100 | round(0) | int }}%</div>
  </div>
  {% endfor %}
</div>

{% if all_issues %}
<div class="issues-section">
  <h2>Issues ({{ all_issues | length }} total)</h2>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Row</th>
        <th>Field</th>
        <th>Dimension</th>
        <th>Reason</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      {% for issue in all_issues[:500] %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ issue.row_index }}</td>
        <td>{{ issue.field }}</td>
        <td><span class="badge badge-{{ issue.dimension }}">{{ issue.dimension }}</span></td>
        <td>{{ issue.reason }}</td>
        <td>{{ issue.get("value", "") }}</td>
      </tr>
      {% endfor %}
      {% if all_issues | length > 500 %}
      <tr><td colspan="6" style="text-align:center;color:#a0aec0;padding:0.75rem">
        ... and {{ (all_issues | length) - 500 }} more issues (export full JSON for complete list)
      </td></tr>
      {% endif %}
    </tbody>
  </table>
</div>
{% else %}
<div class="issues-section">
  <p class="no-issues">No issues detected across all dimensions.</p>
</div>
{% endif %}

<div class="footer">
  Generated by <strong>open-dqi</strong> &mdash; FutuX Agri-consult Limited
</div>
</body>
</html>
"""


@dataclass
class DQIReport:
    """
    Holds the complete DQI scoring results for a dataset evaluation run.

    Attributes
    ----------
    overall_score  : weighted average score across all four dimensions (0-100)
    completeness   : raw result dict from dimensions.completeness.score()
    validity       : raw result dict from dimensions.validity.score()
    uniqueness     : raw result dict from dimensions.uniqueness.score()
    outliers       : raw result dict from dimensions.outliers.score()
    schema         : the Schema used for the evaluation
    total_records  : number of rows in the evaluated DataFrame
    """
    overall_score: float
    completeness: dict
    validity: dict
    uniqueness: dict
    outliers: dict
    schema: "Schema"
    total_records: int

    @property
    def grade(self) -> str:
        """Return a letter grade for the overall score."""
        s = self.overall_score
        if s >= 90:
            return "A"
        if s >= 75:
            return "B"
        if s >= 60:
            return "C"
        if s >= 45:
            return "D"
        return "F"

    @property
    def dimensions(self) -> dict:
        """Return a summary dict of all four dimension scores."""
        return {
            "completeness": self.completeness["score"],
            "validity": self.validity["score"],
            "uniqueness": self.uniqueness["score"],
            "outliers": self.outliers["score"],
        }

    @property
    def all_issues(self) -> list[dict]:
        """Flatten issues from all four dimensions, adding a 'dimension' tag to each."""
        result = []
        for dim_name, dim_data in [
            ("completeness", self.completeness),
            ("validity", self.validity),
            ("uniqueness", self.uniqueness),
            ("outliers", self.outliers),
        ]:
            for issue in dim_data.get("issues", []):
                tagged = dict(issue)
                tagged["dimension"] = dim_name
                result.append(tagged)
        return result

    def export_json(self, path: str | Path) -> None:
        """Export the full report as a JSON file."""
        path = Path(path)
        payload = {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "total_records": self.total_records,
            "dimensions": self.dimensions,
            "weights": {
                "completeness": self.schema.weights.completeness,
                "validity": self.schema.weights.validity,
                "uniqueness": self.schema.weights.uniqueness,
                "outliers": self.schema.weights.outliers,
            },
            "completeness": self.completeness,
            "validity": self.validity,
            "uniqueness": self.uniqueness,
            "outliers": self.outliers,
            "all_issues": self.all_issues,
        }
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def export_html(self, path: str | Path) -> None:
        """
        Export a self-contained HTML report with inline CSS.
        No external dependencies are required to open the file.
        """
        from jinja2 import Environment
        from datetime import datetime

        path = Path(path)

        def score_color(s: float) -> str:
            if s >= 90:
                return "#38a169"
            if s >= 75:
                return "#3182ce"
            if s >= 60:
                return "#d69e2e"
            if s >= 45:
                return "#e53e3e"
            return "#742a2a"

        dim_display = {}
        w = self.schema.weights
        for dim_name, weight in [
            ("completeness", w.completeness),
            ("validity", w.validity),
            ("uniqueness", w.uniqueness),
            ("outliers", w.outliers),
        ]:
            s = self.dimensions[dim_name]
            dim_display[dim_name] = {
                "score": s,
                "weight": weight,
                "color": score_color(s),
            }

        env = Environment(autoescape=True)
        template = env.from_string(_HTML_TEMPLATE)
        html = template.render(
            overall_score=self.overall_score,
            grade=self.grade,
            score_color=score_color(self.overall_score),
            entity_label=self.schema.entity_label,
            total_records=self.total_records,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            dimensions=dim_display,
            weights=self.schema.weights,
            all_issues=self.all_issues,
        )
        path.write_text(html, encoding="utf-8")

    def __repr__(self) -> str:
        dims = self.dimensions
        return (
            f"DQIReport(overall={self.overall_score}, grade={self.grade!r}, "
            f"records={self.total_records}, "
            f"completeness={dims['completeness']}, "
            f"validity={dims['validity']}, "
            f"uniqueness={dims['uniqueness']}, "
            f"outliers={dims['outliers']})"
        )

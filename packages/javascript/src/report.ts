import { EvaluationReport } from "./types.js";

export class DQIReport {
  public data: EvaluationReport;

  constructor(data: EvaluationReport) {
    this.data = data;
  }

  get overallScore(): number {
    return this.data.overallScore;
  }

  get grade(): string {
    return this.data.grade;
  }

  toJSON(): string {
    return JSON.stringify(this.data, null, 2);
  }

  toHTML(): string {
    const { overallScore, grade, totalRecords, dimensions, allIssues, generatedAt } = this.data;

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DQI Report</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f6f9; color: #2d3748; padding: 2rem; margin: 0; }
  .header { margin-bottom: 2rem; }
  .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
  .card { background: #fff; border-radius: 10px; padding: 1.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .score-val { font-size: 2.2rem; font-weight: 800; color: #2b6cb0; }
  .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; }
  .grade-A { background: #c6f6d5; color: #22543d; }
  .grade-B { background: #bee3f8; color: #2b6cb0; }
  .grade-C { background: #feebc8; color: #7b341e; }
  .grade-D { background: #fed7d7; color: #742a2a; }
  .grade-F { background: #e2e8f0; color: #1a202c; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; margin-top: 1rem; }
  th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #edf2f7; font-size: 0.85rem; }
  th { background: #edf2f7; color: #4a5568; }
</style>
</head>
<body>
<div class="header">
  <h1>Data Quality Index Report</h1>
  <p>Total records: ${totalRecords} | Generated: ${generatedAt}</p>
</div>

<div class="card-grid">
  <div class="card">
    <div>Overall DQI</div>
    <div class="score-val">${overallScore}</div>
    <span class="badge grade-${grade}">Grade ${grade}</span>
  </div>
  <div class="card">
    <div>Completeness</div>
    <div class="score-val">${dimensions.completeness.score}</div>
  </div>
  <div class="card">
    <div>Validity</div>
    <div class="score-val">${dimensions.validity.score}</div>
  </div>
  <div class="card">
    <div>Uniqueness</div>
    <div class="score-val">${dimensions.uniqueness.score}</div>
  </div>
  <div class="card">
    <div>Outliers</div>
    <div class="score-val">${dimensions.outliers.score}</div>
  </div>
</div>

<h2>Audit Issues (${allIssues.length})</h2>
${
  allIssues.length === 0
    ? "<p>No issues detected.</p>"
    : `<table>
  <thead>
    <tr><th>Row</th><th>Field</th><th>Dimension</th><th>Reason</th></tr>
  </thead>
  <tbody>
    ${allIssues
      .slice(0, 500)
      .map(
        (i) =>
          `<tr><td>${i.rowIndex}</td><td>${i.field}</td><td>${i.dimension}</td><td>${i.reason}</td></tr>`
      )
      .join("")}
  </tbody>
</table>`
}
</body>
</html>`;
  }
}

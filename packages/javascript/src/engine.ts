import { Schema } from "./schema.js";
import { DQIReport } from "./report.js";
import { EvaluationReport, IssueItem } from "./types.js";
import { scoreCompleteness } from "./dimensions/completeness.js";
import { scoreValidity } from "./dimensions/validity.js";
import { scoreUniqueness } from "./dimensions/uniqueness.js";
import { scoreOutliers } from "./dimensions/outliers.js";
import Papa from "papaparse";

export class DQIEngine {
  public schema: Schema | null;

  constructor(schema: Schema | null = null) {
    this.schema = schema;
  }

  evaluate(csvInput: string | Record<string, string>[]): DQIReport {
    let rows: Record<string, string>[];

    if (typeof csvInput === "string") {
      const parsed = Papa.parse<Record<string, string>>(csvInput, {
        header: true,
        skipEmptyLines: true,
      });
      rows = parsed.data;
      if (!this.schema) {
        this.schema = Schema.infer(csvInput);
      }
    } else {
      rows = csvInput;
      if (!this.schema) {
        throw new Error("Schema must be provided when evaluating raw row arrays.");
      }
    }

    const completeness = scoreCompleteness(rows, this.schema);
    const validity = scoreValidity(rows, this.schema);
    const uniqueness = scoreUniqueness(rows, this.schema);
    const outliers = scoreOutliers(rows, this.schema);

    const w = this.schema.weights;
    const overall =
      completeness.score * w.completeness +
      validity.score * w.validity +
      uniqueness.score * w.uniqueness +
      outliers.score * w.outliers;

    const roundOverall = Number(overall.toFixed(2));
    let grade: "A" | "B" | "C" | "D" | "F" = "F";
    if (roundOverall >= 90) grade = "A";
    else if (roundOverall >= 75) grade = "B";
    else if (roundOverall >= 60) grade = "C";
    else if (roundOverall >= 45) grade = "D";

    const allIssues: IssueItem[] = [
      ...completeness.issues,
      ...validity.issues,
      ...uniqueness.issues,
      ...outliers.issues,
    ];

    const reportData: EvaluationReport = {
      overallScore: roundOverall,
      grade,
      totalRecords: rows.length,
      dimensions: {
        completeness,
        validity,
        uniqueness,
        outliers,
      },
      weights: w,
      allIssues,
      generatedAt: new Date().toISOString(),
    };

    return new DQIReport(reportData);
  }
}

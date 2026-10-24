import { Schema } from "../schema.js";
import { DimensionResult, IssueItem } from "../types.js";

export function scoreCompleteness(rows: Record<string, string>[], schema: Schema): DimensionResult {
  const issues: IssueItem[] = [];
  const requiredFields = Object.values(schema.fields)
    .filter((f) => f.required)
    .map((f) => f.name);

  if (requiredFields.length === 0 || rows.length === 0) {
    return { score: 100, issues: [] };
  }

  let totalRequiredSlots = rows.length * requiredFields.length;
  let missingCount = 0;

  rows.forEach((row, rowIndex) => {
    for (const field of requiredFields) {
      const val = row[field];
      if (val === undefined || val === null || val.trim() === "") {
        missingCount++;
        issues.push({
          rowIndex,
          field,
          dimension: "completeness",
          reason: "required_field_empty",
          value: val ?? null,
        });
      }
    }
  });

  const score = Math.max(0, Math.min(100, (1 - missingCount / totalRequiredSlots) * 100));
  return { score: Number(score.toFixed(2)), issues };
}

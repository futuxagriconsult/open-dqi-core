import { Schema } from "../schema.js";
import { DimensionResult, IssueItem, FieldType } from "../types.js";

function quantile(arr: number[], q: number): number {
  const sorted = [...arr].sort((a, b) => a - b);
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base]! + rest * (sorted[base + 1]! - sorted[base]!);
  }
  return sorted[base]!;
}

export function scoreOutliers(rows: Record<string, string>[], schema: Schema): DimensionResult {
  const issues: IssueItem[] = [];
  const flaggedRows = new Set<number>();

  const numericFields = Object.values(schema.fields)
    .filter((f) => [FieldType.FLOAT, FieldType.INTEGER].includes(f.type))
    .map((f) => f.name);

  if (numericFields.length === 0 || rows.length < 4) {
    return { score: 100, issues: [] };
  }

  for (const col of numericFields) {
    const validEntries: Array<{ idx: number; val: number }> = [];
    rows.forEach((row, rowIndex) => {
      const v = row[col];
      if (v !== undefined && v !== null && v.trim() !== "") {
        const num = Number(v);
        if (!isNaN(num)) {
          validEntries.push({ idx: rowIndex, val: num });
        }
      }
    });

    if (validEntries.length < 4) continue;

    const values = validEntries.map((e) => e.val);
    const q1 = quantile(values, 0.25);
    const q3 = quantile(values, 0.75);
    const iqr = q3 - q1;
    const lowerFence = q1 - 1.5 * iqr;
    const upperFence = q3 + 1.5 * iqr;

    for (const entry of validEntries) {
      if (entry.val < lowerFence || entry.val > upperFence) {
        flaggedRows.add(entry.idx);
        issues.push({
          rowIndex: entry.idx,
          field: col,
          dimension: "outliers",
          reason: `iqr_outlier_[${lowerFence.toFixed(2)},${upperFence.toFixed(2)}]`,
          value: entry.val,
        });
      }
    }
  }

  const score = rows.length === 0 ? 100 : Math.max(0, (1 - flaggedRows.size / rows.length) * 100);
  return {
    score: Number(score.toFixed(2)),
    issues,
  };
}

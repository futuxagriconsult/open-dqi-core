import { Schema } from "../schema.js";
import { DimensionResult, IssueItem } from "../types.js";

export function jaroWinkler(s1: string, s2: string): number {
  if (s1 === s2) return 1.0;
  const len1 = s1.length;
  const len2 = s2.length;
  if (len1 === 0 || len2 === 0) return 0.0;

  const matchDistance = Math.floor(Math.max(len1, len2) / 2) - 1;
  const s1Matches = new Array(len1).fill(false);
  const s2Matches = new Array(len2).fill(false);

  let matches = 0;
  for (let i = 0; i < len1; i++) {
    const start = Math.max(0, i - matchDistance);
    const end = Math.min(i + matchDistance + 1, len2);
    for (let j = start; j < end; j++) {
      if (s2Matches[j] || s1[i] !== s2[j]) continue;
      s1Matches[i] = true;
      s2Matches[j] = true;
      matches++;
      break;
    }
  }

  if (matches === 0) return 0.0;

  let transpositions = 0;
  let k = 0;
  for (let i = 0; i < len1; i++) {
    if (!s1Matches[i]) continue;
    while (!s2Matches[k]) k++;
    if (s1[i] !== s2[k]) transpositions++;
    k++;
  }

  const jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3;
  let prefix = 0;
  for (let i = 0; i < Math.min(4, Math.min(len1, len2)); i++) {
    if (s1[i] === s2[i]) prefix++;
    else break;
  }

  return jaro + prefix * 0.1 * (1 - jaro);
}

export function scoreUniqueness(rows: Record<string, string>[], schema: Schema): DimensionResult {
  const issues: IssueItem[] = [];
  const flaggedRows = new Set<number>();
  let exactDuplicates = 0;

  const uniqueKeyFields = Object.values(schema.fields)
    .filter((f) => f.uniqueKey)
    .map((f) => f.name);

  // Exact duplicates
  for (const col of uniqueKeyFields) {
    const seen = new Map<string, number>();
    rows.forEach((row, rowIndex) => {
      const val = row[col];
      if (!val || val.trim() === "") return;
      const key = val.trim();
      if (seen.has(key)) {
        exactDuplicates++;
        flaggedRows.add(rowIndex);
        issues.push({
          rowIndex,
          field: col,
          dimension: "uniqueness",
          reason: "exact_duplicate_key",
          duplicateOf: seen.get(key),
        });
      } else {
        seen.set(key, rowIndex);
      }
    });
  }

  // Soft fuzzy candidate pairs
  const fuzzyFields = Object.values(schema.fields)
    .filter((f) => f.fuzzyKey)
    .map((f) => f.name);

  for (const col of fuzzyFields) {
    const blocks = new Map<string, Array<{ idx: number; val: string }>>();
    rows.forEach((row, rowIndex) => {
      const val = row[col];
      if (!val || val.trim() === "") return;
      const clean = val.trim().toLowerCase();
      const bucket = clean[0] ?? "_";
      if (!blocks.has(bucket)) blocks.set(bucket, []);
      blocks.get(bucket)!.push({ idx: rowIndex, val: clean });
    });

    for (const entries of blocks.values()) {
      for (let i = 0; i < entries.length; i++) {
        for (let j = i + 1; j < entries.length; j++) {
          const sim = jaroWinkler(entries[i]!.val, entries[j]!.val);
          if (sim >= 0.85) {
            flaggedRows.add(entries[j]!.idx);
            issues.push({
              rowIndex: entries[j]!.idx,
              field: col,
              dimension: "uniqueness",
              reason: "fuzzy_duplicate_candidate",
              duplicateOf: entries[i]!.idx,
            });
          }
        }
      }
    }
  }

  const score = rows.length === 0 ? 100 : Math.max(0, (1 - flaggedRows.size / rows.length) * 100);
  return {
    score: Number(score.toFixed(2)),
    exactDuplicateCount: exactDuplicates,
    issues,
  };
}

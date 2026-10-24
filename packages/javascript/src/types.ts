export enum FieldType {
  TEXT = "text",
  INTEGER = "integer",
  FLOAT = "float",
  DATE = "date",
  PHONE = "phone",
  EMAIL = "email",
  LATITUDE = "latitude",
  LONGITUDE = "longitude",
  ENUM = "enum",
  ID = "id",
  BOOLEAN = "boolean",
}

export interface FieldDefinition {
  name: string;
  type: FieldType;
  required?: boolean;
  uniqueKey?: boolean;
  fuzzyKey?: boolean;
  min?: number | string;
  max?: number | string;
  pattern?: string;
  allowedValues?: string[];
  autoInferred?: boolean;
}

export interface DimensionWeights {
  completeness: number;
  validity: number;
  uniqueness: number;
  outliers: number;
}

export interface IssueItem {
  rowIndex: number;
  field: string;
  dimension: "completeness" | "validity" | "uniqueness" | "outliers";
  reason: string;
  value?: string | number | null;
  duplicateOf?: number;
}

export interface DimensionResult {
  score: number;
  issues: IssueItem[];
  [key: string]: unknown;
}

export interface EvaluationReport {
  overallScore: number;
  grade: "A" | "B" | "C" | "D" | "F";
  totalRecords: number;
  dimensions: {
    completeness: DimensionResult;
    validity: DimensionResult;
    uniqueness: DimensionResult;
    outliers: DimensionResult;
  };
  weights: DimensionWeights;
  allIssues: IssueItem[];
  generatedAt: string;
}

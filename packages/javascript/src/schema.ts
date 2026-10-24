import { FieldType, FieldDefinition, DimensionWeights } from "./types.js";
import yaml from "js-yaml";
import Papa from "papaparse";

export class Schema {
  public fields: Record<string, FieldDefinition>;
  public weights: DimensionWeights;
  public entityLabel: string;

  constructor(
    fields: Record<string, FieldDefinition>,
    weights: DimensionWeights = { completeness: 0.25, validity: 0.35, uniqueness: 0.25, outliers: 0.15 },
    entityLabel: string = "Record"
  ) {
    this.fields = fields;
    this.weights = weights;
    this.entityLabel = entityLabel;
  }

  static fromYAML(yamlString: string): Schema {
    const data = yaml.load(yamlString) as {
      entity_label?: string;
      dimensions?: { weights?: Partial<DimensionWeights> };
      fields?: Record<string, Record<string, unknown>>;
    };

    const entityLabel = data?.entity_label ?? "Record";
    const weightsCfg = data?.dimensions?.weights ?? {};
    const weights: DimensionWeights = {
      completeness: weightsCfg.completeness ?? 0.25,
      validity: weightsCfg.validity ?? 0.35,
      uniqueness: weightsCfg.uniqueness ?? 0.25,
      outliers: weightsCfg.outliers ?? 0.15,
    };

    const fields: Record<string, FieldDefinition> = {};
    if (data?.fields) {
      for (const [name, cfg] of Object.entries(data.fields)) {
        fields[name] = {
          name,
          type: (cfg["type"] as FieldType) || FieldType.TEXT,
          required: Boolean(cfg["required"]),
          uniqueKey: Boolean(cfg["unique_key"]),
          fuzzyKey: Boolean(cfg["fuzzy_key"]),
          min: cfg["min"] as number | string | undefined,
          max: cfg["max"] as number | string | undefined,
          pattern: cfg["pattern"] as string | undefined,
          allowedValues: cfg["allowed_values"] as string[] | undefined,
        };
      }
    }

    return new Schema(fields, weights, entityLabel);
  }

  static infer(csvContent: string): Schema {
    const parsed = Papa.parse<Record<string, string>>(csvContent, {
      header: true,
      skipEmptyLines: true,
      preview: 500,
    });

    const rows = parsed.data;
    const fields: Record<string, FieldDefinition> = {};
    const columns = parsed.meta.fields ?? [];

    for (const col of columns) {
      const lower = col.toLowerCase();
      let detectedType = FieldType.TEXT;

      if (lower.includes("phone") || lower.includes("tel") || lower.includes("mobile")) {
        detectedType = FieldType.PHONE;
      } else if (lower.includes("email")) {
        detectedType = FieldType.EMAIL;
      } else if (lower.includes("lat") || lower.includes("latitude")) {
        detectedType = FieldType.LATITUDE;
      } else if (lower.includes("lon") || lower.includes("lng") || lower.includes("longitude")) {
        detectedType = FieldType.LONGITUDE;
      } else if (lower.includes("date") || lower.includes("dob") || lower.includes("birth")) {
        detectedType = FieldType.DATE;
      } else if (lower.includes("id") || lower.includes("nin") || lower.includes("uuid") || lower.includes("ref")) {
        detectedType = FieldType.ID;
      } else {
        // Sample inspection
        const sampleVals = rows.map((r) => r[col]).filter((v) => v !== undefined && v !== null && v.trim() !== "");
        const allNumeric = sampleVals.length > 0 && sampleVals.every((v) => !isNaN(Number(v)));
        if (allNumeric) {
          const allInts = sampleVals.every((v) => Number.isInteger(Number(v)));
          detectedType = allInts ? FieldType.INTEGER : FieldType.FLOAT;
        }
      }

      const nonNullCount = rows.filter((r) => r[col] !== undefined && r[col] !== null && r[col].trim() !== "").length;
      const isRequired = rows.length > 0 && nonNullCount / rows.length > 0.95;
      const isUniqueKey = detectedType === FieldType.ID || lower.includes("id");

      fields[col] = {
        name: col,
        type: detectedType,
        required: isRequired,
        uniqueKey: isUniqueKey,
        fuzzyKey: detectedType === FieldType.TEXT && (lower.includes("name") || lower.includes("title")),
        autoInferred: true,
      };
    }

    return new Schema(fields);
  }
}

import { Schema } from "../schema.js";
import { DimensionResult, IssueItem, FieldType } from "../types.js";

const PHONE_REGEX = /^\+?[\d\s\-().]{7,15}$/;
const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function scoreValidity(rows: Record<string, string>[], schema: Schema): DimensionResult {
  const issues: IssueItem[] = [];
  let checkedSlots = 0;
  let invalidSlots = 0;

  rows.forEach((row, rowIndex) => {
    for (const [colName, fdef] of Object.entries(schema.fields)) {
      const val = row[colName];
      if (val === undefined || val === null || val.trim() === "") {
        continue;
      }

      checkedSlots++;
      const cleanVal = val.trim();
      let isValid = true;
      let reason = "";

      switch (fdef.type) {
        case FieldType.INTEGER: {
          const num = Number(cleanVal);
          if (isNaN(num) || !Number.isInteger(num)) {
            isValid = false;
            reason = "invalid_integer_format";
          } else {
            if (fdef.min !== undefined && num < Number(fdef.min)) {
              isValid = false;
              reason = `integer_below_min_${fdef.min}`;
            }
            if (fdef.max !== undefined && num > Number(fdef.max)) {
              isValid = false;
              reason = `integer_above_max_${fdef.max}`;
            }
          }
          break;
        }
        case FieldType.FLOAT: {
          const num = Number(cleanVal);
          if (isNaN(num)) {
            isValid = false;
            reason = "invalid_float_format";
          } else {
            if (fdef.min !== undefined && num < Number(fdef.min)) {
              isValid = false;
              reason = `float_below_min_${fdef.min}`;
            }
            if (fdef.max !== undefined && num > Number(fdef.max)) {
              isValid = false;
              reason = `float_above_max_${fdef.max}`;
            }
          }
          break;
        }
        case FieldType.LATITUDE: {
          const num = Number(cleanVal);
          const minLat = fdef.min !== undefined ? Number(fdef.min) : -90.0;
          const maxLat = fdef.max !== undefined ? Number(fdef.max) : 90.0;
          if (isNaN(num) || num < minLat || num > maxLat) {
            isValid = false;
            reason = `latitude_out_of_bounds_[${minLat},${maxLat}]`;
          }
          break;
        }
        case FieldType.LONGITUDE: {
          const num = Number(cleanVal);
          const minLon = fdef.min !== undefined ? Number(fdef.min) : -180.0;
          const maxLon = fdef.max !== undefined ? Number(fdef.max) : 180.0;
          if (isNaN(num) || num < minLon || num > maxLon) {
            isValid = false;
            reason = `longitude_out_of_bounds_[${minLon},${maxLon}]`;
          }
          break;
        }
        case FieldType.PHONE: {
          if (!PHONE_REGEX.test(cleanVal)) {
            isValid = false;
            reason = "invalid_phone_format";
          }
          break;
        }
        case FieldType.EMAIL: {
          if (!EMAIL_REGEX.test(cleanVal)) {
            isValid = false;
            reason = "invalid_email_format";
          }
          break;
        }
        case FieldType.ENUM: {
          if (fdef.allowedValues && !fdef.allowedValues.includes(cleanVal)) {
            isValid = false;
            reason = `value_not_in_allowed_enum`;
          }
          break;
        }
        case FieldType.DATE: {
          const parsed = Date.parse(cleanVal);
          if (isNaN(parsed)) {
            isValid = false;
            reason = "invalid_date_format";
          }
          break;
        }
        case FieldType.BOOLEAN: {
          const boolLower = cleanVal.toLowerCase();
          if (!["true", "false", "1", "0", "yes", "no"].includes(boolLower)) {
            isValid = false;
            reason = "invalid_boolean_format";
          }
          break;
        }
      }

      if (!isValid) {
        invalidSlots++;
        issues.push({
          rowIndex,
          field: colName,
          dimension: "validity",
          reason,
          value: cleanVal,
        });
      }
    }
  });

  const score = checkedSlots === 0 ? 100 : Math.max(0, Math.min(100, (1 - invalidSlots / checkedSlots) * 100));
  return { score: Number(score.toFixed(2)), issues };
}

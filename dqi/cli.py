"""
Command-line interface for open-dqi.

Commands
--------
dqi audit           : score a CSV file and produce a report
dqi init            : generate a YAML schema from a CSV file
dqi validate-schema : validate an existing YAML schema file
"""
from __future__ import annotations
import sys
from pathlib import Path
import click
from .engine import DQIEngine
from .schema import Schema


@click.group()
@click.version_option(package_name="open-dqi")
def main():
    """open-dqi: Data Quality Index scoring for any tabular dataset."""


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to the CSV file to audit.")
@click.option("--schema", "schema_path", default=None, type=click.Path(exists=True),
              help="Path to a YAML schema file. If omitted, schema is auto-inferred.")
@click.option("--output", "output_path", default=None, type=click.Path(),
              help="Output path (without extension). Defaults to <input_stem>_dqi_report.")
@click.option("--format", "output_format", default="both",
              type=click.Choice(["html", "json", "both"], case_sensitive=False),
              help="Output format: html, json, or both.")
def audit(input_path: str, schema_path: str | None, output_path: str | None, output_format: str):
    """
    Score a CSV file across all four DQI dimensions and produce a report.

    Examples:

        dqi audit --input data.csv

        dqi audit --input data.csv --schema schema.yaml --format html

        dqi audit --input data.csv --output results/report --format both
    """
    input_file = Path(input_path)
    schema = None

    if schema_path:
        click.echo(f"Loading schema from: {schema_path}")
        try:
            schema = Schema.from_yaml(schema_path)
        except Exception as exc:
            click.echo(f"Error loading schema: {exc}", err=True)
            sys.exit(1)
    else:
        click.echo("No schema provided; auto-inferring from input data.")

    engine = DQIEngine(schema)

    click.echo(f"Evaluating: {input_file} ...")
    try:
        report = engine.evaluate(input_file)
    except Exception as exc:
        click.echo(f"Evaluation failed: {exc}", err=True)
        sys.exit(1)

    # Print summary to terminal
    click.echo("")
    click.echo(f"  Overall DQI Score : {report.overall_score:.2f} / 100  (Grade {report.grade})")
    click.echo(f"  Total records     : {report.total_records}")
    click.echo(f"  Completeness      : {report.completeness['score']:.2f}")
    click.echo(f"  Validity          : {report.validity['score']:.2f}")
    click.echo(f"  Uniqueness        : {report.uniqueness['score']:.2f}")
    click.echo(f"  Outliers          : {report.outliers['score']:.2f}")
    click.echo(f"  Total issues      : {len(report.all_issues)}")
    click.echo("")

    # Determine output base path
    base = Path(output_path) if output_path else input_file.parent / f"{input_file.stem}_dqi_report"

    if output_format in ("json", "both"):
        json_path = base.with_suffix(".json")
        report.export_json(json_path)
        click.echo(f"  JSON report saved : {json_path}")

    if output_format in ("html", "both"):
        html_path = base.with_suffix(".html")
        report.export_html(html_path)
        click.echo(f"  HTML report saved : {html_path}")


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to the CSV file to infer a schema from.")
@click.option("--output", "output_path", default=None, type=click.Path(),
              help="Output YAML path. Defaults to <input_stem>_schema.yaml.")
@click.option("--rows", "sample_rows", default=500, show_default=True, type=int,
              help="Number of rows to sample for type inference.")
def init(input_path: str, output_path: str | None, sample_rows: int):
    """
    Generate a YAML schema by auto-inferring field types from a CSV file.

    The generated schema can be hand-edited before passing it to 'dqi audit'.

    Examples:

        dqi init --input data.csv

        dqi init --input data.csv --output my_schema.yaml
    """
    input_file = Path(input_path)
    click.echo(f"Inferring schema from: {input_file} (sampling up to {sample_rows} rows) ...")

    try:
        schema = Schema.infer(input_file, sample_rows=sample_rows)
    except Exception as exc:
        click.echo(f"Schema inference failed: {exc}", err=True)
        sys.exit(1)

    out_path = Path(output_path) if output_path else input_file.parent / f"{input_file.stem}_schema.yaml"

    yaml_str = schema.to_yaml()
    out_path.write_text(yaml_str, encoding="utf-8")

    click.echo(f"Schema written to: {out_path}")
    click.echo(f"Fields detected: {len(schema.fields)}")
    for col, fdef in schema.fields.items():
        flags = []
        if fdef.required:
            flags.append("required")
        if fdef.unique_key:
            flags.append("unique_key")
        if fdef.fuzzy_key:
            flags.append("fuzzy_key")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""
        click.echo(f"  {col}: {fdef.type.value}{flag_str}")


@main.command("validate-schema")
@click.option("--schema", "schema_path", required=True, type=click.Path(exists=True),
              help="Path to the YAML schema file to validate.")
def validate_schema(schema_path: str):
    """
    Validate a YAML schema file for structural correctness.

    Checks that all field types are recognised, weights sum to 1.0, and all
    referenced FieldType values are valid.

    Examples:

        dqi validate-schema --schema my_schema.yaml
    """
    click.echo(f"Validating schema: {schema_path} ...")

    try:
        schema = Schema.from_yaml(schema_path)
    except Exception as exc:
        click.echo(f"Schema is INVALID: {exc}", err=True)
        sys.exit(1)

    w = schema.weights
    click.echo("  Schema is valid.")
    click.echo(f"  Entity label  : {schema.entity_label}")
    click.echo(f"  Fields        : {len(schema.fields)}")
    click.echo(f"  Required      : {len(schema.required_fields())}")
    click.echo(f"  Unique keys   : {len(schema.unique_key_fields())}")
    click.echo(f"  Fuzzy keys    : {len(schema.fuzzy_key_fields())}")
    click.echo(f"  Weights       : completeness={w.completeness}, validity={w.validity}, "
               f"uniqueness={w.uniqueness}, outliers={w.outliers}")


if __name__ == "__main__":
    main()


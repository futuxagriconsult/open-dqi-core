# Contributing to open-dqi

Thank you for considering a contribution to open-dqi. This document covers everything needed to get a development environment running, the coding standards to follow, and the non-negotiable privacy rule that applies to all contributions.

---

## Data Privacy Rule

**This section is binding on all contributors. No exceptions.**

1. **All test fixtures and documentation examples must use synthetically generated data only.** The `tests/fixtures/generate_fixtures.py` script provides a reproducible, Faker-based generator (SEED=42) for all CSV fixtures. Any new fixture added to the repository must be produced by this script or an equivalent deterministic synthetic generator.

2. **Real operational records must never be committed to this repository.** This includes, but is not limited to: actual farmer names and phone numbers from any registry, voter PII from any electoral commission dataset, patient records from any health facility, beneficiary data from any social protection program, or any other dataset containing real personal information.

3. **Model weights (in the sister repository `whitebox-dedup-ml`) may be trained locally on private data and committed to that repository as serialized JSON files only.** Raw training data containing PII must never be committed to any repository in this organisation.

Violations of this rule will result in immediate removal of the offending commit and revocation of contributor access.

---

## Development Setup

Prerequisites: Python 3.10+, pip.

```bash
git clone https://github.com/futux/open-dqi-core
cd open-dqi-core
pip install -e ".[dev]"
python tests/fixtures/generate_fixtures.py   # generate synthetic fixtures
pytest tests/ -v                             # run the full test suite
```

---

## Running the Linter

This project uses `ruff` for linting and formatting:

```bash
ruff check dqi/ tests/
ruff format dqi/ tests/
```

All linting checks must pass before a pull request is merged.

---

## Adding a New Dimension

The four current dimensions (Completeness, Validity, Uniqueness, Outlier Detection) are implemented in `dqi/dimensions/`. To add a new dimension:

1. Create `dqi/dimensions/<your_dimension>.py` exposing a `score(df, schema) -> dict` function. The dict must contain at least a `score` key (float, 0-100) and an `issues` key (list of dicts).
2. Add the new dimension to `dqi/engine.py` and wire it into the weighted average.
3. Add a `DimensionWeights` field and ensure all weights still sum to 1.0.
4. Add tests in `tests/test_<your_dimension>.py`.
5. Update the README dimensions table.

---

## Adding a New Schema Template

Schema templates live in `dqi/schemas/`. Each file is a YAML document following the format described in the Schema Guide section of the README. When adding a new template:

1. Place the file in `dqi/schemas/<name>_v1.yaml`.
2. Add an entry to the pre-built schema templates table in README.md.
3. Add at least one clean and one dirty fixture CSV for the new schema in `tests/fixtures/`.
4. Add the fixture generation logic to `tests/fixtures/generate_fixtures.py`.

---

## Pull Request Process

1. Fork the repository and create a branch from `main`.
2. Make changes. Write tests for any new behaviour.
3. Run `pytest tests/ --cov=dqi` and confirm coverage does not decrease.
4. Run `ruff check dqi/ tests/` and fix any warnings.
5. Open a pull request against `main` with a clear description of what changed and why.

---

## Code of Conduct

This project follows the Contributor Covenant v2.1. All participants are expected to treat each other with respect. Harassment, discrimination, and bad-faith contributions will not be tolerated.

---

## License

By contributing to open-dqi, contributors agree that their contributions will be licensed under the Apache 2.0 License, the same license that covers the rest of the project.

"""
Deterministic synthetic fixture generator for open-dqi tests.

Run this script to regenerate all CSV fixtures:

    python tests/fixtures/generate_fixtures.py

All data is entirely synthetic (Faker seed=42). No real personal data is used.

Fixtures produced
-----------------
agriculture_clean.csv           200 rows, zero defects
agriculture_dirty.csv           200 rows, documented defects
voter_registry_clean.csv        200 rows, zero defects
voter_registry_dirty.csv        200 rows, documented defects
credit_applicants_clean.csv     200 rows, zero defects
credit_applicants_dirty.csv     200 rows, documented defects
expected_scores.json            Approximate expected DQI scores per fixture
"""
from __future__ import annotations
import json
import random
from pathlib import Path

# Faker is an optional dev dependency; gate the import cleanly
try:
    from faker import Faker
except ImportError as exc:
    raise SystemExit(
        "Faker is required to generate fixtures. "
        "Install it with: pip install faker>=24.0"
    ) from exc

import pandas as pd

SEED = 42
OUT_DIR = Path(__file__).parent

# Reproducible generators
fake_en = Faker("en_US")
try:
    fake_ng = Faker("en_NG")
except Exception:
    fake_ng = Faker("en_GB")
Faker.seed(SEED)
random.seed(SEED)

# Nigerian states for agriculture / civil registry data
NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa",
    "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti",
    "Enugu", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina",
    "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun",
    "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba",
    "Yobe", "Zamfara", "FCT",
]

CROP_TYPES = ["Maize", "Rice", "Cassava", "Yam", "Sorghum", "Millet",
              "Groundnut", "Cowpea", "Soybean", "Tomato", "Pepper", "Other"]

GENDERS = ["Male", "Female"]
REGIONS = ["North West", "North East", "North Central", "South West", "South East", "South South"]


def _phone() -> str:
    """Generate a valid phone number string."""
    return f"+234{random.randint(7000000000, 9099999999)}"


def _nigeria_lat() -> float:
    return round(random.uniform(3.1, 13.9), 6)


def _nigeria_lon() -> float:
    return round(random.uniform(3.1, 14.9), 6)


def _generate_clean_names(n: int, seed: int = 42) -> list[str]:
    import jellyfish
    first_names = [
        "Aaron", "Abubakar", "Ada", "Adamu", "Ade", "Adewale", "Aisha", "Akin", "Aliyu", "Aminu",
        "Babatunde", "Bello", "Bilkisu", "Blessing", "Bolaji", "Bukola", "Chidi", "Chinedu", "Chisom", "Comfort",
        "Danladi", "Daniel", "David", "Dayo", "Dike", "Efe", "Emeka", "Emmanuel", "Eniola", "Faith",
        "Fatima", "Femi", "Gabriel", "Garba", "Gbenga", "Grace", "Habib", "Hadiza", "Halima", "Haruna",
        "Hassan", "Hauwa", "Ibrahim", "Idris", "Ifeanyi", "Isaac", "Isah", "Janet", "John", "Joseph",
        "Kabir", "Kehinde", "Kelechi", "Lawal", "Maimuna", "Maryam", "Mohammed", "Musa", "Mustapha", "Ngozi",
        "Ogechi", "Olamide", "Olumide", "Oluwaseun", "Patience", "Peter", "Rabi", "Rakiya", "Ramatu", "Rotimi",
        "Sadiq", "Salisu", "Samuel", "Sanusi", "Saratu", "Segun", "Shehu", "Suleiman", "Taiwo", "Temitope",
        "Uche", "Umar", "Usman", "Victoria", "Wale", "Yakubu", "Yusuf", "Zainab"
    ]
    last_names = [
        "Abiola", "Abdullahi", "Adeyemi", "Afolabi", "Agbaje", "Ahmed", "Ajayi", "Akintola", "Alabi", "Ali",
        "Babangida", "Bakare", "Balogun", "Bankole", "Buba", "Chukwu", "Danjuma", "Dauda", "Dikko", "Dosunmu",
        "Ebuka", "Eze", "Fashola", "Gbadamosi", "Gowon", "Gwarzo", "Hassan", "Ibe", "Igwe", "Jalingo",
        "Kano", "Katsina", "Kalu", "Lawan", "Maikudi", "Makama", "Momoh", "Nwosu", "Nnamani", "Obi",
        "Ogundipe", "Okafor", "Okeke", "Okonkwo", "Oladipo", "Olawale", "Oloyede", "Oni", "Otedola", "Rabiu",
        "Ribadu", "Salami", "Sanusi", "Shekarau", "Shonekan", "Soyinka", "Tafa", "Tukur", "Uba", "Waziri",
        "YarAdua", "Zubairu"
    ]
    rng = random.Random(seed)
    candidates = [f"{fn} {ln}" for fn in first_names for ln in last_names]
    rng.shuffle(candidates)
    selected: list[str] = []
    for cand in candidates:
        bucket = cand[0].lower()
        clash = False
        for s in selected:
            if s[0].lower() == bucket:
                if jellyfish.jaro_winkler_similarity(cand.lower(), s.lower()) >= 0.85:
                    clash = True
                    break
        if not clash:
            selected.append(cand)
            if len(selected) == n:
                break
    while len(selected) < n:
        selected.append(f"Person{len(selected)} Distinct{len(selected)}")
    return selected


# ---------------------------------------------------------------------------
# Agriculture clean (200 rows, no defects)
# ---------------------------------------------------------------------------
def make_agriculture_clean(n: int = 200) -> pd.DataFrame:
    names = _generate_clean_names(n, seed=42)
    rows = []
    for i in range(n):
        rows.append({
            "farmer_id": f"FMR-{i+1:06d}",
            "full_name": names[i],
            "phone_number": _phone(),
            "state": random.choice(NIGERIAN_STATES),
            "lga": fake_en.city(),
            "latitude": _nigeria_lat(),
            "longitude": _nigeria_lon(),
            "farm_area_ha": round(random.uniform(0.5, 10.0), 2),
            "age": random.randint(18, 70),
            "gender": random.choice(GENDERS),
            "crop_type": random.choice(CROP_TYPES),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Agriculture dirty (200 rows, documented defects)
#
# Defect inventory:
#   D1: rows 0-19   -> phone_number is None             (20 rows)
#   D2: rows 20-29  -> latitude outside Nigeria (<-10)  (10 rows)
#   D3: rows 30-37  -> 8 rows share full_name "Aminu Kano" (fuzzy duplicate candidate)
#   D4: rows 38-42  -> farm_area_ha = 800               (5 rows, extreme outlier)
# ---------------------------------------------------------------------------
def make_agriculture_dirty(n: int = 200) -> pd.DataFrame:
    df = make_agriculture_clean(n)

    # D1: null phone_number (exactly 20 rows, 0-19)
    df.loc[0:19, "phone_number"] = None

    # D2: latitude outside Nigeria bounds (rows 30-59)
    for i in range(30, 60):
        df.loc[i, "latitude"] = round(random.uniform(-30.0, -11.0), 6)

    # D3: fuzzy name duplicates (rows 60-69 all share a very similar name)
    dup_names = [
        "Aminu Kano", "Aminu Kano", "Aminu Kanu", "Aminu Kanoo",
        "Aminnu Kano", "Aminu Kano", "Aminn Kano", "Aminu Kano",
        "Aminu Kanou", "Aminnu Kanu"
    ]
    for i, name in zip(range(60, 70), dup_names):
        df.loc[i, "full_name"] = name

    # D4: extreme outlier farm_area_ha (rows 70-79)
    for i in range(70, 80):
        df.loc[i, "farm_area_ha"] = 800.0

    return df


# ---------------------------------------------------------------------------
# Voter registry clean (200 rows)
# ---------------------------------------------------------------------------
def make_voter_registry_clean(n: int = 200) -> pd.DataFrame:
    names = _generate_clean_names(n, seed=99)
    rows = []
    for i in range(n):
        dob = fake_en.date_of_birth(minimum_age=18, maximum_age=74)
        rows.append({
            "voter_id": f"VTR-{i+1:06d}",
            "full_name": names[i],
            "date_of_birth": dob.strftime("%Y-%m-%d"),
            "gender": random.choice(GENDERS),
            "state": random.choice(NIGERIAN_STATES),
            "registration_date": fake_en.date_between(start_date="-10y", end_date="today").strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Voter registry dirty (200 rows)
#
# Defect inventory:
#   D1: rows 0-14   -> date_of_birth is None        (15 rows)
#   D2: rows 15-19  -> duplicate voter_id "VTR-000001" (5 rows, exact dup of row 0)
#   D3: rows 20-27  -> gender = "Unknown" (invalid)  (8 rows)
# ---------------------------------------------------------------------------
def make_voter_registry_dirty(n: int = 200) -> pd.DataFrame:
    df = make_voter_registry_clean(n)

    # D1: null date_of_birth
    df.loc[0:14, "date_of_birth"] = None

    # D2: duplicate voter_id values (rows 15-19 get the same ID as row 0)
    for i in range(15, 20):
        df.loc[i, "voter_id"] = "VTR-000001"

    # D3: invalid gender values
    for i in range(20, 28):
        df.loc[i, "gender"] = "Unknown"

    return df


# ---------------------------------------------------------------------------
# Credit applicants clean (200 rows)
# ---------------------------------------------------------------------------
def make_credit_applicants_clean(n: int = 200) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append({
            "applicant_id": f"APP-{i+1:06d}",
            "full_name": fake_en.name(),
            "phone": _phone(),
            "email": fake_en.email(),
            "monthly_income": round(random.uniform(5000, 500000), 2),
            "age": random.randint(21, 65),
            "gender": random.choice(GENDERS),
            "region": random.choice(REGIONS),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Credit applicants dirty (200 rows)
#
# Defect inventory:
#   D1: rows 0-11   -> email is None                       (12 rows)
#   D2: rows 12-18  -> phone = "not-a-phone"               (7 rows)
#   D3: rows 19-28  -> monthly_income = 9_500_000 (outlier) (10 rows)
# ---------------------------------------------------------------------------
def make_credit_applicants_dirty(n: int = 200) -> pd.DataFrame:
    df = make_credit_applicants_clean(n)

    # D1: null email
    df.loc[0:11, "email"] = None

    # D2: invalid phone formats
    for i in range(12, 19):
        df.loc[i, "phone"] = "not-a-phone"

    # D3: extreme income outliers
    for i in range(19, 29):
        df.loc[i, "monthly_income"] = 9_500_000.0

    return df


# ---------------------------------------------------------------------------
# Expected scores (approximate, based on defect counts)
# ---------------------------------------------------------------------------
def compute_expected_scores() -> dict:
    """
    Approximate expected DQI scores per fixture.
    These values are used in tests as upper/lower bound guards only.
    Exact scores depend on the engine implementation and weights.
    """
    return {
        "agriculture_clean": {
            "overall_min": 90.0,
            "completeness_min": 95.0,
            "validity_min": 90.0,
            "uniqueness_min": 95.0,
            "outliers_min": 95.0,
            "note": "Clean fixture; all dimensions should score near 100.",
        },
        "agriculture_dirty": {
            "overall_max": 80.0,
            "completeness_max": 90.0,
            "note": (
                "D1: 20/200 null phone_numbers -> completeness ~90%;"
                " D2: 10 lat outliers -> validity and outlier penalty;"
                " D3: 8 fuzzy duplicate rows -> uniqueness penalty;"
                " D4: 5 extreme farm_area_ha -> outlier penalty."
            ),
        },
        "voter_registry_clean": {
            "overall_min": 90.0,
            "completeness_min": 95.0,
            "note": "Clean voter fixture; should score near 100 on all dimensions.",
        },
        "voter_registry_dirty": {
            "overall_max": 85.0,
            "note": (
                "D1: 15 null dob -> completeness penalty;"
                " D2: 5 duplicate voter_id -> uniqueness penalty;"
                " D3: 8 invalid gender -> validity penalty."
            ),
        },
        "credit_applicants_clean": {
            "overall_min": 90.0,
            "note": "Clean credit fixture; should score near 100.",
        },
        "credit_applicants_dirty": {
            "overall_max": 85.0,
            "note": (
                "D1: 12 null emails -> completeness penalty;"
                " D2: 7 invalid phone formats -> validity penalty;"
                " D3: 10 extreme income outliers -> outlier penalty."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating agriculture_clean.csv ...")
    make_agriculture_clean().to_csv(OUT_DIR / "agriculture_clean.csv", index=False)

    print("Generating agriculture_dirty.csv ...")
    make_agriculture_dirty().to_csv(OUT_DIR / "agriculture_dirty.csv", index=False)

    print("Generating voter_registry_clean.csv ...")
    make_voter_registry_clean().to_csv(OUT_DIR / "voter_registry_clean.csv", index=False)

    print("Generating voter_registry_dirty.csv ...")
    make_voter_registry_dirty().to_csv(OUT_DIR / "voter_registry_dirty.csv", index=False)

    print("Generating credit_applicants_clean.csv ...")
    make_credit_applicants_clean().to_csv(OUT_DIR / "credit_applicants_clean.csv", index=False)

    print("Generating credit_applicants_dirty.csv ...")
    make_credit_applicants_dirty().to_csv(OUT_DIR / "credit_applicants_dirty.csv", index=False)

    print("Writing expected_scores.json ...")
    (OUT_DIR / "expected_scores.json").write_text(
        json.dumps(compute_expected_scores(), indent=2),
        encoding="utf-8",
    )

    print("All fixtures generated successfully.")


if __name__ == "__main__":
    main()

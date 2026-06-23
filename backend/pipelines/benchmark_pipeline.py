import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "clinicaltrials_gov"

PROCESSED_DIR = DATA_DIR / "processed" / "v0_1"
BENCHMARK_DIR = DATA_DIR / "benchmarks" / "v0_1"

def load_raw_trials(filename: str) -> dict:
    path = RAW_DIR / filename

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_processed_trials(filename: str) -> list[dict]:
    path = PROCESSED_DIR / filename

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_operational_risk_benchmark(
    trials: list[dict],
) -> list[dict]:
    benchmark = []

    for trial in trials:
        benchmark.append({
            "nct_id": trial.get("nct_id"),
            "phase": trial.get("phase"),
            "study_type": trial.get("study_type"),
            "status": trial.get("status"),
            "sponsor": trial.get("sponsor"),
            "enrollment": trial.get("enrollment"),
            "conditions": trial.get("conditions"),
            "interventions": trial.get("interventions"),
            "target": trial.get("operational_risk"),
        })

    return benchmark


def save_benchmark(
    benchmark: list[dict],
    filename: str,
) -> Path:
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    path = BENCHMARK_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(benchmark, f, indent=2, ensure_ascii=False)

    return path

def save_benchmark_metadata(
    benchmark: list[dict],
    filename: str,
    task_name: str,
) -> Path:

    n_examples = len(benchmark)

    n_positive = sum(
        row["target"] == 1
        for row in benchmark
    )

    n_negative = n_examples - n_positive

    metadata = {
        "task": task_name,
        "created_at": datetime.now().isoformat(),

        "n_examples": n_examples,
        "n_positive": n_positive,
        "n_negative": n_negative,
        "positive_ratio": round(
            n_positive / n_examples,
            4,
        ),

        "target_name": "operational_risk",

        "label_definition": {
            "positive": [
                "TERMINATED",
                "WITHDRAWN",
                "SUSPENDED",
            ],
            "negative": "all other statuses",
        },

        "features": [
            "phase",
            "study_type",
            "status",
            "sponsor",
            "enrollment",
            "conditions",
            "interventions",
        ],
    }

    path = BENCHMARK_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False,
        )

    return path

def save_unified_benchmark_metadata(
    benchmark: list[dict],
    filename: str,
) -> Path:
    n_examples = len(benchmark)

    risk_columns = [
        "operational_risk",
        "safety_risk",
        "efficacy_risk",
    ]

    label_stats = {}

    for column in risk_columns:
        valid_rows = [
            row for row in benchmark
            if row.get(column) is not None
        ]

        n_valid = len(valid_rows)
        n_positive = sum(row[column] == 1 for row in valid_rows)
        n_negative = n_valid - n_positive

        label_stats[column] = {
            "n_valid": n_valid,
            "n_positive": n_positive,
            "n_negative": n_negative,
            "positive_ratio": (
                round(n_positive / n_valid, 4)
                if n_valid
                else None
            ),
        }

    metadata = {
        "task": "unified_risk",
        "created_at": datetime.now().isoformat(),
        "n_examples": n_examples,
        "risk_columns": risk_columns,
        "label_stats": label_stats,
        "features": [
            "phase",
            "study_type",
            "status",
            "sponsor",
            "enrollment",
            "conditions",
            "interventions",
        ],
    }

    path = BENCHMARK_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return path

def _join(values):
    if not values:
        return None
    if isinstance(values, list):
        return ", ".join(str(v) for v in values if v)
    return str(values)

def build_safety_risk_benchmark(studies: list[dict]) -> list[dict]:
    benchmark = []

    for study in studies:
        if not study.get("hasResults"):
            continue

        protocol = study.get("protocolSection", {})
        results = study.get("resultsSection", {})

        identification = protocol.get("identificationModule", {})
        design = protocol.get("designModule", {})
        sponsor = protocol.get("sponsorCollaboratorsModule", {})
        conditions = protocol.get("conditionsModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        adverse = results.get("adverseEventsModule", {})

        serious_total = sum(
            int(group.get("seriousNumAffected", 0) or 0)
            for group in adverse.get("eventGroups", [])
        )

        benchmark.append({
            "nct_id": identification.get("nctId"),
            "phase": _join(design.get("phases")),
            "study_type": design.get("studyType"),
            "sponsor": sponsor.get("leadSponsor", {}).get("name"),
            "enrollment": design.get("enrollmentInfo", {}).get("count"),
            "conditions": conditions.get("conditions", []),
            "interventions": [
                item.get("name")
                for item in arms.get("interventions", [])
                if item.get("name")
            ],
            "serious_adverse_events": serious_total,
            "target": int(serious_total > 0),
        })

    return benchmark


def build_unified_risk_benchmark(
    operational_rows: list[dict],
    safety_rows: list[dict],
) -> list[dict]:
    safety_by_nct_id = {
        row["nct_id"]: row
        for row in safety_rows
        if row.get("nct_id")
    }

    unified = []

    for row in operational_rows:
        nct_id = row.get("nct_id")
        safety_row = safety_by_nct_id.get(nct_id)

        unified.append({
            "nct_id": nct_id,
            "phase": row.get("phase"),
            "study_type": row.get("study_type"),
            "status": row.get("status"),
            "sponsor": row.get("sponsor"),
            "enrollment": row.get("enrollment"),
            "conditions": row.get("conditions"),
            "interventions": row.get("interventions"),
            "source_condition": row.get("source_condition"),

            "operational_risk": row.get("target"),
            "safety_risk": (
                safety_row.get("target")
                if safety_row is not None
                else None
            ),

            # Placeholder for now.
            "efficacy_risk": None,
        })

    return unified

if __name__ == "__main__":
    conditions = [
        "autism",
        "depression",
        "psoriasis",
        "diabetes",
        "breast cancer",
        "covid 19",
        "alzheimers",
        "parkinsons",
    ]

    operational_examples = []
    safety_examples = []

    for condition in conditions:
        processed_filename = f"{condition}_trials.json"
        raw_filename = f"{condition}_raw_trials.json"

        try:
            trials = load_processed_trials(processed_filename)

            benchmark = build_operational_risk_benchmark(trials)

            for row in benchmark:
                row["source_condition"] = condition

            operational_examples.extend(benchmark)

        except FileNotFoundError:
            print(f"Skipping operational labels for {condition}")

        try:
            raw_data = load_raw_trials(raw_filename)

            benchmark = build_safety_risk_benchmark(
                raw_data.get("studies", [])
            )

            for row in benchmark:
                row["source_condition"] = condition

            safety_examples.extend(benchmark)

        except FileNotFoundError:
            print(f"Skipping safety labels for {condition}")

    unified_examples = build_unified_risk_benchmark(
        operational_examples,
        safety_examples,
    )

    output_path = save_benchmark(
        unified_examples,
        "unified_risk_multi_condition.json",
    )

    metadata_path = save_unified_benchmark_metadata(
        unified_examples,
        "unified_risk_multi_condition_metadata.json",
    )

    print("\nUnified risk benchmark")
    print(f"Saved benchmark to: {output_path}")
    print(f"Saved metadata to: {metadata_path}")
    print(f"Examples: {len(unified_examples)}")

    for risk_type in [
        "operational_risk",
        "safety_risk",
        "efficacy_risk",
    ]:
        valid_rows = [
            row for row in unified_examples
            if row.get(risk_type) is not None
        ]

        positives = sum(row[risk_type] == 1 for row in valid_rows)

        print(f"\n{risk_type}")
        print(f"Valid examples: {len(valid_rows)}")
        print(f"High risk: {positives}")
        print(f"Low risk: {len(valid_rows) - positives}")

        if valid_rows:
            print(f"Positive ratio: {positives / len(valid_rows):.2%}")


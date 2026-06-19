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

    # ------------------------------------------------------------
    # Operational risk benchmark
    # Uses processed normalized Trial objects.
    # ------------------------------------------------------------

    operational_examples = []

    for condition in conditions:
        filename = f"{condition}_trials.json"

        try:
            trials = load_processed_trials(filename)
        except FileNotFoundError:
            print(f"Skipping operational benchmark for {condition}")
            continue

        benchmark = build_operational_risk_benchmark(trials)

        for row in benchmark:
            row["source_condition"] = condition

        operational_examples.extend(benchmark)

    operational_output_path = save_benchmark(
        operational_examples,
        "operational_risk_multi_condition.json",
    )

    operational_metadata_path = save_benchmark_metadata(
        operational_examples,
        "operational_risk_multi_condition_metadata.json",
        task_name="operational_risk",
    )

    n_operational_positive = sum(
        row["target"] == 1
        for row in operational_examples
    )

    print("\nOperational risk benchmark")
    print(f"Saved benchmark to: {operational_output_path}")
    print(f"Saved metadata to: {operational_metadata_path}")
    print(f"Examples: {len(operational_examples)}")
    print(f"High risk: {n_operational_positive}")
    print(
        f"Low risk: "
        f"{len(operational_examples) - n_operational_positive}"
    )

    if operational_examples:
        print(
            f"Positive ratio: "
            f"{n_operational_positive / len(operational_examples):.2%}"
        )

    # ------------------------------------------------------------
    # Safety risk benchmark
    # Uses raw ClinicalTrials.gov studies with posted results.
    # ------------------------------------------------------------

    safety_examples = []

    for condition in conditions:
        filename = f"{condition}_raw_trials.json"

        try:
            raw_data = load_raw_trials(filename)
        except FileNotFoundError:
            print(f"Skipping safety benchmark for {condition}")
            continue

        benchmark = build_safety_risk_benchmark(
            raw_data.get("studies", [])
        )

        for row in benchmark:
            row["source_condition"] = condition

        safety_examples.extend(benchmark)

    safety_output_path = save_benchmark(
        safety_examples,
        "safety_risk_multi_condition.json",
    )

    safety_metadata_path = save_benchmark_metadata(
        safety_examples,
        "safety_risk_multi_condition_metadata.json",
        task_name="safety_risk",
    )

    n_safety_positive = sum(
        row["target"] == 1
        for row in safety_examples
    )

    print("\nSafety risk benchmark")
    print(f"Saved benchmark to: {safety_output_path}")
    print(f"Saved metadata to: {safety_metadata_path}")
    print(f"Examples: {len(safety_examples)}")
    print(f"High risk: {n_safety_positive}")
    print(f"Low risk: {len(safety_examples) - n_safety_positive}")

    if safety_examples:
        print(
            f"Positive ratio: "
            f"{n_safety_positive / len(safety_examples):.2%}"
        )




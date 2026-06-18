import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

PROCESSED_DIR = DATA_DIR / "processed" / "v0_1"
BENCHMARK_DIR = DATA_DIR / "benchmarks" / "v0_1"


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

    all_examples = []

    for condition in conditions:
        filename = f"{condition}_trials.json"

        try:
            trials = load_processed_trials(filename)
        except FileNotFoundError:
            print(f"Skipping {condition}: {filename} not found")
            continue

        benchmark = build_operational_risk_benchmark(trials)

        for row in benchmark:
            row["source_condition"] = condition

        all_examples.extend(benchmark)

    output_path = save_benchmark(
        all_examples,
        "operational_risk_multi_condition.json",
    )

    n_positive = sum(
        row["target"] == 1
        for row in all_examples
    )

    n_negative = len(all_examples) - n_positive

    print(f"Saved benchmark to: {output_path}")
    print(f"Number of examples: {len(all_examples)}")
    print(f"High risk: {n_positive}")
    print(f"Low risk: {n_negative}")

    if all_examples:
        print(
            f"Positive ratio: "
            f"{n_positive / len(all_examples):.2%}"
        )

    output_path = save_benchmark(
        all_examples,
        "operational_risk_multi_condition.json",
    )

    metadata_path = save_benchmark_metadata(
        all_examples,
        "operational_risk_multi_condition_metadata.json",
        task_name="operational_risk",
    )

    print(f"Saved metadata to: {metadata_path}")


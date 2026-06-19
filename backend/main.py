from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from ct_io.clinicaltrials_api import fetch_trials
from pipelines.preprocessing_pipeline import flatten_trials
from services.trial_storage import (
    load_processed_trials,
    save_raw_trials,
    save_processed_trials,
    save_metadata,
)
from pathlib import Path
import json
from pydantic import BaseModel
from pipelines.benchmark_pipeline import (
    build_operational_risk_benchmark,
    save_benchmark,
    save_benchmark_metadata,
)
from models.train_risk_model import train_risk_model

app = FastAPI(title="Clinical Trial Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BenchmarkGenerationRequest(BaseModel):
    task: str = "operational_risk"
    conditions: list[str]
    page_size: int = 500
    version: str = "v0_1"

@app.post("/benchmarks/generate")
def generate_benchmark(request: BenchmarkGenerationRequest):
    if request.task != "operational_risk":
        return {
            "success": False,
            "message": "Only operational_risk is supported for now.",
        }

    all_examples = []

    for condition in request.conditions:
        raw = fetch_trials(
            condition=condition,
            page_size=request.page_size,
        )

        trials = flatten_trials(raw)

        save_raw_trials(raw, f"{condition}_raw_trials.json")
        save_processed_trials(trials, f"{condition}_trials.json")
        save_metadata(
            condition=condition,
            page_size=request.page_size,
            n_raw_studies=len(raw.get("studies", [])),
            n_processed_trials=len(trials),
            filename=f"{condition}_metadata.json",
        )

        benchmark = build_operational_risk_benchmark(
            [trial.model_dump() for trial in trials]
        )

        for row in benchmark:
            row["source_condition"] = condition

        all_examples.extend(benchmark)

    output_path = save_benchmark(
        all_examples,
        "operational_risk_multi_condition.json",
    )

    metadata_path = save_benchmark_metadata(
        all_examples,
        "operational_risk_multi_condition_metadata.json",
        task_name="operational_risk",
    )

    n_positive = sum(row["target"] == 1 for row in all_examples)
    n_examples = len(all_examples)
    n_negative = n_examples - n_positive

    return {
        "success": True,
        "task": request.task,
        "n_examples": n_examples,
        "n_positive": n_positive,
        "n_negative": n_negative,
        "positive_ratio": n_positive / n_examples if n_examples else 0,
        "source_conditions": request.conditions,
        "benchmark_path": str(output_path),
        "metadata_path": str(metadata_path),
    }

@app.get("/")
def root():
    return {"message": "CTD backend running"}


@app.get("/trials")
def get_trials(
    condition: str = Query(default="autism"),
    page_size: int = Query(default=100, ge=1, le=1000),
    refresh: bool = Query(default=False),
):
    processed_filename = f"{condition}_trials.json"

    if not refresh:
        saved_trials = load_processed_trials(processed_filename)

        if saved_trials:
            return {
                "source": "processed",
                "total_count": len(saved_trials),
                "trials": saved_trials,
            }

    raw = fetch_trials(condition=condition, page_size=page_size)
    trials = flatten_trials(raw)

    save_raw_trials(raw, f"{condition}_raw_trials.json")
    save_processed_trials(trials, processed_filename)
    save_metadata(
        condition=condition,
        page_size=page_size,
        n_raw_studies=len(raw.get("studies", [])),
        n_processed_trials=len(trials),
        filename=f"{condition}_metadata.json",
    )

    return {
        "source": "clinicaltrials.gov",
        "total_count": raw.get("totalCount"),
        "trials": trials,
    }

@app.get("/benchmark/risk-overview")
def get_risk_benchmark_overview():
    metadata_path = (
        Path(__file__).resolve().parent
        / "data"
        / "benchmarks"
        / "v0_1"
        / "operational_risk_multi_condition_metadata.json"
    )

    operational = {
        "name": "Operational",
        "status": "available",
        "n_examples": None,
        "n_positive": None,
        "positive_ratio": None,
    }

    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)

        operational.update({
            "n_examples": metadata["n_examples"],
            "n_positive": metadata["n_positive"],
            "positive_ratio": metadata["positive_ratio"],
        })

    return {
        "title": "Risk Benchmark Overview",
        "description": (
            "Integrated benchmark framework for safety, efficacy, "
            "and operational risk assessment."
        ),
        "benchmarks": [
            {
                "name": "Safety",
                "status": "planned",
                "description": "Adverse-event based risk prediction.",
            },
            {
                "name": "Efficacy",
                "status": "planned",
                "description": "Outcome and endpoint success prediction.",
            },
            {
                "name": "Operational",
                "status": operational["status"],
                "description": "Termination, withdrawal, or suspension risk.",
                "n_examples": operational["n_examples"],
                "n_positive": operational["n_positive"],
                "positive_ratio": operational["positive_ratio"],
            },
        ],
    }

class ModelTrainingRequest(BaseModel):
    benchmark: str
    model: str


@app.post("/models/train")
def train_model(request: ModelTrainingRequest):

    results = train_risk_model(
        request.benchmark,
        request.model,
    )

    return {
        "success": True,
        **results,
    }


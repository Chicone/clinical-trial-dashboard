from fastapi import FastAPI, Query, HTTPException
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
    build_safety_risk_benchmark,
    build_unified_risk_benchmark,
    save_benchmark,
    save_unified_benchmark_metadata,
)
from models.train_risk_model import train_risk_model
from routers import benchmarks

app = FastAPI(title="Clinical Trial Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(benchmarks.router)

class BenchmarkGenerationRequest(BaseModel):
    task: str = "operational_risk"
    conditions: list[str]
    page_size: int = 500
    version: str = "v0_1"

@app.post("/benchmarks/generate")
def generate_benchmark(request: BenchmarkGenerationRequest):
    operational_examples = []
    safety_examples = []

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

        operational_benchmark = build_operational_risk_benchmark(
            [trial.model_dump() for trial in trials]
        )

        for row in operational_benchmark:
            row["source_condition"] = condition

        operational_examples.extend(operational_benchmark)

        safety_benchmark = build_safety_risk_benchmark(
            raw.get("studies", [])
        )

        for row in safety_benchmark:
            row["source_condition"] = condition

        safety_examples.extend(safety_benchmark)

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

    operational_valid = [
        row for row in unified_examples
        if row.get("operational_risk") is not None
    ]

    operational_positive = sum(
        row["operational_risk"] == 1
        for row in operational_valid
    )

    return {
        "success": True,
        "task": "unified_risk",
        "n_examples": len(unified_examples),
        "n_positive": operational_positive,
        "n_negative": len(operational_valid) - operational_positive,
        "positive_ratio": (
            operational_positive / len(operational_valid)
            if operational_valid
            else 0
        ),
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
        / "unified_risk_multi_condition_metadata.json"
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
    risk_type: str
    model: str


from pathlib import Path
import json

BENCHMARK_DIR = Path("data/benchmarks/v0_1")


@app.post("/models/train")
def train_model(request: ModelTrainingRequest):
    benchmark_path = BENCHMARK_DIR / f"{request.benchmark}.json"

    if not benchmark_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Benchmark not found: {request.benchmark}",
        )

    with benchmark_path.open("r", encoding="utf-8") as f:
        benchmark_data = json.load(f)

    allowed_risk_types = {
        "operational_risk",
        "safety_risk",
        "efficacy_risk",
    }

    if request.risk_type not in allowed_risk_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid risk type: {request.risk_type}",
        )

    rows = [
        row for row in benchmark_data
        if row.get(request.risk_type) is not None
    ]

    if not rows:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No valid labels found for risk type: "
                f"{request.risk_type}"
            ),
        )

    labels = {row[request.risk_type] for row in rows}

    if len(labels) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot train {request.risk_type}: "
                f"only one class is present: {labels}"
            ),
        )

    return train_risk_model(
        data=rows,
        benchmark_name=request.benchmark,
        risk_type=request.risk_type,
        model_name=request.model,
    )


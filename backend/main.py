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

app = FastAPI(title="Clinical Trial Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "CTD backend running"}


@app.get("/trials")
def get_trials(
    condition: str = Query(default="autism"),
    page_size: int = Query(default=50, ge=1, le=100),
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
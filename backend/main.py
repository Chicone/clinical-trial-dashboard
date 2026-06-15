from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from ct_io.clinicaltrials_api import fetch_trials
from pipelines.preprocessing_pipeline import flatten_trials

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
    condition: str = Query(default="high functioning autism"),
    page_size: int = Query(default=50, ge=1, le=100),
):
    raw = fetch_trials(condition=condition, page_size=page_size)
    return {
        "total_count": raw.get("totalCount"),
        "trials": flatten_trials(raw),
    }
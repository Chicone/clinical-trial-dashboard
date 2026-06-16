"""
Utilities for saving clinical trial data.

Raw data is stored unchanged for reproducibility.
Processed data is normalized to the canonical Trial schema
and used by the dashboard and future ML pipelines.
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
from schemas.trial import Trial

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

# Original API responses
RAW_CT_DIR = DATA_DIR / "raw" / "clinicaltrials_gov"

# Versioned normalized datasets
PROCESSED_V01_DIR = DATA_DIR / "processed" / "v0_1"


def ensure_data_dirs() -> None:
    RAW_CT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_V01_DIR.mkdir(parents=True, exist_ok=True)


def save_raw_trials(api_response: dict[str, Any], filename: str) -> Path:
    ensure_data_dirs()

    path = RAW_CT_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(api_response, f, indent=2, ensure_ascii=False)

    return path


def save_processed_trials(
    trials: list[Trial],
    filename: str = "trials.json",
) -> Path:
    ensure_data_dirs()

    path = PROCESSED_V01_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            [trial.model_dump() for trial in trials],
            f,
            indent=2,
            ensure_ascii=False,
        )

    return path

def save_metadata(
    condition: str,
    page_size: int,
    n_raw_studies: int,
    n_processed_trials: int,
    filename: str,
) -> Path:
    ensure_data_dirs()

    metadata = {
        "source": "clinicaltrials.gov",
        "condition": condition,
        "page_size": page_size,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "n_raw_studies": n_raw_studies,
        "n_processed_trials": n_processed_trials,
        "schema_version": "v0_1",
    }

    path = PROCESSED_V01_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return path

def load_processed_trials(filename: str) -> list[dict]:
    """
    Load normalized trials from the processed data directory.
    """
    path = PROCESSED_V01_DIR / filename

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
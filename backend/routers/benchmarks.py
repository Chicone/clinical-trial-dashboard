# backend/routers/benchmarks.py

from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

BENCHMARK_DIR = Path("data/benchmarks/v0_1")


@router.get("/benchmarks")
def list_benchmarks():
    benchmarks = []

    if not BENCHMARK_DIR.exists():
        return {"benchmarks": []}

    for path in BENCHMARK_DIR.glob("*.json"):

        if "metadata" in path.stem.lower():
            continue

        benchmark_id = path.stem

        name = benchmark_id.replace("_", " ").title()

        benchmarks.append({
            "id": benchmark_id,
            "name": name,
            "version": "v0_1",
        })
    return {"benchmarks": benchmarks}
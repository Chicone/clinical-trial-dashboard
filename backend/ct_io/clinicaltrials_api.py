import requests


BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


def fetch_trials(condition: str = "breast cancer", page_size: int = 50) -> dict:
    params = {
        "query.cond": condition,
        "pageSize": page_size,
        "format": "json",
        "countTotal": "true",
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()
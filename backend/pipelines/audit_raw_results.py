import json

INPUT_FILE = (
    "backend/data/raw/clinicaltrials_gov/autism_raw_trials.json"
)

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

studies = data["studies"]

n_results = 0
n_adverse = 0
n_outcomes = 0

for study in studies:

    if study.get("hasResults"):
        n_results += 1

    results = study.get("resultsSection", {})

    if "adverseEventsModule" in results:
        n_adverse += 1

    if "outcomeMeasuresModule" in results:
        n_outcomes += 1

print(f"Studies:                {len(studies)}")
print(f"hasResults=True:        {n_results}")
print(f"adverseEventsModule:    {n_adverse}")
print(f"outcomeMeasuresModule:  {n_outcomes}")
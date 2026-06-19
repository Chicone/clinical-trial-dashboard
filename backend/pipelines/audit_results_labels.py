import json
from pprint import pprint

INPUT_FILE = "backend/data/raw/clinicaltrials_gov/autism_raw_trials.json"

with open(INPUT_FILE) as f:
    data = json.load(f)

for study in data["studies"]:
    if not study.get("hasResults"):
        continue

    nct_id = study["protocolSection"]["identificationModule"]["nctId"]
    results = study.get("resultsSection", {})

    adverse = results.get("adverseEventsModule", {})
    outcomes = results.get("outcomeMeasuresModule", {})

    print("\nNCT ID:", nct_id)

    print("\nAdverse event groups:")
    pprint(adverse.get("eventGroups", [])[:2])

    print("\nFirst outcome measure:")
    pprint(outcomes.get("outcomeMeasures", [])[:1])

    break
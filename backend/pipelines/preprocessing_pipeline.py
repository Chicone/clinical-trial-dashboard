def _join(values):
    if not values:
        return None
    if isinstance(values, list):
        return ", ".join(str(v) for v in values if v)
    return str(values)


def flatten_study(study: dict) -> dict:
    protocol = study.get("protocolSection", {})

    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    conditions = protocol.get("conditionsModule", {})
    arms = protocol.get("armsInterventionsModule", {})
    outcomes = protocol.get("outcomesModule", {})
    eligibility = protocol.get("eligibilityModule", {})

    lead_sponsor = sponsor.get("leadSponsor", {})
    enrollment_info = design.get("enrollmentInfo", {})

    interventions = arms.get("interventions", [])
    primary_outcomes = outcomes.get("primaryOutcomes", [])

    return {
        "nct_id": identification.get("nctId"),
        "title": identification.get("briefTitle"),
        "official_title": identification.get("officialTitle"),

        "status": status.get("overallStatus"),
        "start_date": status.get("startDateStruct", {}).get("date"),
        "completion_date": status.get("completionDateStruct", {}).get("date"),

        "phase": _join(design.get("phases")),
        "study_type": design.get("studyType"),
        "enrollment": enrollment_info.get("count"),
        "enrollment_type": enrollment_info.get("type"),

        "sponsor": lead_sponsor.get("name"),
        "sponsor_class": lead_sponsor.get("class"),

        "conditions": _join(conditions.get("conditions")),
        "interventions": _join([i.get("name") for i in interventions]),
        "intervention_types": _join([i.get("type") for i in interventions]),

        "primary_outcomes": _join([o.get("measure") for o in primary_outcomes]),

        "sex": eligibility.get("sex"),
        "minimum_age": eligibility.get("minimumAge"),
        "maximum_age": eligibility.get("maximumAge"),
    }


def flatten_trials(api_response: dict) -> list[dict]:
    return [flatten_study(study) for study in api_response.get("studies", [])]
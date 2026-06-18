from schemas.trial import Trial

HIGH_OPERATIONAL_RISK_STATUSES = {
    "TERMINATED",
    "WITHDRAWN",
    "SUSPENDED",
}

def _join(values):
    if not values:
        return None
    if isinstance(values, list):
        return ", ".join(str(v) for v in values if v)
    return str(values)


def normalize_study(study: dict) -> Trial:
    protocol = study.get("protocolSection", {})

    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    trial_status = status.get("overallStatus")
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

    description = protocol.get("descriptionModule", {})
    contacts_locations = protocol.get("contactsLocationsModule", {})

    return Trial(
        source="clinicaltrials.gov",

        nct_id=identification.get("nctId"),
        title=identification.get("briefTitle"),
        official_title=identification.get("officialTitle"),

        status=trial_status,
        operational_risk=int(trial_status in HIGH_OPERATIONAL_RISK_STATUSES),
        start_date=status.get("startDateStruct", {}).get("date"),
        completion_date=status.get("completionDateStruct", {}).get("date"),

        phase=_join(design.get("phases")),
        study_type=design.get("studyType"),

        enrollment=enrollment_info.get("count"),

        sponsor=lead_sponsor.get("name"),

        conditions=conditions.get("conditions", []),

        interventions=[
            i.get("name")
            for i in interventions
            if i.get("name")
        ],

        primary_outcomes=[
            o.get("measure")
            for o in primary_outcomes
            if o.get("measure")
        ],

        sex=eligibility.get("sex"),
        minimum_age=eligibility.get("minimumAge"),
        maximum_age=eligibility.get("maximumAge"),

        brief_summary=description.get("briefSummary"),
        detailed_description=description.get("detailedDescription"),
    )


def flatten_trials(api_response: dict) -> list[Trial]:
    return [normalize_study(study) for study in api_response.get("studies", [])]
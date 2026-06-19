from pydantic import BaseModel, Field
from typing import Optional


class Trial(BaseModel):
    # Identifiers
    nct_id: str
    source: str = "clinicaltrials.gov"

    # Basic information
    title: str
    official_title: Optional[str] = None
    brief_summary: Optional[str] = None
    detailed_description: Optional[str] = None

    # Study design
    study_type: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None

    # Dates
    start_date: Optional[str] = None
    primary_completion_date: Optional[str] = None
    completion_date: Optional[str] = None

    # Sponsor
    sponsor: Optional[str] = None

    # Medical context
    conditions: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)

    # Population
    enrollment: Optional[int] = None
    sex: Optional[str] = None
    minimum_age: Optional[str] = None
    maximum_age: Optional[str] = None

    # Outcomes
    primary_outcomes: list[str] = Field(default_factory=list)
    secondary_outcomes: list[str] = Field(default_factory=list)

    # Future risk labels
    safety_risk: Optional[int] = None
    efficacy_risk: Optional[int] = None
    operational_risk: Optional[int] = None

    # Future embeddings / multimodal features
    protocol_embedding_id: Optional[str] = None
    molecular_graph_id: Optional[str] = None

    # Results / stopping information
    has_results: Optional[bool] = None
    why_stopped: Optional[str] = None

    # Safety signals
    serious_adverse_events: Optional[int] = None
    other_adverse_events: Optional[int] = None

    # Efficacy signals
    primary_outcome_results: list[str] = Field(default_factory=list)
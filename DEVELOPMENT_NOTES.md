# CTD Development Notes

## Project vision

The Clinical Trial Dashboard (CTD) is being developed as the first layer of a broader multimodal clinical trial intelligence platform.

The long-term objective is not only to display clinical trials, but to build the foundations for AI-based clinical trial risk assessment. The platform should eventually support the prediction and analysis of safety risk, efficacy risk, and operational risk by combining multiple data modalities, including structured trial metadata, protocol text, adverse events, outcomes, drug information, molecular data, and external benchmark datasets.

At this stage, the CTD acts as the data ingestion, normalization, storage, and exploration layer. The dashboard is therefore not treated as a standalone frontend application, but as the visible interface over a growing benchmark-building platform.

## Current architecture

The current backend pipeline follows this structure:

```text
ClinicalTrials.gov API
        ↓
Raw API response
        ↓
Raw data storage
        ↓
Normalization into canonical Trial schema
        ↓
Processed dataset storage
        ↓
Metadata generation
        ↓
Frontend dashboard
```

This architecture separates raw external data from normalized internal data. Raw data is preserved unchanged for reproducibility and debugging. Processed data is converted into a stable internal schema that can be used consistently by the dashboard, analytics modules, and future machine learning pipelines.

## Current capabilities

The CTD currently supports the following functionality:

* Fetches clinical trial data from ClinicalTrials.gov.
* Accepts a condition query, such as `autism`.
* Retrieves a configurable number of trials through the backend API.
* Normalizes raw ClinicalTrials.gov JSON into a canonical `Trial` schema.
* Stores raw API responses under:

```text
backend/data/raw/clinicaltrials_gov/
```

* Stores processed normalized trial datasets under:

```text
backend/data/processed/v0_1/
```

* Generates metadata files describing how each processed dataset was created.
* Serves trials from the local processed dataset when available.
* Supports a `refresh=true` query parameter to force a new ingestion from ClinicalTrials.gov.
* Returns normalized trial data to the React frontend.
* Displays trial information in the dashboard.
* Supports filtering and expandable trial details in the frontend.

## Canonical Trial schema

A key architectural step was the introduction of a canonical `Trial` schema.

Instead of allowing the frontend and future AI modules to depend directly on the raw ClinicalTrials.gov API structure, raw trials are now converted into a stable internal representation.

This makes the project more robust because future data sources can be mapped into the same schema. For example, CT-ADE, CliniFact, DeepCTRisk, and other benchmark datasets can later be integrated without forcing the frontend or machine learning code to understand each source-specific format.

The guiding principle is:

```text
External data source → source-specific parser → canonical Trial object
```

This canonical schema is the basis for future benchmark creation and model development.

## Raw and processed data

The project now distinguishes between raw and processed data.

Raw data is the original response from the external API. It is stored unchanged and should be treated as the source of truth.

Processed data is the normalized representation produced from the raw data. It follows the canonical `Trial` schema and is the version used by the dashboard and future analytics or machine learning modules.

This distinction is important because it allows the project to remain reproducible. If a preprocessing bug is discovered later, the raw data can be reprocessed without needing to query the external API again.

## Metadata files

For each processed dataset, a metadata file is created.

The metadata records information such as:

* Data source
* Query condition
* Requested page size
* Retrieval time
* Number of raw studies
* Number of processed trials
* Schema version

This makes each dataset auditable. Later, when comparing model results or benchmark versions, it will be possible to know exactly how each dataset was produced.

## Serving versus ingestion

The project now has an initial separation between ingestion and serving.

Previously, every frontend request triggered a new call to ClinicalTrials.gov.

The current behavior is better:

```text
If a processed dataset exists:
    load local processed data

If no processed dataset exists:
    fetch from ClinicalTrials.gov, normalize, save, and return

If refresh=true:
    force a new ClinicalTrials.gov fetch and overwrite the saved data
```

This improves reproducibility and reduces unnecessary dependency on the external API.

The `refresh=true` parameter is currently used as a pragmatic bridge between ingestion and serving. In the future, ingestion should probably be moved to a dedicated endpoint or standalone pipeline script.

## Why this matters

This architecture moves the CTD beyond a simple dashboard.

The project now has the beginning of a real data platform:

* External data ingestion
* Raw data preservation
* Canonical schema normalization
* Versioned processed datasets
* Dataset metadata
* Frontend exploration
* Future benchmark support

This is essential for the long-term goal of building an integrated clinical trial risk assessment system.

## Near-term next steps

The next development priorities are:

1. Make ingestion and serving fully separate.

   The dashboard should primarily serve existing processed datasets. Data ingestion should eventually be triggered by a dedicated endpoint or script.

2. Expand the `Trial` schema.

   Important future fields include adverse events, trial results, eligibility criteria, protocol amendments, outcome timeframes, locations, and sponsor details.

3. Improve dataset versioning.

   The current processed dataset version is `v0_1`. Future schema or preprocessing changes should create new versions rather than silently overwriting old assumptions.

4. Add benchmark construction logic.

   The processed trial datasets should eventually be transformed into benchmark-ready tables for machine learning.

5. Define risk labels.

   Future model development will require explicit definitions of safety risk, efficacy risk, and operational risk.

6. Add baseline models.

   Before using transformers or graph neural networks, the project should establish classical machine learning baselines such as logistic regression, random forests, and gradient boosting.

7. Integrate additional datasets.

   Future sources may include CT-ADE, CliniFact, DeepCTRisk, and other open clinical trial datasets.

## Long-term direction

The long-term goal is to evolve the CTD into a multimodal clinical trial intelligence platform.

The future system should support:

* Structured trial metadata analysis
* Protocol text processing
* Adverse event and outcome extraction
* Drug and intervention linking
* Molecular structure integration
* Knowledge graph construction
* Transformer-based trial representations
* GNN-based relational modeling
* Multitask prediction of safety, efficacy, and operational risks
* Retrospective and prospective model evaluation

The dashboard should remain the user-facing interface, but the real value of the project will come from the underlying benchmark dataset, data model, and machine learning infrastructure.

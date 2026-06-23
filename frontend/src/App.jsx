import { useEffect, useState } from "react";
import "./App.css";

function App() {
// Navigation
const [activeView, setActiveView] = useState("trials");

// ------------------------------------------------------------------
// Trial Browser
// ------------------------------------------------------------------

const [trials, setTrials] = useState([]);
const [selectedTrial, setSelectedTrial] = useState(null);
const [loading, setLoading] = useState(true);

// Search configuration
const [condition, setCondition] = useState("autism");
const [conditionInput, setConditionInput] = useState("autism");
const [pageSize, setPageSize] = useState(100);

// Trial filters and sorting
const [phaseFilter, setPhaseFilter] = useState("all");
const [statusFilter, setStatusFilter] = useState("all");
const [sortBy, setSortBy] = useState("relevance");


// ------------------------------------------------------------------
// Benchmark Builder
// ------------------------------------------------------------------

// Benchmark overview displayed in the dashboard
const [riskOverview, setRiskOverview] = useState(null);

// Benchmark generation parameters
const [benchmarkConditions, setBenchmarkConditions] = useState(
  "autism, depression, psoriasis, diabetes"
);

const [benchmarkPageSize, setBenchmarkPageSize] = useState(500);

// Benchmark generation state
const [generatingBenchmark, setGeneratingBenchmark] = useState(false);
const [benchmarkResult, setBenchmarkResult] = useState(null);


// ------------------------------------------------------------------
// Model Lab
// ------------------------------------------------------------------

// Selected model configuration
const [selectedModel, setSelectedModel] =
  useState("logistic_regression");

const [selectedDataset, setSelectedDataset] =
  useState("operational_risk_multi_condition");

const [selectedRiskType, setSelectedRiskType] =
  useState("operational_risk");

const [availableBenchmarks, setAvailableBenchmarks] = useState([]);
const [selectedBenchmark, setSelectedBenchmark] = useState("");

// Training state and results
const [trainingResults, setTrainingResults] = useState(null);
const [training, setTraining] = useState(false);

useEffect(() => {
  fetch("http://localhost:8000/benchmarks")
    .then((res) => res.json())
    .then((data) => {
      const benchmarks = data.benchmarks || [];

      setAvailableBenchmarks(benchmarks);

      if (benchmarks.length > 0) {
        setSelectedBenchmark(benchmarks[0].id);
      }
    })
    .catch((err) => {
      console.error("Failed to load benchmarks:", err);
    });
}, []);

  useEffect(() => {
    setLoading(true);
    setSelectedTrial(null);

    fetch(
      `http://localhost:8000/trials?condition=${encodeURIComponent(
        condition
      )}&page_size=${pageSize}`
    )
      .then((res) => res.json())
      .then((data) => {
        setTrials(data.trials || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load clinical trials:", err);
        setLoading(false);
      });
  }, [condition, pageSize]);

  const loadRiskOverview = () => {
    fetch(`http://localhost:8000/benchmark/risk-overview?t=${Date.now()}`)
      .then((res) => res.json())
      .then((data) => setRiskOverview(data))
      .catch((err) => {
        console.error("Failed to load risk overview:", err);
    });
  };

  useEffect(() => {
    loadRiskOverview();
  }, []);

  const filteredTrials = trials
    .filter((trial) => {
      const phaseMatches =
        phaseFilter === "all" || trial.phase === phaseFilter;

      const statusMatches =
        statusFilter === "all" || trial.status === statusFilter;

      return phaseMatches && statusMatches;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "enrollment":
          return (b.enrollment || 0) - (a.enrollment || 0);

        case "start_date":
          return new Date(b.start_date || 0) - new Date(a.start_date || 0);

        case "recruiting":
          return (
            (b.status === "RECRUITING") -
            (a.status === "RECRUITING")
          );

        default:
          return 0;
      }
    });

  const getStatusClass = (status) => {
    if (!status) return "badge neutral";

    const value = status.toLowerCase();

    if (value.includes("recruiting")) return "badge success";
    if (value.includes("completed")) return "badge info";
    if (value.includes("terminated")) return "badge danger";
    if (value.includes("withdrawn")) return "badge warning";

    return "badge neutral";
  };

  const generateBenchmark = () => {
    const conditions = benchmarkConditions
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    setGeneratingBenchmark(true);
    loadRiskOverview();
    setBenchmarkResult(null);

    fetch("http://localhost:8000/benchmarks/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        task: "operational_risk",
        conditions,
        page_size: benchmarkPageSize,
        version: "v0_1",
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setBenchmarkResult(data);

        setRiskOverview((prev) => {
          if (!prev) return prev;

          return {
            ...prev,
            benchmarks: prev.benchmarks.map((item) =>
              item.name === "Operational"
                ? {
                    ...item,
                    status: "available",
                    n_examples: data.n_examples,
                    n_positive: data.n_positive,
                    n_negative: data.n_negative,
                    positive_ratio: data.positive_ratio,
                    source_conditions: data.source_conditions || item.source_conditions,
                  }
                : item
            ),
          };
        });

        setGeneratingBenchmark(false);
      })
      .catch((err) => {
        console.error("Failed to generate benchmark:", err);
        setGeneratingBenchmark(false);
      });
  };

  const trainModel = () => {
      if (!selectedBenchmark) {
        console.error("No benchmark selected");
        return;
      }

      setTraining(true);

      fetch("http://localhost:8000/models/train", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          benchmark: selectedBenchmark,
          risk_type: selectedRiskType,
          model: selectedModel,
        }),
      })
        .then(async (res) => {
          const data = await res.json();

          if (!res.ok) {
            throw new Error(data.detail || "Training failed");
          }

          return data;
        })
        .then((data) => {
          setTrainingResults(data);
          setTraining(false);
        })
        .catch((err) => {
          console.error(err);
          alert(err.message);
          setTraining(false);
        });
    };

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>CT Dashboard</h2>

        <button
          className={activeView === "trials" ? "active-nav" : ""}
          onClick={() => setActiveView("trials")}
        >
          Trial Browser
        </button>

        <button
          className={activeView === "benchmarks" ? "active-nav" : ""}
          onClick={() => setActiveView("benchmarks")}
        >
          Benchmarks
        </button>

        <button
          className={activeView === "models" ? "active-nav" : ""}
          onClick={() => setActiveView("models")}
        >
          Model Lab
        </button>

        <button
          className={activeView === "logs" ? "active-nav" : ""}
          onClick={() => setActiveView("logs")}
        >
          Logs
        </button>
      </aside>

      <main className="main">
        {activeView === "trials" && (
          <>
            <h1>Trial Browser</h1>

            <div className="search-bar">
              <input
                className="search-input"
                type="text"
                value={conditionInput}
                onChange={(e) => setConditionInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    setCondition(conditionInput);
                  }
                }}
                placeholder="Search condition, e.g. psoriasis"
              />

              <input
                className="page-size-input"
                type="number"
                min="1"
                max="1000"
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
              />

              <button
                className="search-button"
                onClick={() => setCondition(conditionInput)}
              >
                Search
              </button>
            </div>

            <div className="filter-bar">
              <select
                value={phaseFilter}
                onChange={(e) => setPhaseFilter(e.target.value)}
              >
                <option value="all">All phases</option>
                <option value="PHASE1">Phase 1</option>
                <option value="PHASE2">Phase 2</option>
                <option value="PHASE3">Phase 3</option>
                <option value="PHASE4">Phase 4</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All statuses</option>
                <option value="RECRUITING">Recruiting</option>
                <option value="COMPLETED">Completed</option>
                <option value="TERMINATED">Terminated</option>
                <option value="WITHDRAWN">Withdrawn</option>
                <option value="ACTIVE_NOT_RECRUITING">
                  Active, not recruiting
                </option>
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="relevance">Relevance</option>
                <option value="start_date">Newest start date</option>
                <option value="enrollment">Largest enrollment</option>
                <option value="recruiting">Recruiting first</option>
              </select>
            </div>

            <p className="result-count">
              Showing {filteredTrials.length} of {trials.length} trials
            </p>

            {loading && <p>Loading trials...</p>}

            {!loading && (
              <div className="layout">
                <section className="trial-list">
                  {filteredTrials.length === 0 ? (
                    <div className="empty-state">
                      No trials found. Try another condition or relax the
                      filters.
                    </div>
                  ) : (
                    filteredTrials.map((trial, index) => (
                      <div
                        key={trial.nct_id || index}
                        className={`trial-card ${
                          selectedTrial === trial ? "selected" : ""
                        }`}
                        onClick={() => setSelectedTrial(trial)}
                      >
                        <h3>
                          {trial.title ||
                            trial.brief_title ||
                            "Untitled trial"}
                        </h3>

                        <div className="badge-row">
                          <span className={getStatusClass(trial.status)}>
                            {trial.status || "No status"}
                          </span>

                          <span className="badge phase">
                            {trial.phase || "No phase"}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </section>

                <section className="trial-detail">
                  {selectedTrial ? (
                    <>
                      <h2>{selectedTrial.title}</h2>

                      <div className="badge-row detail-badges">
                        <span className={getStatusClass(selectedTrial.status)}>
                          {selectedTrial.status || "No status"}
                        </span>

                        <span className="badge phase">
                          {selectedTrial.phase || "No phase"}
                        </span>
                      </div>

                      <div className="risk-panel">
                        <h3>Risk Assessment</h3>

                        <div className="risk-grid">
                          <div>
                            <span>Safety</span>
                            <strong>N/A</strong>
                          </div>

                          <div>
                            <span>Efficacy</span>
                            <strong>N/A</strong>
                          </div>

                          <div>
                            <span>Operational</span>
                            <strong
                              style={{
                                color:
                                  selectedTrial.operational_risk === 1
                                    ? "#dc2626"
                                    : "#16a34a",
                              }}
                            >
                              {selectedTrial.operational_risk === 1
                                ? "High"
                                : "Low"}
                            </strong>
                          </div>
                        </div>

                        <p className="risk-note">
                          Operational risk is currently derived from trial
                          status. Safety and efficacy models are under
                          development.
                        </p>
                      </div>

                      <div className="detail-panel">
                        <h3>Trial Details</h3>

                        <div className="detail-grid">
                          <div className="detail-label">ID</div>
                          <div className="detail-value">
                            {selectedTrial.nct_id}
                          </div>

                          <div className="detail-label">Status</div>
                          <div className="detail-value">
                            {selectedTrial.status}
                          </div>

                          <div className="detail-label">Phase</div>
                          <div className="detail-value">
                            {selectedTrial.phase}
                          </div>

                          <div className="detail-label">Study Type</div>
                          <div className="detail-value">
                            {selectedTrial.study_type}
                          </div>

                          <div className="detail-label">Sponsor</div>
                          <div className="detail-value">
                            {selectedTrial.sponsor}
                          </div>

                          <div className="detail-label">Condition</div>
                          <div className="detail-value">
                            {Array.isArray(selectedTrial.conditions)
                              ? selectedTrial.conditions.join(", ")
                              : selectedTrial.conditions}
                          </div>

                          <div className="detail-label">Interventions</div>
                          <div className="detail-value">
                            {Array.isArray(selectedTrial.interventions)
                              ? selectedTrial.interventions.join(", ")
                              : selectedTrial.interventions}
                          </div>

                          <div className="detail-label">Enrollment</div>
                          <div className="detail-value">
                            {selectedTrial.enrollment}
                          </div>

                          <div className="detail-label">Start Date</div>
                          <div className="detail-value">
                            {selectedTrial.start_date}
                          </div>

                          <div className="detail-label">Completion Date</div>
                          <div className="detail-value">
                            {selectedTrial.completion_date}
                          </div>

                          <div className="detail-label">Sex</div>
                          <div className="detail-value">
                            {selectedTrial.sex}
                          </div>

                          <div className="detail-label">Age Range</div>
                          <div className="detail-value">
                            {selectedTrial.minimum_age} -{" "}
                            {selectedTrial.maximum_age}
                          </div>
                        </div>
                      </div>

                      <details className="detail-section">
                        <summary>Summary</summary>
                        <p>
                          {selectedTrial.brief_summary ||
                            "No summary available."}
                        </p>
                      </details>

                      <details className="detail-section">
                        <summary>Eligibility Criteria</summary>
                        <p>
                          {selectedTrial.eligibility_criteria ||
                            "No eligibility criteria available."}
                        </p>
                      </details>

                      <details className="detail-section">
                        <summary>Locations</summary>
                        <p>
                          {selectedTrial.locations ||
                            "No locations available."}
                        </p>
                      </details>

                      <details className="detail-section">
                        <summary>Primary Outcomes</summary>
                        <p>
                          {Array.isArray(selectedTrial.primary_outcomes)
                            ? selectedTrial.primary_outcomes.join(", ")
                            : selectedTrial.primary_outcomes ||
                              "No primary outcomes available."}
                        </p>
                      </details>

                      <a
                        href={`https://clinicaltrials.gov/study/${selectedTrial.nct_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="external-link"
                      >
                        View on ClinicalTrials.gov
                      </a>
                    </>
                  ) : (
                    <p>Select a clinical trial to view details.</p>
                  )}
                </section>
              </div>
            )}
          </>
        )}

        {activeView === "benchmarks" && (
          <>
            <h1>Benchmarks</h1>

<section className="placeholder-panel">
  <h2>Benchmark Builder</h2>

  <label>Conditions</label>
  <textarea
    className="benchmark-input"
    value={benchmarkConditions}
    onChange={(e) => setBenchmarkConditions(e.target.value)}
    rows={3}
  />

  <label>Trials per condition</label>
  <input
    className="page-size-input"
    type="number"
    min="1"
    max="1000"
    value={benchmarkPageSize}
    onChange={(e) => setBenchmarkPageSize(Number(e.target.value))}
  />

  <button
    className="search-button"
    onClick={generateBenchmark}
    disabled={generatingBenchmark}
  >
    {generatingBenchmark ? "Generating..." : "Generate Benchmark"}
  </button>

  {benchmarkResult && (
    <div className="benchmark-result">
      <p>Examples: {benchmarkResult.n_examples}</p>
      <p>High risk: {benchmarkResult.n_positive}</p>
      <p>Low risk: {benchmarkResult.n_negative}</p>
      <p>
        Positive ratio:{" "}
        {(benchmarkResult.positive_ratio * 100).toFixed(2)}%
      </p>
    </div>
  )}
</section>

            {riskOverview ? (
              <section className="benchmark-panel">
                <div>
                  <h2>{riskOverview.title}</h2>
                  <p>{riskOverview.description}</p>
                </div>

                <div className="benchmark-stats">
                  {riskOverview.benchmarks.map((item) => (
                    <div key={item.name}>
                      <span>{item.name} risk</span>

                      {item.status === "available" ? (
                        <>
                          <strong>{item.n_examples}</strong>
                          <small>
                            {item.n_positive} high-risk examples (
                            {(item.positive_ratio * 100).toFixed(2)}%)
                          </small>

                          {item.source_conditions && (
                            <small>
                              Built from:{" "}
                              {item.source_conditions.join(", ")}
                            </small>
                          )}
                        </>
                      ) : (
                        <>
                          <strong>Planned</strong>
                          <small>{item.description}</small>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            ) : (
              <p>Loading benchmark overview...</p>
            )}
          </>
        )}

        {activeView === "models" && (
          <>
            <h1>Model Lab</h1>

            <section className="placeholder-panel">

<div className="model-lab-toolbar">
  <div className="control-group">
    <label>Benchmark</label>

    <select
      value={selectedBenchmark}
      onChange={(e) => setSelectedBenchmark(e.target.value)}
      disabled={availableBenchmarks.length === 0}
    >
      {availableBenchmarks.length === 0 ? (
        <option value="">No benchmarks available</option>
      ) : (
        availableBenchmarks.map((benchmark) => (
          <option key={benchmark.id} value={benchmark.id}>
            {benchmark.name}
          </option>
        ))
      )}
    </select>
  </div>

  <div className="control-group">
    <label>Risk Type</label>

    <select
      value={selectedRiskType}
      onChange={(e) => setSelectedRiskType(e.target.value)}
    >
      <option value="operational_risk">Operational Risk</option>
      <option value="safety_risk">Safety Risk</option>
      <option value="efficacy_risk">Efficacy Risk</option>
    </select>
  </div>

  <div className="control-group">
    <label>Model</label>

    <select
      value={selectedModel}
      onChange={(e) => setSelectedModel(e.target.value)}
    >
      <option value="logistic_regression">Logistic Regression</option>
      <option value="random_forest">Random Forest</option>
      <option value="gradient_boosting">Gradient Boosting</option>
    </select>
  </div>

  <button
    className="train-button"
    onClick={trainModel}
    disabled={training || !selectedBenchmark}
  >
    {training ? "Training..." : "Train Model"}
  </button>
</div>

              {trainingResults && (
                <div className="benchmark-result">

                <div className="metrics-grid">
                  <div className="metric-card">
                    <span className="metric-title">Precision</span>
                    <strong className="metric-value">
                      {trainingResults.precision?.toFixed(3) ?? "N/A"}
                    </strong>
                    <small className="metric-help">False alarms ↓</small>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">Recall</span>
                    <strong className="metric-value">
                      {trainingResults.recall?.toFixed(3) ?? "N/A"}
                    </strong>
                    <small className="metric-help">Risks found ↑</small>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">F1</span>
                    <strong className="metric-value">
                      {trainingResults.f1?.toFixed(3) ?? "N/A"}
                    </strong>
                    <small className="metric-help">Precision-recall balance</small>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">MCC</span>
                    <strong className="metric-value">
                      {trainingResults.mcc?.toFixed(3) ?? "N/A"}
                    </strong>
                    <small className="metric-help">Overall signal</small>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">PR-AUC</span>
                    <strong className="metric-value">
                      {trainingResults.pr_auc?.toFixed(3) ?? "N/A"}
                    </strong>
                    <small className="metric-help">Minority-class performance</small>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">ROC-AUC</span>
                    <strong className="metric-value">
                      {trainingResults.roc_auc?.toFixed(3) ?? "N/A"}
                    </strong>
                    <small className="metric-help">Ranking ability</small>
                  </div>
                </div>

                  {trainingResults.confusion_matrix && (
                  <div className="confusion-matrix">
                    <h3>Confusion Matrix</h3>

                    <div className="confusion-grid">
                      <div></div>
                      <div className="matrix-label">Predicted Low</div>
                      <div className="matrix-label">Predicted High</div>

                      <div className="matrix-label">Actual Low</div>
                      <div className="matrix-cell tn">
                        {trainingResults.confusion_matrix.tn}
                        <span>True Negative</span>
                      </div>
                      <div className="matrix-cell fp">
                        {trainingResults.confusion_matrix.fp}
                        <span>False Positive</span>
                      </div>

                      <div className="matrix-label">Actual High</div>
                      <div className="matrix-cell fn">
                        {trainingResults.confusion_matrix.fn}
                        <span>False Negative</span>
                      </div>
                      <div className="matrix-cell tp">
                        {trainingResults.confusion_matrix.tp}
                        <span>True Positive</span>
                      </div>
                    </div>
                  </div>
                )}

                </div>
              )}

            </section>
          </>
        )}

        {activeView === "logs" && (
          <>
            <h1>Logs</h1>

            <section className="placeholder-panel">
              <h2>System logs</h2>
              <p>
                Pipeline events, ingestion messages, benchmark generation logs,
                and model training logs will be displayed here.
              </p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
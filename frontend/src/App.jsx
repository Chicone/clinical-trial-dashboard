import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [trials, setTrials] = useState([]);
  const [selectedTrial, setSelectedTrial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [condition, setCondition] = useState("autism");
  const [conditionInput, setConditionInput] = useState("autism");
  const [phaseFilter, setPhaseFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("relevance");
  const [pageSize, setPageSize] = useState(100);

  useEffect(() => {
    setLoading(true);
    setSelectedTrial(null);

    fetch(
      `http://localhost:8000/trials?condition=${encodeURIComponent(
        condition
      )}&page_size=${pageSize}&refresh=true`
    )
      .then((res) => res.json())
      .then((data) => {
        console.log("Backend data:", data);
        setTrials(data.trials || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load clinical trials:", err);
        setLoading(false);
      });
  }, [condition, pageSize]);

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
          return (
            new Date(b.start_date || 0) -
            new Date(a.start_date || 0)
          );

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

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>CT Dashboard</h2>
        <button>Clinical Trials</button>
        <button>Logs</button>
      </aside>

      <main className="main">
        <h1>Clinical Trials</h1>

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
            placeholder="Trials"
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
                  No trials found. Try another condition or relax the filters.
                </div>
              ) : (
                filteredTrials.map((trial, index) => (
                  <div
                    key={trial.nct_id || index}
                    className={`trial-card ${
                      selectedTrial === trial ? "selected" : ""
                    }`}
                    onClick={() => {
                      console.log(trial);
                      setSelectedTrial(trial);
                    }}
                  >
                    <h3>
                      {trial.title || trial.brief_title || "Untitled trial"}
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
                   <h3 className="panel-title">Risk Assessment</h3>

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
                      Operational risk is currently derived from trial status.
                      Safety and efficacy models are under development.
                    </p>
                  </div>

              <div className="detail-panel">
                <h3 className="panel-title">Trial Details</h3>
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
                      {selectedTrial.conditions}
                    </div>

                    <div className="detail-label">Interventions</div>
                    <div className="detail-value">
                      {selectedTrial.interventions}
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
                      {selectedTrial.primary_outcomes ||
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
      </main>
    </div>
  );
}

export default App;
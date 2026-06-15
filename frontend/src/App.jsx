import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [trials, setTrials] = useState([]);
  const [selectedTrial, setSelectedTrial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [condition, setCondition] = useState("high functioning autism");
  const [conditionInput, setConditionInput] = useState("high functioning autism");

  useEffect(() => {
      setLoading(true);
      setSelectedTrial(null);
      fetch(`http://localhost:8000/trials?condition=${encodeURIComponent(condition)}`)
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
    }, [condition]);

  const filteredTrials = trials.filter((trial) => {
      const text = [
        trial.title,
        trial.brief_title,
        trial.status,
        trial.overall_status,
        trial.phase,
        trial.condition,
        trial.sponsor,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return true;
    });

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
            placeholder="Search condition, e.g. psoriasis"
          />

          <button
            className="search-button"
            onClick={() => setCondition(conditionInput)}
          >
            Search
          </button>
        </div>

        {loading && <p>Loading trials...</p>}

        {!loading && (
          <div className="layout">
            <section className="trial-list">
              {filteredTrials.map((trial, index) => (
                <div
                  key={trial.ntc_id || index}
                  className={`trial-card ${
                      selectedTrial === trial ? "selected" : ""
                    }`}
                    onClick={() => {
                      console.log(trial);
                      setSelectedTrial(trial);
                    }}                >
                  <h3>{trial.title || trial.brief_title || "Untitled trial"}</h3>
                  <p>{trial.status || trial.overall_status || "No status"}</p>
                  <p>{trial.phase || "No phase"}</p>
                </div>
              ))}
            </section>

            <section className="trial-detail">
              {selectedTrial ? (
                <>
                  <h2>{selectedTrial.title}</h2>

                 <div className="detail-grid">
                  <div className="detail-label">ID</div>
                  <div className="detail-value">{selectedTrial.nct_id}</div>

                  <div className="detail-label">Status</div>
                  <div className="detail-value">{selectedTrial.status}</div>

                  <div className="detail-label">Phase</div>
                  <div className="detail-value">{selectedTrial.phase}</div>

                  <div className="detail-label">Study Type</div>
                  <div className="detail-value">{selectedTrial.study_type}</div>

                  <div className="detail-label">Sponsor</div>
                  <div className="detail-value">{selectedTrial.sponsor}</div>

                  <div className="detail-label">Condition</div>
                  <div className="detail-value">{selectedTrial.conditions}</div>

                  <div className="detail-label">Interventions</div>
                  <div className="detail-value">{selectedTrial.interventions}</div>

                  <div className="detail-label">Enrollment</div>
                  <div className="detail-value">{selectedTrial.enrollment}</div>

                  <div className="detail-label">Start Date</div>
                  <div className="detail-value">{selectedTrial.start_date}</div>

                  <div className="detail-label">Completion Date</div>
                  <div className="detail-value">{selectedTrial.completion_date}</div>

                  <div className="detail-label">Sex</div>
                  <div className="detail-value">{selectedTrial.sex}</div>

                  <div className="detail-label">Age Range</div>
                  <div className="detail-value">
                    {selectedTrial.minimum_age} - {selectedTrial.maximum_age}
                  </div>
                </div>

                  <p>{selectedTrial.primary_outcomes}</p>

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
                      <strong>N/A</strong>
                    </div>
                  </div>

                  <p className="risk-note">
                    Risk models will be connected later using protocol, intervention,
                    safety, efficacy, and operational features.
                  </p>
                </div>
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
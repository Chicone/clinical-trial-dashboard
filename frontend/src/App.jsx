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
                  key={trial.id || trial.nct_id || index}
                  className={`trial-card ${
                      selectedTrial === trial ? "selected" : ""
                    }`}
                  onClick={() => setSelectedTrial(trial)}
                >
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
                  <p><strong>ID:</strong> {selectedTrial.id}</p>
                  <p><strong>Status:</strong> {selectedTrial.status}</p>
                  <p><strong>Phase:</strong> {selectedTrial.phase}</p>
                  <p><strong>Sponsor:</strong> {selectedTrial.sponsor}</p>
                  <p><strong>Condition:</strong> {selectedTrial.condition}</p>
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
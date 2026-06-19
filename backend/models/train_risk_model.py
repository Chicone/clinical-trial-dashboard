import json
from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import confusion_matrix
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer

# Project root
BASE_DIR = Path(__file__).resolve().parents[1]

# Benchmark dataset used for training
BENCHMARK_DIR = (
    BASE_DIR
    / "data"
    / "benchmarks"
    / "v0_1"
)

def get_benchmark_path(benchmark_name: str) -> Path:
    return BENCHMARK_DIR / f"{benchmark_name}.json"


def train_risk_model(
    benchmark_name: str,
    model_name: str,
):
    """
    Train a baseline logistic regression model to predict
    operational risk.
    """

    # Load benchmark dataset
    benchmark_path = get_benchmark_path(
        benchmark_name
    )

    with benchmark_path.open("r", encoding="utf-8",) as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    def list_to_text(value):
        if isinstance(value, list):
            return " ".join(str(item) for item in value)
        if value is None:
            return ""
        return str(value)

    df["conditions_text"] = df["conditions"].apply(list_to_text)
    df["interventions_text"] = df["interventions"].apply(list_to_text)

    # Initial hand-crafted feature set
    features = [
        "phase",
        "study_type",
        "sponsor",
        "enrollment",
        "conditions_text",
        "interventions_text",
    ]

    X = df[features]
    y = df["target"]

    categorical_features = [
        "phase",
        "study_type",
        "sponsor",
    ]

    numeric_features = [
        "enrollment",
    ]

    text_features = [
        "conditions_text",
        "interventions_text",
    ]

    # Preprocessing pipeline:
    # - fill missing values
    # - one-hot encode categorical variables
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                numeric_features,
            ),
            (
                "conditions_text",
                TfidfVectorizer(
                    max_features=1000,
                    stop_words="english",
                    min_df=2,
                ),
                "conditions_text",
            ),
            (
                "interventions_text",
                TfidfVectorizer(
                    max_features=1000,
                    stop_words="english",
                    min_df=2,
                ),
                "interventions_text",
            ),
        ]
    )
    # Baseline model:
    # use class balancing because the dataset is imbalanced
    # Select classifier
    if model_name == "logistic_regression":
        classifier = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )

    elif model_name == "random_forest":
        classifier = RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

    elif model_name == "gradient_boosting":
        classifier = GradientBoostingClassifier(
            n_estimators=300,
            learning_rate=0.05,
            random_state=42,
        )

    else:
        raise ValueError(f"Unsupported model: {model_name}")

    # Build full pipeline
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    # Preserve class distribution in train/test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )

    # Train model
    model.fit(X_train, y_train)

    # Evaluate on held-out data
    y_pred = model.predict(X_test)

    y_proba = model.predict_proba(X_test)[:, 1]

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    return {
        "model": "logistic_regression",
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "mcc": matthews_corrcoef(y_test, y_pred),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "pr_auc": average_precision_score(y_test, y_proba),
        "roc_auc": roc_auc_score(y_test, y_proba),
    }
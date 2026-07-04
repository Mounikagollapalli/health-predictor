"""
train_model.py
---------------
Generates a small synthetic health dataset and trains a scikit-learn
classifier to predict a health risk category from three blood markers:

    - Glucose      (mg/dL)
    - Haemoglobin  (g/dL)
    - Cholesterol  (mg/dL)

The labels are generated using well-known clinical reference ranges
(combined with a little random noise so the model has to learn boundaries
rather than memorize a lookup table). This is NOT a medical device and the
ranges used here are simplified for demonstration purposes only.

Run this script once to produce model/risk_model.joblib, which the FastAPI
app loads at startup. If the file is missing, app/ml_model.py will
automatically call this script to regenerate it.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

RANDOM_SEED = 42
N_SAMPLES = 4000

# Reference ranges used to construct synthetic ground-truth labels.
# (Simplified general adult ranges for demo purposes.)
GLUCOSE_NORMAL = (70, 99)        # mg/dL, fasting
GLUCOSE_PREDIABETIC = (100, 125)
HAEMOGLOBIN_NORMAL = (12.0, 17.5)  # g/dL, general adult range
CHOLESTEROL_NORMAL = (0, 200)     # mg/dL total cholesterol
CHOLESTEROL_BORDERLINE = (200, 239)


def label_row(glucose: float, haemoglobin: float, cholesterol: float) -> str:
    """Assigns a risk category based on how many markers are out of range
    and how far out of range they are. Returns one of:
    'Low', 'Moderate', 'High'.
    """
    score = 0

    # Glucose scoring
    if glucose > GLUCOSE_PREDIABETIC[1]:
        score += 2
    elif glucose > GLUCOSE_NORMAL[1]:
        score += 1
    elif glucose < GLUCOSE_NORMAL[0]:
        score += 1  # hypoglycemia also a concern

    # Haemoglobin scoring (too low = anemia risk, too high also flagged)
    if haemoglobin < HAEMOGLOBIN_NORMAL[0] - 2:
        score += 2
    elif haemoglobin < HAEMOGLOBIN_NORMAL[0]:
        score += 1
    elif haemoglobin > HAEMOGLOBIN_NORMAL[1]:
        score += 1

    # Cholesterol scoring
    if cholesterol >= CHOLESTEROL_BORDERLINE[1]:
        score += 2
    elif cholesterol >= CHOLESTEROL_BORDERLINE[0]:
        score += 1

    if score >= 4:
        return "High"
    elif score >= 2:
        return "Moderate"
    else:
        return "Low"


def generate_dataset(n_samples: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Sample from realistic-ish distributions covering normal -> abnormal ranges
    glucose = rng.normal(loc=105, scale=35, size=n_samples).clip(50, 350)
    haemoglobin = rng.normal(loc=14, scale=2.5, size=n_samples).clip(5, 20)
    cholesterol = rng.normal(loc=190, scale=50, size=n_samples).clip(100, 400)

    df = pd.DataFrame({
        "glucose": glucose,
        "haemoglobin": haemoglobin,
        "cholesterol": cholesterol,
    })

    df["risk"] = df.apply(
        lambda row: label_row(row["glucose"], row["haemoglobin"], row["cholesterol"]),
        axis=1,
    )

    return df


def train_and_save(model_path: str) -> dict:
    df = generate_dataset()

    X = df[["glucose", "haemoglobin", "cholesterol"]]
    y = df["risk"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        random_state=RANDOM_SEED,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(clf, model_path)

    print(f"Model trained. Test accuracy: {acc:.3f}")
    print(classification_report(y_test, y_pred))

    return {"accuracy": acc, "report": report}


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    model_file = os.path.join(here, "risk_model.joblib")
    train_and_save(model_file)

"""
ml_model.py
------------
Loads the trained scikit-learn model (model/risk_model.joblib) and exposes
a simple predict_risk() function used by the API layer. If the model file
doesn't exist yet (e.g. first run), it triggers training automatically.
"""

import os
import sys
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.joblib")

_model = None


def _ensure_model_exists():
    if not os.path.exists(MODEL_PATH):
        sys.path.insert(0, MODEL_DIR)
        from train_model import train_and_save  # noqa: E402
        train_and_save(MODEL_PATH)


def get_model():
    global _model
    if _model is None:
        _ensure_model_exists()
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_risk(glucose: float, haemoglobin: float, cholesterol: float) -> dict:
    """Returns the predicted risk category, confidence, and full
    probability breakdown for the given health markers."""
    model = get_model()

    X = pd.DataFrame(
        [[glucose, haemoglobin, cholesterol]],
        columns=["glucose", "haemoglobin", "cholesterol"],
    )

    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    classes = model.classes_

    prob_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
    confidence = prob_dict[prediction]

    return {
        "risk_level": prediction,
        "risk_confidence": round(confidence, 4),
        "probabilities": {k: round(v, 4) for k, v in prob_dict.items()},
    }

# Health Risk Tracker

A full-stack web app that predicts a person's health risk level (Low / Moderate / High)
from three blood markers — **Glucose**, **Haemoglobin**, and **Cholesterol** — using a
trained machine learning model, with full CRUD and historical tracking.

> ⚠️ **Not a medical device.** The reference ranges and ML model in this project are
> simplified for demonstration purposes. Do not use this to make real health decisions.

## Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLite (via SQLAlchemy ORM)
- **ML model:** scikit-learn `RandomForestClassifier`, trained on a synthetic dataset
  built from general clinical reference ranges (see `model/train_model.py`)
- **Frontend:** Plain HTML / CSS / JavaScript (no framework, no build step)

## Features

- Add a person (Name, Date of Birth, Email) along with their first blood-marker reading
- Get an instant ML-predicted risk level + confidence + full probability breakdown
- Add additional readings over time per person (full history, not overwritten)
- View, edit, and delete people and individual readings (full CRUD)
- Auto-generated interactive API docs at `/docs` (Swagger UI)

## Project structure

```
health-predictor/
├── app/
│   ├── main.py          # FastAPI app + all routes
│   ├── database.py       # SQLAlchemy engine/session setup
│   ├── models.py          # ORM models: Patient, HealthRecord
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py            # Database CRUD operations
│   └── ml_model.py        # Loads the trained model, runs predictions
├── model/
│   ├── train_model.py     # Generates synthetic data + trains the model
│   └── risk_model.joblib  # The trained model (already included)
├── static/
│   ├── style.css
│   └── script.js
├── templates/
│   └── index.html
├── requirements.txt
└── health.db               # Created automatically on first run
```

## Setup & run

1. **Install Python 3.10+** if you don't already have it.

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # on Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open your browser to:**
   ```
   http://127.0.0.1:8000
   ```

   API docs (Swagger UI): `http://127.0.0.1:8000/docs`

The SQLite database (`health.db`) and the trained model (`model/risk_model.joblib`)
are created automatically if missing — there's no manual setup step beyond
`pip install`.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/patients` | Create a person + their first reading |
| `GET` | `/api/patients` | List all people (with their reading history) |
| `GET` | `/api/patients/{id}` | Get one person + their reading history |
| `PUT` | `/api/patients/{id}` | Update a person's Name / DOB / Email |
| `DELETE` | `/api/patients/{id}` | Delete a person and all their readings |
| `POST` | `/api/patients/{id}/records` | Add a new reading for an existing person |
| `GET` | `/api/patients/{id}/records` | Get a person's full reading history |
| `DELETE` | `/api/records/{id}` | Delete a single reading |
| `POST` | `/api/predict` | Predict risk for given markers, no DB write |
| `GET` | `/api/health` | Health check |

## Retraining the ML model

The model is trained on synthetic data generated from clinical reference-range rules
(see `label_row()` in `model/train_model.py`). To regenerate it — e.g. after changing
the reference ranges or the synthetic data generation — delete
`model/risk_model.joblib` and either restart the app (it auto-trains on startup if the
file is missing) or run:

```bash
python model/train_model.py
```

## Notes on the risk model

The model classifies risk based on three markers using ranges commonly cited for
general adults:

- **Glucose (fasting):** Normal 70–99 mg/dL, Prediabetic 100–125 mg/dL, High >125 mg/dL
- **Haemoglobin:** Normal ~12.0–17.5 g/dL (general adult range)
- **Cholesterol (total):** Normal <200 mg/dL, Borderline 200–239 mg/dL, High ≥240 mg/dL

These are simplified, general-purpose ranges (not adjusted for age, sex, pregnancy,
or existing conditions) used only to generate training labels for the demo model.

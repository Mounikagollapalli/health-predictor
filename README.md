# 🩺 Health Predictor

A machine learning-based Health Predictor API developed using **FastAPI** and **Scikit-learn**. The application analyzes health-related parameters to estimate an individual's risk of lifestyle diseases through a fast and user-friendly REST API.

## 🚀 Features

- Predicts the likelihood of lifestyle-related diseases using a trained machine learning model
- RESTful API built with FastAPI
- Interactive API documentation with Swagger UI and ReDoc
- Request validation using Pydantic
- Lightweight, high-performance backend
- Modular architecture for easy maintenance and future enhancements

## 🛠️ Technology Stack

- Python 3
- FastAPI
- Scikit-learn
- Pandas
- NumPy
- Pydantic
- Uvicorn

## 📁 Project Structure

```text
health-predictor/
│── app/
│   ├── main.py
│   ├── model/
│   ├── routes/
│   ├── schemas/
│   └── utils/
│
│── requirements.txt
│── README.md
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Mounikagollapalli/health-predictor.git
```

### 2. Navigate to the project directory

```bash
cd health-predictor
```

### 3. Install the required dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the FastAPI development server

```bash
uvicorn app.main:app --reload
```

The application will be available at:

```
http://127.0.0.1:8000
```

## 📖 API Documentation

Once the server is running, you can explore the API using the built-in documentation.

### Swagger UI

```
http://127.0.0.1:8000/docs
```

### ReDoc

```
http://127.0.0.1:8000/redoc
```

## 🔍 Sample Prediction Request

```json
{
  "age": 35,
  "gender": "Male",
  "bmi": 24.5,
  "blood_pressure": 120,
  "glucose": 95
}
```

## 📌 Future Enhancements

- User authentication and authorization
- Database integration
- Automated model retraining pipeline
- Docker containerization
- Cloud deployment
- CI/CD implementation
- Enhanced model monitoring and logging

## 👩‍💻 Author

**Mounika Gollapalli**

GitHub: https://github.com/Mounikagollapalli

---

If you found this project helpful, consider giving it a ⭐ on GitHub.

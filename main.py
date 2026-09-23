from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "Mental_Health_Model.pkl"
STATIC_DIR = BASE_DIR / "static"
INDEX_PATH = STATIC_DIR / "index.html"

MODEL_FEATURE_COLUMNS = [
    "Age",
    "Gender",
    "Grouped_country",
    "Academic_Level",
    "Most_Used_Platform",
    "Purpose_Of_Use",
    "Avg_Daily_Usage_Hours",
    "Daily_Unlocks",
    "Study_Hours",
    "Physical_Activity_Hours",
    "Sleep_Hours_Per_Night",
    "Stress_Level",
]

TOP_COUNTRIES = {
    "Other",
    "India",
    "USA",
    "Canada",
    "Australia",
    "UK",
    "Germany",
    "Mexico",
    "Turkey",
    "France",
}


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    loaded_model = joblib.load(MODEL_PATH)
    expected_columns = set(getattr(loaded_model, "feature_names_in_", MODEL_FEATURE_COLUMNS))
    configured_columns = set(MODEL_FEATURE_COLUMNS)

    if expected_columns != configured_columns:
        missing = sorted(expected_columns - configured_columns)
        extra = sorted(configured_columns - expected_columns)
        raise RuntimeError(
            "Configured input columns do not match the trained model. "
            f"Missing: {missing}. Extra: {extra}."
        )

    return loaded_model


model = load_model()

app = FastAPI(
    title="Mental Health Prediction API",
    description="API for predicting mental health scores",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(INDEX_PATH)


class InputData(BaseModel):
    age: int = Field(..., gt=0, lt=100, description="Age must be a positive integer")
    gender: Literal["Male", "Female"]
    country: str
    academic_level: Literal["High School", "Undergraduate", "Graduate"]
    most_used_platform: Literal[
        "Facebook",
        "LinkedIn",
        "Instagram",
        "Snapchat",
        "Twitter",
        "YouTube",
        "TikTok",
        "LINE",
        "KakaoTalk",
        "VKontakte",
        "WhatsApp",
        "WeChat",
    ]
    purpose_of_use: Literal["Networking", "Education", "Entertainment", "News"]
    average_daily_usage_hours: float = Field(
        ...,
        gt=0,
        lt=24,
        description="Average daily usage hours must be a positive number less than 24",
    )
    daily_unlocks: int = Field(..., gt=0, description="Daily unlocks must be a positive integer")
    study_hours: float = Field(
        ...,
        gt=0,
        lt=24,
        description="Study hours must be a positive number less than 24",
    )
    physical_activity_hours: float = Field(
        ...,
        gt=0,
        lt=24,
        description="Physical activity hours must be a positive number less than 24",
    )
    sleep_hours_per_night: float = Field(
        ...,
        gt=0,
        lt=24,
        description="Sleep hours per night must be a positive number less than 24",
    )
    stress_level: Literal["Medium", "Low", "Very High", "High"]


class PredictionResponse(BaseModel):
    prediction: float = Field(..., description="Predicted mental health score")


def build_input_frame(data: InputData) -> pd.DataFrame:
    country_group = data.country if data.country in TOP_COUNTRIES else "Other"

    row = {
        "Age": data.age,
        "Gender": data.gender,
        "Grouped_country": country_group,
        "Academic_Level": data.academic_level,
        "Most_Used_Platform": data.most_used_platform,
        "Purpose_Of_Use": data.purpose_of_use,
        "Avg_Daily_Usage_Hours": data.average_daily_usage_hours,
        "Daily_Unlocks": data.daily_unlocks,
        "Study_Hours": data.study_hours,
        "Physical_Activity_Hours": data.physical_activity_hours,
        "Sleep_Hours_Per_Night": data.sleep_hours_per_night,
        "Stress_Level": data.stress_level,
    }

    return pd.DataFrame([row], columns=MODEL_FEATURE_COLUMNS)


@app.post("/predict", response_model=PredictionResponse)
def predict(data: InputData):
    try:
        input_row = build_input_frame(data)
        prediction = model.predict(input_row)[0]
        return PredictionResponse(prediction=round(float(prediction), 2))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

# To run the FastAPI application, use the following command in your terminal:
#  Set-Location "C:\All Coding Here\Codess\python\Machine Learning\Mental Health Score ML Project"; py -3.11 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Best permanent fix: create a Python 3.11 virtual environment and always activate it before working:
# py -3.11 -m venv .venv
# .\.venv\Scripts\Activate.ps1
# python -m pip install fastapi uvicorn pandas joblib scikit-learn==1.9.0
# python -m uvicorn main:app --reload

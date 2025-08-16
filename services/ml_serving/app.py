import os
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import pandas as pd
import logging

app = FastAPI(title="ML Serving Service")

# بارگذاری مدل از مسیر محیطی
MODEL_PATH = os.getenv("MODEL_PATH", "models/iforest_model.pkl")
_model = None


def load_model() -> Any:
    """سعی می‌کند مدل را از فایل بارگذاری کند؛ اگر موجود نباشد یک مدل ساده ایجاد می‌کند."""
    global _model
    if _model is not None:
        return _model
    if os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
    else:
        # اگر مدل پیدا نشد، یک IsolationForest ساده آموزش می‌دهیم
        from sklearn.ensemble import IsolationForest
        import numpy as np
        X = np.random.randn(100, 3)
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X)
        _model = model
    return _model


class FeatureInput(BaseModel):
    engineered_features: Dict[str, float]


@app.on_event("startup")
async def startup_event():
    # بارگذاری مدل در شروع
    load_model()


@app.post("/predict")
async def predict(input: FeatureInput) -> Dict[str, Any]:
    """
    این نقطه ورود برای پیش‌بینی است. مدل IsolationForest روی ویژگی‌ها اجرا شده و نمره و برچسب ناهنجاری بازگردانده می‌شود.
    """
    try:
        features = input.engineered_features
        # ساخت DataFrame با ویژگی‌های عددی
        df = pd.DataFrame([features])
        model = load_model()
        preds = model.predict(df)
        scores = model.decision_function(df)
        result = {
            "anomaly": bool(preds[0] == -1),
            "score": float(scores[0])
        }
        return result
    except Exception as exc:
        logging.exception("خطا در پیش‌بینی: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
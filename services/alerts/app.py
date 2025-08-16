import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

app = FastAPI(title="Alerting Service")

ALERT_EMAIL = os.getenv("ALERT_EMAIL", "security@example.com")


class Prediction(BaseModel):
    anomaly: bool
    score: float
    context: Dict[str, Any] | None = None


@app.post("/alert")
async def handle_alert(pred: Prediction) -> Dict[str, str]:
    """
    این سرویس اگر ناهنجاری شناسایی شده باشد پیام هشداری را ارسال می‌کند. در این نمونه، فقط پیام در لاگ چاپ می‌شود.
    """
    try:
        if pred.anomaly:
            message = f"[ALERT] Anomaly detected with score {pred.score:.4f}! Context: {pred.context}"
            # در محیط واقعی می‌توانید ایمیل بفرستید یا با سیستم Ticketing مجتمع کنید
            logging.warning(message)
            return {"status": "alert_sent", "message": message}
        else:
            return {"status": "ok", "message": "No anomaly."}
    except Exception as exc:
        logging.exception("خطا در سرویس هشدار: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
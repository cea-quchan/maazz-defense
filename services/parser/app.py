from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json
import os
import logging

app = FastAPI(title="Parser Service")


class Event(BaseModel):
    """ساختار ساده برای دریافت رخدادهای خام."""
    timestamp: str
    message: str
    host: str | None = None
    source: str | None = None
    metadata: Dict[str, Any] | None = None


@app.post("/parse")
async def parse_event(event: Event) -> Dict[str, Any]:
    """
    نقطه ورود برای دریافت رخداد خام و استخراج برخی ویژگی‌ها.

    این پیاده‌سازی اولیه تنها طول پیام و تعداد کلمات را برمی‌گرداند.
    """
    try:
        message = event.message
        length = len(message)
        word_count = len(message.split())
        features = {
            "timestamp": event.timestamp,
            "host": event.host,
            "source": event.source,
            "length": length,
            "word_count": word_count,
        }
        return {"features": features}
    except Exception as exc:
        logging.exception("خطا در پردازش رخداد: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
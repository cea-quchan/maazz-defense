from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

app = FastAPI(title="Feature Engineering Service")


class ParsedEvent(BaseModel):
    features: Dict[str, Any]


@app.post("/features")
async def generate_features(parsed_event: ParsedEvent) -> Dict[str, Any]:
    """
    این سرویس روی دادهٔ استخراج‌شده از پارسر ویژگی‌های اضافی می‌سازد. در این MVP تنها نسبت طول پیام به تعداد کلمات محاسبه می‌شود.
    """
    try:
        f = parsed_event.features
        # اگر تعداد کلمات صفر بود نسبت را صفر قرار می‌دهیم تا خطای تقسیم بر صفر نداشته باشیم
        ratio = f.get("length", 0) / max(f.get("word_count", 1), 1)
        engineered = f.copy()
        engineered["length_to_word_ratio"] = ratio
        return {"engineered_features": engineered}
    except Exception as exc:
        logging.exception("خطا در ساخت ویژگی‌ها: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
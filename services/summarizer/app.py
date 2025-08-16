import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
# در صورت نیاز، می‌توانید کتابخانهٔ openai را import و استفاده کنید
import openai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LLM Summarizer Service")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


class SummarizeRequest(BaseModel):
    events: List[Dict[str, Any]]


@app.post("/summarize")
async def summarize(req: SummarizeRequest) -> Dict[str, Any]:
    """
    این سرویس مجموعه‌ای از رخدادها را می‌گیرد و خلاصه‌ای تولید می‌کند.
    اگر کلید OpenAI تعریف شده باشد، از مدل زبانی برای خلاصه‌سازی استفاده می‌شود؛ در غیر این صورت تنها تعداد رخدادها را اعلام می‌کند.
    """
    try:
        events = req.events
        if not events:
            return {"summary": "No events provided."}
        if OPENAI_API_KEY:
            # متن اولیهٔ خلاصه‌سازی
            content = "\n".join([str(e) for e in events])
            # فراخوانی مدل چت برای خلاصه‌سازی
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4.0-turbo",  # می‌توانید مدل به‌روزتری انتخاب کنید
                    messages=[
                        {"role": "system", "content": "You are a log summarization assistant."},
                        {"role": "user", "content": f"Summarize these events:\n{content}"},
                    ],
                    max_tokens=150,
                    temperature=0.3,
                )
                summary_text = response.choices[0].message.content.strip()
            except Exception as e:
                logging.exception("خطا در فراخوانی OpenAI: %s", e)
                summary_text = f"Received {len(events)} events."  # بازگشت به خلاصهٔ ساده در صورت خطا
        else:
            summary_text = f"Received {len(events)} events."
        return {"summary": summary_text}
    except Exception as exc:
        logging.exception("خطا در سرویس خلاصه‌سازی: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

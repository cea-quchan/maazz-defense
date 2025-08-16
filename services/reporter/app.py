import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import requests
from email.message import EmailMessage
import smtplib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Reporter Service")

# Environment configuration
REPORTER_OUTPUT_DIR = os.getenv("REPORTER_OUTPUT_DIR", "./storage/reports")
LLM_URL = os.getenv("LLM_URL")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL")
TO_EMAIL = os.getenv("TO_EMAIL")

Path(REPORTER_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


class ReportRequest(BaseModel):
    events: List[Dict[str, Any]]
    channels: List[str] = []
    include_charts: bool = False
    include_audio: bool = False


@app.get("/health")
async def health() -> Dict[str, bool]:
    return {"ok": True}


def summarize_events(events: List[Dict[str, Any]]) -> str:
    if LLM_URL:
        try:
            resp = requests.post(LLM_URL, json={"events": events}, timeout=10)
            if resp.ok:
                data = resp.json()
                return data.get("summary", f"Received {len(events)} events.")
        except Exception as e:  # pragma: no cover - external service
            logging.exception("LLM request failed: %s", e)
    return f"Received {len(events)} events."


def generate_chart(events: List[Dict[str, Any]]) -> str:
    chart_path = Path(REPORTER_OUTPUT_DIR) / "usage.png"
    cpu = [e.get("cpu", 0) for e in events]
    mem = [e.get("mem", 0) for e in events]
    plt.figure()
    plt.plot(cpu, label="CPU")
    plt.plot(mem, label="MEM")
    plt.legend()
    plt.savefig(chart_path)
    plt.close()
    return str(chart_path)


def send_telegram(text: str) -> Dict[str, Any]:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"channel": "telegram", "skipped": True}
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        return {"channel": "telegram", "skipped": False}
    except Exception as e:  # pragma: no cover - external service
        logging.exception("Telegram send failed: %s", e)
        return {"channel": "telegram", "error": str(e)}


def send_slack(text: str) -> Dict[str, Any]:
    if not SLACK_WEBHOOK_URL:
        return {"channel": "slack", "skipped": True}
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        return {"channel": "slack", "skipped": False}
    except Exception as e:  # pragma: no cover - external service
        logging.exception("Slack send failed: %s", e)
        return {"channel": "slack", "error": str(e)}


def send_email(text: str, attachments: Optional[List[str]] = None) -> Dict[str, Any]:
    if not (SMTP_HOST and FROM_EMAIL and TO_EMAIL):
        return {"channel": "email", "skipped": True}
    try:
        msg = EmailMessage()
        msg["Subject"] = "Reporter Output"
        msg["From"] = FROM_EMAIL
        msg["To"] = TO_EMAIL
        msg.set_content(text)
        for path in attachments or []:
            with open(path, "rb") as f:
                data = f.read()
            msg.add_attachment(data, maintype="image", subtype="png", filename=os.path.basename(path))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USER and SMTP_PASS:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return {"channel": "email", "skipped": False}
    except Exception as e:  # pragma: no cover - external service
        logging.exception("Email send failed: %s", e)
        return {"channel": "email", "error": str(e)}


@app.post("/report")
async def report(req: ReportRequest) -> Dict[str, Any]:
    try:
        summary = summarize_events(req.events)
        chart_path = generate_chart(req.events) if req.include_charts else None
        audio_path = None
        if req.include_audio:
            audio_path = str(Path(REPORTER_OUTPUT_DIR) / "summary.txt")
            with open(audio_path, "w", encoding="utf-8") as f:
                f.write(summary)
        results = []
        for ch in req.channels:
            if ch == "telegram":
                results.append(send_telegram(summary))
            elif ch == "slack":
                results.append(send_slack(summary))
            elif ch == "email":
                attachments = [p for p in [chart_path, audio_path] if p]
                results.append(send_email(summary, attachments))
            else:
                results.append({"channel": ch, "skipped": True})
        return {"summary": summary, "chart": chart_path, "audio": audio_path, "results": results}
    except Exception as exc:
        logging.exception("report error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

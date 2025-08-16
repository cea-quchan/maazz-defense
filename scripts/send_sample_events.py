#!/usr/bin/env python
"""
اسکریپتی ساده برای ارسال چند رخداد نمونه به سرویس‌ها و نمایش نتیجهٔ خروجی.

این اسکریپت برای توسعه‌دهندگان نوشته شده تا بتوانند زنجیرهٔ پردازش (Parser → Features → ML Serving → Alerts) را در حالت محلی تست کنند.
قبل از اجرای آن حتماً سرویس‌ها را با `docker compose up` اجرا کرده باشید.
"""

import time
import requests
import random
from datetime import datetime


def generate_log() -> dict:
    messages = [
        "User admin logged in from 192.168.1.10",
        "Failed login attempt for root",
        "Malware detected in process 1234",
        "Database connection timed out",
        "New SSH key added for user deploy",
    ]
    message = random.choice(messages)
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": message,
        "host": "test-host",
        "source": "sample-script",
    }


def main():
    for i in range(5):
        event = generate_log()
        print(f"\nSending event {i+1}: {event['message']}")
        # Step 1: parse
        resp = requests.post("http://localhost:8001/parse", json=event)
        parsed = resp.json().get("features")
        # Step 2: feature engineering
        resp2 = requests.post("http://localhost:8002/features", json={"features": parsed})
        engineered = resp2.json().get("engineered_features")
        # Step 3: ML prediction
        resp3 = requests.post(
            "http://localhost:8003/predict", json={"engineered_features": engineered}
        )
        prediction = resp3.json()
        print(f"Prediction: {prediction}")
        # Step 4: alert if needed
        resp4 = requests.post(
            "http://localhost:8004/alert",
            json={"anomaly": prediction["anomaly"], "score": prediction["score"], "context": event},
        )
        print(f"Alert service response: {resp4.json()}")
        time.sleep(1)


if __name__ == "__main__":
    main()
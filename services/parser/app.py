import asyncio
import contextlib
import json
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aiokafka import AIOKafkaConsumer

app = FastAPI(title="Parser Service")


class Event(BaseModel):
    """ساختار ساده برای دریافت رخدادهای خام."""
    timestamp: str
    message: str
    host: str | None = None
    source: str | None = None
    metadata: Dict[str, Any] | None = None


def extract_features(event: Event) -> Dict[str, Any]:
    """منطق اصلی استخراج ویژگی از رخداد."""
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


@app.post("/parse")
async def parse_event(event: Event) -> Dict[str, Any]:
    """
    نقطه ورود برای دریافت رخداد خام و استخراج برخی ویژگی‌ها.

    این پیاده‌سازی اولیه تنها طول پیام و تعداد کلمات را برمی‌گرداند.
    """
    try:
        return extract_features(event)
    except Exception as exc:
        logging.exception("خطا در پردازش رخداد: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_PARSER_TOPIC", "logs.raw")
ENABLE_KAFKA_CONSUMER = os.getenv("ENABLE_KAFKA_CONSUMER", "false").lower() == "true"


async def consume_loop() -> None:
    """مصرف آسنکرون رخدادها از Kafka و استخراج ویژگی."""
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()
    try:
        async for msg in consumer:
            try:
                event = Event(**msg.value)
                features = extract_features(event)
                logging.info("Consumed event: %s", features)
            except Exception as exc:  # pragma: no cover - فقط لاگ
                logging.exception("خطا در پردازش پیام Kafka: %s", exc)
    finally:
        await consumer.stop()


@app.on_event("startup")
async def startup_event() -> None:
    if ENABLE_KAFKA_CONSUMER:
        app.state.consumer_task = asyncio.create_task(consume_loop())
    else:
        app.state.consumer_task = None


@app.on_event("shutdown")
async def shutdown_event() -> None:
    task = getattr(app.state, "consumer_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(Exception):
            await task


import asyncio
import json
import logging
import os
from collections import deque
from datetime import datetime, timezone
from typing import Set

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from ingestion import run_ingestion_cycle

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))   # seconds between ingestion cycles
EVENT_HISTORY = 200                                       # keep last N events in memory

app = FastAPI(title="CityPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------- In-memory state -------
event_buffer: deque = deque(maxlen=EVENT_HISTORY)
connected_clients: Set[WebSocket] = set()
pipeline_task: asyncio.Task | None = None


# ------- WebSocket broadcast -------

async def broadcast(event: dict):
    dead = set()
    for ws in connected_clients:
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    connected_clients.difference_update(dead)


# ------- Background pipeline loop -------

async def pipeline_loop():
    """Continuously ingests data and broadcasts to all connected clients."""
    while True:
        try:
            logger.info("Starting ingestion cycle...")
            events = await run_ingestion_cycle()
            for event in events:
                event_buffer.append(event)
                await broadcast({"type": "event", "data": event})
            # Broadcast a "cycle_complete" signal with city-level summary
            summary = compute_city_summary(list(event_buffer))
            await broadcast({"type": "summary", "data": summary})
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
        await asyncio.sleep(POLL_INTERVAL)


def compute_city_summary(events: list[dict]) -> list[dict]:
    """Aggregate average sentiment per city for the heatmap."""
    city_scores: dict[str, list[float]] = {}
    city_meta: dict[str, dict] = {}
    for ev in events:
        city = ev["city"]
        if city not in city_scores:
            city_scores[city] = []
            # FIX: Changed "lng" to "lon" to match incoming ingestion data keys
            city_meta[city] = {"lat": ev["lat"], "lon": ev["lon"]}
        
        # FIX: Ensure we read the correct key name from the sentiment model
        score = ev.get("sentiment_score") or ev.get("sentiment") or 0.0
        city_scores[city].append(score)

    summary = []
    for city, scores in city_scores.items():
        if not scores:
            continue
        avg = round(sum(scores) / len(scores), 4)
        intensity = round((avg + 1) / 2, 4)
        summary.append({
            "city": city,
            "lat": city_meta[city]["lat"],
            "lon": city_meta[city]["lon"], # FIX: Changed "lng" to "lon"
            "avg_sentiment": avg,
            "intensity": intensity,
            "event_count": len(scores),
        })
    return summary


# ------- Startup / Shutdown -------

@app.on_event("startup")
async def startup():
    global pipeline_task
    pipeline_task = asyncio.create_task(pipeline_loop())
    logger.info("CityPulse pipeline started")


@app.on_event("shutdown")
async def shutdown():
    if pipeline_task:
        pipeline_task.cancel()


# ------- HTTP Routes -------

@app.get("/health")
def health():
    return {"status": "ok", "clients": len(connected_clients), "events_buffered": len(event_buffer)}


@app.get("/events")
def get_events(limit: int = 50):
    """REST fallback: return latest N events."""
    events = list(event_buffer)[-limit:]
    return {"events": events, "total": len(event_buffer)}


@app.get("/summary")
def get_summary():
    """Return current city-level sentiment summary."""
    return {"summary": compute_city_summary(list(event_buffer))}


# ------- WebSocket Endpoint -------

import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# A list of global cities to cycle through for mock streaming
MOCK_CITIES = [
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "texts": ["Heavy traffic near Bandra, but the weather is fantastic!", "Incredible food experience in South Mumbai tonight!"]},
    {"city": "Delhi", "lat": 28.7041, "lon": 77.1025, "texts": ["Excited for the new tech hub launching in Connaught Place.", "Metro commutes are busy but incredibly efficient today."]},
    {"city": "London", "lat": 51.5074, "lon": -0.1278, "texts": ["Beautiful sunny afternoon walking around Hyde Park!", "The museum exhibition was completely overcrowded today."]},
    {"city": "Houston", "lat": 29.7604, "lon": -95.3698, "texts": ["Clear skies and a wonderful evening out in downtown.", "Local space center exhibit was absolutely inspiring!"]}
]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 Frontend map successfully connected to WebSocket pipeline!")
    
    try:
        while True:
            # Pick a random city profile
            profile = random.choice(MOCK_CITIES)
            mock_payload = {
                "type": "event",
                "data": {
                    "city": profile["city"],
                    "lat": profile["lat"],
                    "lon": profile["lon"],
                    "source": "Simulation Stream",
                    "text": random.choice(profile["texts"]),
                    "sentiment_score": random.uniform(-1, 1) # Randomize positive, negative, neutral
                }
            }
            
            # Broadcast the data packet down the open pipe
            await websocket.send_json(mock_payload)
            
            # Wait 3 seconds before streaming the next city pulse
            await asyncio.sleep(3)
            
    except WebSocketDisconnect:
        print("🔴 Frontend map disconnected from pipeline.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
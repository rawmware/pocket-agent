"""HTTP server: serves the chat UI and the /api/chat endpoint (SSE)."""
from __future__ import annotations

import asyncio
import json
import os
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from agent.config import load_settings
from agent.loop import Agent, BudgetExceeded

settings = load_settings()
app = FastAPI(title="pocket-agent")
sessions: dict[str, list] = {}
HERE = os.path.dirname(os.path.abspath(__file__))


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(HERE, "web", "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
def health():
    return {"ok": True,
            "default_model": settings["default_model"],
            "smart_model": settings["smart_model"]}


@app.get("/api/models")
def models():
    return {"default": settings["default_model"],
            "smart": settings["smart_model"],
            "daily_budget_usd": settings["daily_budget"]}


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    text = (body.get("message") or "").strip()
    if not text:
        return {"error": "empty message"}
    session_id = body.get("session_id") or str(uuid.uuid4())
    history = sessions.get(session_id, [])
    model = body.get("model") or None

    def work():
        events: list = []
        try:
            agent = Agent(settings, model=model)
            reply, new_history, usage, cost = agent.run(
                text, history, on_event=lambda e: events.append(e))
            sessions[session_id] = new_history
            return {"session_id": session_id, "events": events, "reply": reply,
                    "usage": usage, "cost_usd": round(cost, 4),
                    "spent_today": round(agent.spent_today(), 4)}
        except BudgetExceeded as e:
            return {"session_id": session_id, "events": events, "error": str(e)}
        except Exception as e:
            return {"session_id": session_id, "events": events, "error": str(e)}

    payload = await asyncio.to_thread(work)

    def gen():
        for e in payload.pop("events", []):
            yield "data: " + json.dumps({"type": "tool", "name": e.get("name")}) + "\n\n"
        yield "data: " + json.dumps({"type": "done", **payload}) + "\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"),
                port=int(os.getenv("PORT", "8000")))

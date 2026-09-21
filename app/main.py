from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.adapters import (
    BrightDataAdapter,
    CogneeCloudMemoryAdapter,
    CogneeMemoryAdapter,
    DemoMemoryAdapter,
    InnerOSMemoryAdapter,
)
from app.brain import PersonalBrain
from app.models import BrainRequest, BrainResponse
from app.status import sponsor_status


app = FastAPI(title="InnerOS Personal Brain", version="0.3.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def build_brain() -> PersonalBrain:
    # The hackathon brain is intentionally able to run without Ralphi MCP.
    # Cognee Cloud is the preferred persistent memory when its runtime secret exists.
    if os.getenv("COGNEE_API_KEY") and os.getenv("COGNEE_SERVICE_URL"):
        memory = CogneeCloudMemoryAdapter()
    elif os.getenv("USE_COGNEE", "0") == "1":
        memory = CogneeMemoryAdapter()
    elif os.getenv("INNEROS_MEMORY_ENDPOINT"):
        memory = InnerOSMemoryAdapter()
    else:
        memory = DemoMemoryAdapter(
            seed=[
                "InnerOS is a local-first AI operating system that coordinates memory, tools and agents.",
                "Ralphi IA already receives opportunity signals and stores operational memory in MongoDB and Qdrant.",
                "Bright Data is configured for live public web research.",
                "Current hackathon goal: build a Personal Brain that remembers, discovers, reasons, acts, verifies and learns.",
            ]
        )
    return PersonalBrain(memory=memory, web=BrightDataAdapter())


brain = build_brain()


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "inneros-personal-brain", "version": "0.3.0"}


@app.get("/api/status")
async def status() -> dict:
    return sponsor_status()


@app.post("/api/brain", response_model=BrainResponse)
async def ask_brain(request: BrainRequest) -> BrainResponse:
    return await brain.answer(request.prompt, act=request.act)


@app.get("/api/brain/stream")
async def stream_brain(
    prompt: str = Query(..., min_length=1, max_length=1800),
    act: bool = False,
) -> StreamingResponse:
    async def event_stream():
        queue: asyncio.Queue[dict] = asyncio.Queue()

        async def emit(event: dict) -> None:
            await queue.put({"type": "stage", **event})

        async def run() -> None:
            try:
                result = await brain.answer(prompt, act=act, emit=emit)
                await queue.put({
                    "type": "result",
                    "answer": result.answer,
                    "memory_hits": [x.model_dump() for x in result.memory_hits],
                    "web_hits": [x.model_dump() for x in result.web_hits],
                    "actions": result.actions,
                    "trace": result.trace,
                })
            except Exception as exc:
                await queue.put({
                    "type": "error",
                    "message": f"{type(exc).__name__}: {exc}",
                })
            finally:
                await queue.put({"type": "done"})

        task = asyncio.create_task(run())
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
                if event.get("type") == "done":
                    break
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")

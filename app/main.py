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
from app.demo_memory import seed_in_background, seed_status
from app.models import BrainRequest, BrainResponse
from app.proof_modes import ProofModeRunner
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


def build_proof_runner() -> ProofModeRunner:
    return ProofModeRunner(memory=brain.memory, web=BrightDataAdapter())


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "inneros-personal-brain", "version": "0.3.0"}


@app.on_event("startup")
async def startup_seed_memory() -> None:
    asyncio.create_task(seed_in_background())


@app.get("/api/status")
async def status() -> dict:
    data = sponsor_status()
    data["memory_seed"] = seed_status()
    return data


@app.get("/api/proof/modes")
async def proof_modes() -> dict:
    return {
        "modes": [
            {
                "key": "remember",
                "label": "REMEMBER",
                "description": "Prompt -> Strands memory injection -> Cognee recall -> answer + provenance",
            },
            {
                "key": "observe",
                "label": "OBSERVE",
                "description": "Prompt -> Bright Data live evidence -> reasoning provenance",
            },
            {
                "key": "govern",
                "label": "GOVERN",
                "description": "Action proposed -> deterministic policy check -> blocked for human approval",
            },
            {
                "key": "share",
                "label": "SHARE",
                "description": "Agent A writes a harmless fact -> Agent B recalls it from Cognee",
            },
        ]
    }


@app.post("/api/proof/{mode}")
async def run_proof_mode(mode: str) -> dict:
    return await build_proof_runner().run(mode)


@app.post("/api/brain", response_model=BrainResponse)
async def ask_brain(request: BrainRequest) -> BrainResponse:
    return await brain.answer(request.prompt, act=request.act, route_mode=request.route_mode)


@app.get("/api/brain/stream")
async def stream_brain(
    prompt: str = Query(..., min_length=1, max_length=1800),
    act: bool = False,
    route_mode: str = "auto",
) -> StreamingResponse:
    async def event_stream():
        queue: asyncio.Queue[dict] = asyncio.Queue()

        async def emit(event: dict) -> None:
            await queue.put({"type": "stage", **event})

        async def run() -> None:
            try:
                result = await brain.answer(prompt, act=act, route_mode=route_mode, emit=emit)
                await queue.put({
                    "type": "result",
                    "answer": result.answer,
                    "memory_hits": [x.model_dump() for x in result.memory_hits],
                    "web_hits": [x.model_dump() for x in result.web_hits],
                    "actions": result.actions,
                    "trace": result.trace,
                    "route": result.route,
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

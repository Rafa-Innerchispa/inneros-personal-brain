from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.adapters import (
    BrightDataAdapter,
    CogneeCloudMemoryAdapter,
    CogneeMcpMemoryAdapter,
    CogneeMemoryAdapter,
    DemoMemoryAdapter,
    InnerOSMemoryAdapter,
)
from app.brain import PersonalBrain
from app.demo_memory import seed_in_background, seed_status
from app.memory_curator import curate_for_cognee
from app.models import BrainRequest, BrainResponse
from app.proof_modes import ProofModeRunner
from app.status import sponsor_status


app = FastAPI(title="InnerOS Personal Brain", version="0.3.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
VOICEOPS_GATEWAY_URL = os.getenv("VOICEOPS_GATEWAY_URL", "http://127.0.0.1:8200").rstrip("/")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def build_brain() -> PersonalBrain:
    # The hackathon brain is intentionally able to run without Ralphi MCP.
    # The local official Cognee MCP is preferred when present because it is
    # the shared agent memory surface used by Codex/Cursor/Antigravity.
    if os.getenv("COGNEE_MCP_URL") or os.getenv("COGNEE_MCP_PORT"):
        memory = CogneeMcpMemoryAdapter()
    elif os.getenv("COGNEE_API_KEY") and os.getenv("COGNEE_SERVICE_URL"):
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


def _voiceops_public_health(health: dict, voices: dict | None = None) -> dict:
    tts = health.get("tts") or {}
    whisper = health.get("whisper") or {}
    vllm = health.get("vllm") or {}
    qdrant = health.get("qdrant") or {}
    mcp = health.get("mcp_profile") or health.get("mcp") or {}
    whisper_is_mapping = isinstance(whisper, dict)
    voice_items = []
    if voices:
        for item in voices.get("voices") or []:
            voice_items.append({
                "id": item.get("id") or item.get("voice") or item.get("name"),
                "label": item.get("label") or item.get("name") or item.get("id"),
                "provider": item.get("provider") or item.get("engine"),
            })
    return {
        "ok": bool(health.get("ok")),
        "gateway_reachable": True,
        "local_first": bool(health.get("local_first")),
        "auth_required": bool(health.get("auth_required")),
        "cloud_fallback": bool(health.get("cloud_fallback")),
        "public_urls": health.get("public_urls") or [],
        "whisper": {
            "configured": bool((whisper.get("url") or whisper.get("ok")) if whisper_is_mapping else whisper),
            "ok": whisper.get("ok") if whisper_is_mapping else None,
        },
        "tts": {
            "ready": bool(tts.get("ready")),
            "default_engine": tts.get("default_engine"),
            "voices": voice_items,
        },
        "vllm": {
            "ok": bool(vllm.get("ok")),
            "model": vllm.get("model"),
        },
        "qdrant": {
            "ok": bool(qdrant.get("ok")),
            "points_count": qdrant.get("points_count"),
            "collection": qdrant.get("collection"),
        },
        "mcp": {
            "profile": mcp.get("profile"),
            "visible_tool_count": mcp.get("visible_tool_count"),
            "full_catalog_access": mcp.get("full_catalog_access"),
        },
    }


@app.get("/api/voiceops/status")
async def voiceops_status() -> dict:
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            health_response = await client.get(f"{VOICEOPS_GATEWAY_URL}/api/voice/health")
            health_response.raise_for_status()
            voices = None
            try:
                voices_response = await client.get(f"{VOICEOPS_GATEWAY_URL}/api/voice/tts/voices")
                if voices_response.status_code == 200:
                    voices = voices_response.json()
            except httpx.HTTPError:
                voices = None
            return _voiceops_public_health(health_response.json(), voices)
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "gateway_reachable": False,
            "reason": type(exc).__name__,
            "message": "Local VoiceOps gateway is not reachable from the Personal Brain server.",
        }



def _is_loopback_host(host: str | None) -> bool:
    return str(host or "").strip().lower() in {"127.0.0.1", "::1", "localhost"}


def _voiceops_shared_memory_receipt(payload: dict) -> tuple[str, dict, dict]:
    if payload.get("verification_passed") is not True:
        raise ValueError("verification_passed_required")
    correlation_id = str(payload.get("correlation_id") or "").strip()
    summary = str(payload.get("summary") or "").strip()
    evidence_ref = str(payload.get("evidence_ref") or "").strip()
    source_truth = str(payload.get("source_truth") or "UNVERIFIED").strip().upper()
    if not correlation_id:
        raise ValueError("correlation_id_required")
    if not summary:
        raise ValueError("summary_required")
    if not evidence_ref:
        raise ValueError("evidence_ref_required")
    if source_truth not in {"LIVE", "REPLAY", "SYNTHETIC"}:
        raise ValueError("source_truth_invalid")

    curated = curate_for_cognee(
        "VoiceOps verified outcome. "
        f"Correlation: {correlation_id}. "
        f"Outcome: {summary}. "
        f"Evidence: {evidence_ref}. "
        f"Source truth: {source_truth}."
    )
    memory_id = hashlib.sha256(
        f"{correlation_id}|{evidence_ref}".encode("utf-8")
    ).hexdigest()[:20]
    metadata = {
        "source": "voiceops",
        "kind": "verified_operational_outcome",
        "correlation_id": correlation_id,
        "evidence_ref": evidence_ref,
        "source_truth": source_truth,
        "verification_passed": True,
        "memory_policy": curated.policy,
        "memory_id": memory_id,
    }
    receipt = {
        "ok": True,
        "stored": True,
        "memory_id": memory_id,
        "dataset": os.getenv("COGNEE_DATASET", "inneros-personal-brain"),
        "source_truth": source_truth,
        "verification_passed": True,
        "curated": True,
    }
    return curated.text, metadata, receipt


@app.post("/api/internal/shared-memory/verified-outcome")
async def voiceops_store_verified_outcome(request: Request, payload: dict) -> dict:
    host = request.client.host if request.client else ""
    if not _is_loopback_host(host):
        raise HTTPException(status_code=403, detail="loopback_only")
    try:
        text, metadata, receipt = _voiceops_shared_memory_receipt(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await brain.memory.remember(text, metadata)
    return receipt


@app.get("/api/internal/shared-memory/recall")
async def voiceops_recall_shared_memory(
    request: Request,
    q: str = Query(..., min_length=1, max_length=600),
    limit: int = Query(5, ge=1, le=8),
) -> dict:
    host = request.client.host if request.client else ""
    if not _is_loopback_host(host):
        raise HTTPException(status_code=403, detail="loopback_only")
    hits = await brain.memory.search(q, limit=limit)
    return {
        "ok": True,
        "dataset": os.getenv("COGNEE_DATASET", "inneros-personal-brain"),
        "count": len(hits),
        "hits": [
            {
                "summary": hit.summary[:600],
                "source": hit.source,
                "metadata": {
                    key: value
                    for key, value in hit.metadata.items()
                    if key in {"source", "kind", "correlation_id", "evidence_ref", "source_truth", "verification_passed", "memory_id"}
                },
            }
            for hit in hits
        ],
    }


@app.post("/api/voiceops/tts")
async def voiceops_tts(payload: dict):
    text = str(payload.get("text") or "").strip()
    voice = str(payload.get("voice") or "xtts:rafael").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text_required")
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            gateway_response = await client.post(
                f"{VOICEOPS_GATEWAY_URL}/api/voice/tts/speak",
                json={"text": text[:1800], "voice": voice},
            )
            if gateway_response.status_code in {401, 403} or "login_required" in gateway_response.text:
                return Response(
                    json.dumps({
                        "ok": False,
                        "reason": "login_required",
                        "message": "Local VoiceOps TTS is installed but requires an authenticated VoiceOps session.",
                    }),
                    status_code=401,
                    media_type="application/json",
                )
            gateway_response.raise_for_status()
            data = gateway_response.json()
            audio_url = data.get("audio_url") or data.get("url")
            if not audio_url:
                return {"ok": False, "reason": "audio_url_missing", "raw_status": data.get("status")}
            if audio_url.startswith("/"):
                audio_url = f"{VOICEOPS_GATEWAY_URL}{audio_url}"
            audio_response = await client.get(audio_url)
            audio_response.raise_for_status()
            return Response(
                audio_response.content,
                media_type=audio_response.headers.get("content-type", "audio/mpeg"),
            )
    except httpx.HTTPError as exc:
        return Response(
            json.dumps({"ok": False, "reason": type(exc).__name__, "message": "Local VoiceOps TTS call failed."}),
            status_code=502,
            media_type="application/json",
        )


@app.post("/api/voiceops/transcribe")
async def voiceops_transcribe(request: Request) -> dict:
    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="audio_required")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            gateway_response = await client.post(
                f"{VOICEOPS_GATEWAY_URL}/api/voice/transcribe",
                files={"audio": ("voice.webm", content, request.headers.get("content-type") or "audio/webm")},
            )
            if gateway_response.status_code in {401, 403} or "login_required" in gateway_response.text:
                return {
                    "ok": False,
                    "reason": "login_required",
                    "message": "Local VoiceOps transcription requires an authenticated VoiceOps session.",
                }
            gateway_response.raise_for_status()
            data = gateway_response.json()
            transcript = data.get("text") or data.get("transcript") or data.get("result", {}).get("text")
            return {"ok": bool(transcript), "text": transcript or "", "engine": "voiceops_local"}
    except httpx.HTTPError as exc:
        return {"ok": False, "reason": type(exc).__name__, "message": "Local VoiceOps transcription call failed."}


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

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.adapters import BrightDataAdapter, CogneeMemoryAdapter, DemoMemoryAdapter
from app.brain import PersonalBrain
from app.models import BrainRequest, BrainResponse

app = FastAPI(title="InnerOS Personal Brain", version="0.1.0")


def build_brain() -> PersonalBrain:
    if os.getenv("USE_COGNEE", "0") == "1":
        memory = CogneeMemoryAdapter()
    else:
        memory = DemoMemoryAdapter(
            seed=[
                "InnerOS is a local-first AI operating system that coordinates memory, tools and agents.",
                "Ralphi IA already receives opportunity signals and stores operational memory in MongoDB and Qdrant.",
                "Bright Data is already configured server-side in InnerOS for live public web research.",
                "Current hackathon goal: build a Personal Brain that remembers, discovers, reasons, acts, verifies and learns.",
            ]
        )
    return PersonalBrain(memory=memory, web=BrightDataAdapter())


brain = build_brain()


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "inneros-personal-brain"}


@app.post("/api/brain", response_model=BrainResponse)
async def ask_brain(request: BrainRequest) -> BrainResponse:
    return await brain.answer(request.prompt, act=request.act)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>InnerOS Personal Brain</title>
<style>
body{font-family:system-ui;margin:0;background:#0b1020;color:#eef2ff}
main{max-width:960px;margin:48px auto;padding:24px}
.card{background:#131a2f;border:1px solid #273253;border-radius:18px;padding:24px;margin:18px 0}
textarea{width:100%;min-height:110px;background:#0b1020;color:#fff;border:1px solid #3b4b78;border-radius:12px;padding:14px}
button{padding:12px 18px;border-radius:10px;border:0;font-weight:700;cursor:pointer}
pre{white-space:pre-wrap}
.badge{display:inline-block;padding:6px 10px;border-radius:999px;background:#23315c;margin-right:6px}
</style>
</head>
<body><main>
<h1>InnerOS Personal Brain</h1>
<p>Remember → Discover → Reason → Act → Verify → Remember</p>
<div class="card">
<span class="badge">Cognee memory</span><span class="badge">Bright Data live web</span>
<span class="badge">AWS Strands</span><span class="badge">Docker-safe actions</span>
</div>
<div class="card">
<textarea id="q">What opportunity should I focus on today, based on what you know about me and what is happening now?</textarea>
<label><input id="act" type="checkbox"/> Prepare a safe action</label><br/><br/>
<button onclick="go()">Ask my brain</button>
</div>
<div class="card"><pre id="out">Ready.</pre></div>
<script>
async function go(){
 const out=document.getElementById('out'); out.textContent='Thinking...';
 const r=await fetch('/api/brain',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:document.getElementById('q').value,act:document.getElementById('act').checked})});
 out.textContent=JSON.stringify(await r.json(),null,2);
}
</script>
</main></body></html>"""

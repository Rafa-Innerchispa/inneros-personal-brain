from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.adapters import (
    BrightDataAdapter,
    CogneeMemoryAdapter,
    DemoMemoryAdapter,
    InnerOSMemoryAdapter,
)
from app.brain import PersonalBrain
from app.models import BrainRequest, BrainResponse
from app.status import sponsor_status

app = FastAPI(title="InnerOS Personal Brain", version="0.2.0")


def build_brain() -> PersonalBrain:
    if os.getenv("USE_COGNEE", "0") == "1":
        memory = CogneeMemoryAdapter()
    elif os.getenv("INNEROS_MEMORY_ENDPOINT"):
        memory = InnerOSMemoryAdapter()
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
    return {"ok": True, "service": "inneros-personal-brain", "version": "0.2.0"}


@app.get("/api/status")
async def status() -> dict:
    return sponsor_status()


@app.post("/api/brain", response_model=BrainResponse)
async def ask_brain(request: BrainRequest) -> BrainResponse:
    return await brain.answer(request.prompt, act=request.act)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>InnerOS Personal Brain</title>
<style>
:root{--bg:#07111f;--panel:#0e1a2d;--line:#22324d;--text:#f3f7ff;--muted:#9fb0c7;--ok:#5ee3a4;--warn:#ffd166;--accent:#7aa7ff}
*{box-sizing:border-box} body{font-family:Inter,ui-sans-serif,system-ui;margin:0;background:radial-gradient(circle at top,#102442 0,#07111f 45%);color:var(--text)}
main{max-width:1280px;margin:auto;padding:28px}
.top{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:18px}
.brand h1{margin:0;font-size:30px}.brand p{margin:6px 0 0;color:var(--muted)}
.live{padding:8px 12px;border:1px solid #254c3b;border-radius:999px;background:#102a21;color:var(--ok);font-weight:700}
.grid{display:grid;grid-template-columns:260px 1fr 300px;gap:18px}
.panel{background:rgba(14,26,45,.92);border:1px solid var(--line);border-radius:22px;padding:20px;box-shadow:0 12px 40px rgba(0,0,0,.22)}
.source{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid #17243a;color:var(--muted)}
.source:last-child{border-bottom:0}.dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:9px;background:var(--accent)}
.brain{min-height:430px;position:relative;overflow:hidden}
.orbit{position:absolute;inset:38px;border:1px solid #203b62;border-radius:50%;animation:spin 24s linear infinite;opacity:.8}
.orbit.two{inset:88px;animation-direction:reverse;animation-duration:18s}
.node{position:absolute;padding:8px 11px;border-radius:999px;border:1px solid #2d4e7d;background:#10233c;color:#d9e6ff;font-size:12px}
.n1{top:38px;left:46%}.n2{top:130px;right:28px}.n3{bottom:58px;right:88px}.n4{bottom:40px;left:95px}.n5{top:145px;left:28px}
.core{position:absolute;inset:50% auto auto 50%;transform:translate(-50%,-50%);width:150px;height:150px;border-radius:50%;display:grid;place-items:center;text-align:center;background:radial-gradient(circle,#24518d,#10213a 68%);border:1px solid #4c78b6;box-shadow:0 0 60px rgba(75,126,210,.28)}
.core strong{display:block;font-size:18px}.core span{font-size:12px;color:#bed0ea}
@keyframes spin{to{transform:rotate(360deg)}}
.stage{padding:12px 0;border-bottom:1px solid #17243a}.stage:last-child{border-bottom:0}.stage b{display:block}.stage small{color:var(--muted)}
.ask{margin-top:18px}.ask textarea{width:100%;min-height:92px;background:#081423;color:#fff;border:1px solid #304663;border-radius:14px;padding:14px;font:inherit}
.actions{display:flex;gap:10px;margin-top:10px}.actions button{padding:12px 18px;border:0;border-radius:12px;font-weight:800;cursor:pointer}
.primary{background:#e8f0ff;color:#0b1630}.secondary{background:#14233b;color:#dce7f7;border:1px solid #2c4567!important}
.out{margin-top:18px;background:#081321;border:1px solid #1d2e47;border-radius:16px;padding:16px;min-height:150px;white-space:pre-wrap;font-family:ui-monospace,monospace;color:#d9e6ff}
.status{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:18px}.pill{padding:12px;border-radius:14px;background:#0b1829;border:1px solid #1f3553}.pill strong{display:block}.pill span{font-size:12px;color:var(--muted)}
@media(max-width:900px){.grid{grid-template-columns:1fr}.status{grid-template-columns:1fr 1fr}}
</style>
</head>
<body><main>
<div class="top">
  <div class="brand"><h1>InnerOS Personal Brain</h1><p>Remember → Discover → Reason → Act → Verify → Remember</p></div>
  <div class="live">● LIVE BRAIN</div>
</div>

<div class="grid">
  <section class="panel">
    <h3>My Memory</h3>
    <div class="source"><span><i class="dot"></i>InnerOS MCP</span><span>linked</span></div>
    <div class="source"><span><i class="dot"></i>Mongo / Qdrant</span><span>memory</span></div>
    <div class="source"><span><i class="dot"></i>Email</span><span>signals</span></div>
    <div class="source"><span><i class="dot"></i>Notion / Drive</span><span>context</span></div>
    <div class="source"><span><i class="dot"></i>GitHub</span><span>projects</span></div>
    <div class="source"><span><i class="dot"></i>Cognee</span><span>graph</span></div>
  </section>

  <section class="panel brain">
    <div class="orbit"></div><div class="orbit two"></div>
    <div class="node n1">InnerOS</div><div class="node n2">San Francisco</div><div class="node n3">VoiceOps</div>
    <div class="node n4">Physical Guardian</div><div class="node n5">Hackathons</div>
    <div class="core"><div><strong>Personal Brain</strong><span>context + world + action</span></div></div>
  </section>

  <section class="panel">
    <h3>Live Cognition</h3>
    <div class="stage"><b>① Recall</b><small>InnerOS + Cognee</small></div>
    <div class="stage"><b>② Discover</b><small>Bright Data live web</small></div>
    <div class="stage"><b>③ Reason</b><small>AWS Strands + local vLLM</small></div>
    <div class="stage"><b>④ Act</b><small>Docker Sandbox</small></div>
    <div class="stage"><b>⑤ Verify</b><small>Evidence trace</small></div>
    <div class="stage"><b>⑥ Remember</b><small>Store outcome</small></div>
  </section>
</div>

<div class="status" id="status"></div>

<section class="panel ask">
  <textarea id="q">What should I focus on right now based on what you know about me and what is happening in the world?</textarea>
  <div class="actions">
    <button class="primary" onclick="go(false)">THINK</button>
    <button class="secondary" onclick="go(true)">PREPARE ACTION</button>
  </div>
  <div class="out" id="out">Ready. Ask the brain something real.</div>
</section>

<script>
const labels={cognee:'Cognee',brightdata:'Bright Data',strands:'AWS Strands',docker:'Docker Sandbox'};
async function loadStatus(){
 const r=await fetch('/api/status'); const s=await r.json(); const box=document.getElementById('status');
 box.innerHTML=['cognee','brightdata','strands','docker'].map(k=>'<div class="pill"><strong>'+labels[k]+'</strong><span>'+s[k].state+'</span></div>').join('');
}
async function go(act){
 const out=document.getElementById('out'); out.textContent='Recalling memory...\nSearching live context...\nReasoning...';
 const r=await fetch('/api/brain',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:document.getElementById('q').value,act})});
 const data=await r.json();
 out.textContent='ANSWER\n'+data.answer+'\n\nTRACE\n'+data.trace.map(x=>'✓ '+x).join('\n')+'\n\nMEMORY HITS: '+data.memory_hits.length+'   LIVE WEB HITS: '+data.web_hits.length;
}
loadStatus();
</script>
</main></body></html>"""

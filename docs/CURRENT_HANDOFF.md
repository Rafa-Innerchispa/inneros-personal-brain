# CURRENT HANDOFF — InnerOS Personal Brain / Cognee Shared Agent Memory Fabric

**Date:** 2026-09-22  
**Source of truth:** this file + Ralphi coordination + repo state.

## Canonical repo

- Repo: `Rafa-Innerchispa/inneros-personal-brain`
- `main`: `db45f597c90ac91ee2f81f7dba40fda784759834`
- PR #2 MERGED: Live Cognitive Cortex + real Cognee memory.
- PR #3 MERGED: Cognee shared agent memory fabric.
- Unmerged connector work exists on:
  `chatgpt/cognee-agent-connectors-live-20260922`
- Runtime observed on that branch:
  `f364be523eb07c5766f8e42b4153c53eb9d480d2`

Before changing main, verify whether Codex created or merged any newer branch/PR.

## Product architecture

The Personal Brain core must work without Ralphi MCP.

### Core Brain
- Cognee Cloud: persistent structured/shared memory graph
- Bright Data: live external web context
- AWS Strands: reasoning/orchestration
- Local Qwen3-Coder 30B via vLLM: sovereign inference
- Docker Sandboxes: isolated verified action

### External Nervous System
- Ralphi MCP: optional InnerOS connector for tools, Mongo/Qdrant, apps and infrastructure
- GitHub, Gmail, Calendar, Drive/Notion and other sources may attach through connectors
- MCP outage must not kill core cognition

## Cognee

Shared dataset:

`inneros-personal-brain`

Real memory seed:

`app/demo_memory_seed.json`

Seed version:

`2026-09-21-live-cortex-v1`

48 curated operational facts are defined there, covering InnerOS, Ralphi MCP, Physical Guardian, VoiceOps, PC Doctor, InnerChispa, local compute, Resource Fabric, Cognee, Bright Data, Strands, Docker, governance, evidence, cross-agent memory and demo architecture.

Verified:
- Cognee Cloud health/OpenAPI PASS
- remember -> graph build -> recall PASS
- Personal Brain Cognee recall/remember PASS

Direct Strands memory tools are present on the active Codex branch:
- `cognee_recall`
- `cognee_remember`

The branch also exposes a Strands MemoryManager-compatible `search`/`add`
surface through `CogneeMemoryStore` so the demo can prove safe memory injection
and direct Cognee agent memory without tying correctness to one SDK entry-point
shape.

Doc:
`docs/COGNEE_AGENT_MEMORY_FABRIC.md`

## Official Cognee MCP

Service:

`inneros-cognee-mcp.service`

Endpoint:

`http://127.0.0.1:8241/mcp`

Container:

`cognee/cognee-mcp:main`

Keep localhost-only.

Latest verified state:
- active/running
- health 200
- MCP initialize/tools/list PASS
- real recall PASS
- tools observed: remember, recall, forget, search_tools, call_tool

Service was loaded but not enabled for user startup; Codex has a task to enable it if safe.

## Agent connections

### Strands
Already directly connected to the same Cognee Cloud dataset through agent memory tools.

### Antigravity
Cognee MCP was added to:
- `~/.gemini/config/mcp_config.json`
- `~/.gemini/antigravity-ide/mcp_config.json`

Server:
`cognee-http -> http://127.0.0.1:8241/mcp`

Still needs effective consumption verification/native plugin if viable.

### Cursor
`~/.cursor/mcp.json` contains existing secrets.
Do **not** print or overwrite that file.
Safe file writer refused to rewrite it correctly.
Codex must use a supported CLI/config merge route to add Cognee safely.

### Codex
- CLI: `/home/rlopez/.local/bin/codex`
- version observed: `0.144.5`
- authenticated

Current P0:
- A2A: `a2a_f6cfbbd835d21ef1`
- ops task: `ops_cc10f230ffa5`
- last known state: `working / in_progress`

Do not duplicate this task. Check its status first.

Codex is responsible for:
- Codex -> Cognee
- Cursor -> Cognee
- Antigravity -> Cognee verification
- Strands -> Cognee verification
- Cognee MCP startup persistence
- cross-agent shared-memory demo
- Gmail connector prep
- UI real connector states
- tests + PR + merge

## Gmail -> Cognee

Cognee Community has a Gmail connector.

Expected human auth:
- Google OAuth Desktop `credentials.json`
- `gmail.readonly`
- one browser consent
- local token after auth

Never request Gmail password.
Never commit credentials/token to Git.

## Bright Data

- real search PASS
- credentials protected server-side
- balance observed previously: USD 20
- live-first
- VERIFIED REPLAY only on timeout and must be visibly labeled

## Docker Sandboxes

- authenticated
- sbx v0.43.0
- Intel .4 has KVM
- `rlopez` added to `kvm`
- `sg kvm` used for immediate session access
- real sandbox PASS
- real artifact created: `PERSONAL_BRAIN_ACTION.md`

Do not revisit `setfacl`; it was unnecessary.

## Live Cognitive Cortex UI

Merged in PR #2.

Files:
- `app/static/index.html`
- `app/static/style.css`
- `app/static/app.js`

Backend stream:
- `/api/brain/stream`

Visual intent:
- two-brain map: InnerOS/Ralphi local brain + Cognee shared memory brain
- Curated Memory Bridge
- Strands central orchestrator
- Cognee shared-memory graph
- Bright Data observation
- local Qwen reasoning
- Docker action
- Ralphi MCP tools
- orbiting agents/connectors
- real backend-driven stage events only
- Judge Mode proof buttons: REMEMBER, OBSERVE, GOVERN, SHARE

## Service / public URL

Service:

`inneros-personal-brain-demo.service`

Port:

`8230`

Public hostname:

`sovereign-devos.pcdoctor.ai`

Previous 502 root cause:
Cloudflare tunnel targeted `192.168.1.4:8230` while Uvicorn listened only on `127.0.0.1:8230`.

Owner changed service to:

`--host 0.0.0.0 --port 8230`

and restarted it.

**Still needs final verification**:
1. listener on `0.0.0.0:8230`
2. `http://192.168.1.4:8230/health`
3. public hostname health

## Strong evidence already achieved

- Cognee Cloud PASS
- Cognee remember -> graph -> recall PASS
- Bright Data real search PASS
- Strands -> local vLLM/Qwen PASS
- Docker Sandbox real PASS
- Personal Brain Cognee -> Strands -> remember PASS
- previous four-sponsor E2E: `ok=true`, `all_four_green=true`, `docker_executed=true`
- Live Cognitive Cortex CI: pytest + compileall PASS

## Demo story

**ONE MEMORY. MULTIPLE AGENTS. LOCAL-FIRST.**

`Observe -> Remember -> Reason -> Govern/Act -> Verify -> Learn`

- Bright Data = eyes
- Cognee = shared long-term memory
- Strands = orchestration
- Qwen/vLLM = sovereign reasoning
- Docker = safe action
- Ralphi MCP = optional nervous-system connector

Best proof:

**Agent A learns -> Agent B remembers.**

Current Codex branch has implemented this as `/api/proof/share`; it writes a
harmless marker through the configured memory adapter and immediately recalls it
from the same Cognee dataset when live credentials are available.

## Next chat: exact first actions

1. Connect Ralphi IA MCP Full/Short.
2. Run `get_coordination_live` and `bootstrap_context`.
3. Check `a2a_f6cfbbd835d21ef1` and `ops_cc10f230ffa5`.
4. Inspect `chatgpt/cognee-agent-connectors-live-20260922` and any Codex PR/branch.
5. Verify local/LAN/public Personal Brain URL.
6. Do not redo Cognee/Strands/Docker work already closed.
7. Finish Codex/Cursor/Antigravity shared memory.
8. Finish Gmail up to OAuth if needed.
9. Run cross-agent memory demo.
10. Freeze final hackathon build only after PASS.

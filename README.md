# InnerOS Personal Brain

**A sovereign cognitive layer for InnerOS that remembers, discovers, reasons, acts, verifies, and learns across agents.**

InnerOS Personal Brain is a **living InnerOS product**, not a hackathon snapshot. It combines shared long-term memory, live external context, local-first inference, agent orchestration, governed execution, and visible evidence.

The architecture was publicly demonstrated at **Battle of the Personal Brains, San Francisco, September 21, 2026**. The frozen submission from that event is preserved separately in:

`Rafa-Innerchispa/inneros-personal-brain-battle-2026`

See `docs/PRODUCT_BOUNDARY.md` for provenance and repository policy.

InnerOS Personal Brain is a live cognitive loop over the existing InnerOS / Ralphi IA ecosystem. Cognee is the portable shared memory brain, Bright Data is live perception, AWS Strands coordinates reasoning and tools, local Qwen/vLLM keeps inference sovereign, and Docker Sandboxes execute bounded actions only after policy checks.

## Winning Story

Most assistants start from zero and isolate each agent in its own context. Personal Brain provides a reusable cognitive layer:

```text
Observe -> Remember -> Reason -> Govern/Act -> Verify -> Learn
```

The system can:

- remember durable personal/project context through Cognee;
- observe the public web through Bright Data SERP REST or MCP search;
- reason through Strands with direct Cognee memory tools;
- synthesize through local Qwen/vLLM;
- govern actions before execution;
- act in a sandbox when allowed;
- learn verified outcomes back into Cognee.

## Two-Brain Architecture

```text
INNEROS / RALPHI LOCAL BRAIN                 COGNEE SHARED MEMORY BRAIN
private ops, tools, infra                    portable graph memory
Mongo/Qdrant metadata                        dataset: inneros-personal-brain
MCP/A2A coordination                         Codex / Cursor / Antigravity / Strands
        |                                                  ^
        | curated safe facts, decisions, outcomes          |
        +---------------- CURATED MEMORY BRIDGE -----------+
```

Cognee is not a decorative memory cache. It is the central shared dataset that multiple agents can recall from and write to. Ralphi MCP remains the local coordination and operations nervous system; losing that route must not erase the Personal Brain's Cognee memory.

## Memory Model

Personal Brain intentionally keeps two memory tiers separate:

- **Cognee Shared Memory**: curated, durable, reusable knowledge that multiple agents can safely recall.
- **InnerOS Private Memory**: operational/private context retained under owner control in systems such as MongoDB and Qdrant.

Secrets, credentials, customer-private payloads, and private infrastructure details do not belong in shared semantic memory.

## Sponsor Stack

| Technology | Role | Proof surface |
| --- | --- | --- |
| Cognee | Shared graph memory and cross-agent recall | Product memory, official Cognee MCP, Strands memory tools |
| Bright Data | Live public-web perception | SERP REST via `BRIGHTDATA_API_KEY`/zone or MCP `search_engine` |
| AWS Strands Agents | Reasoning, tool orchestration, audit trail | Direct Cognee tools plus local model route |
| Local Qwen/vLLM | Sovereign inference | `LOCAL_LLM_BASE_URL`, local or AMD on-demand route |
| Docker Sandboxes | Governed execution | Bounded artifact action with evidence |
| InnerOS / Ralphi IA | Local coordination fabric | Private MCP/A2A route, not the core memory store |

## Agent Fabric

The product is designed so compatible agents can share the same curated memory fabric. The target proof is simple:

**Agent A learns -> Agent B remembers.**

Strands, Codex, Cursor, Antigravity and other compatible clients can consume the same shared Cognee dataset through direct tools, MCP, or supported plugins while InnerOS retains its private operational layer.

## Demo Evidence

The live UI keeps the judge path simple: ask a question, watch the trace, and read the source evidence. Each answer shows:

- the Strands route decision;
- Cognee memory hits from the shared dataset;
- Bright Data live public-web results, including result titles and URLs;
- local Qwen/vLLM synthesis;
- Docker Sandbox evidence only when `Think + Act` is requested;
- any fallback or verified replay label when a live route is unavailable.

Verified paths include:

- Cognee remember -> graph -> recall
- Strands -> local vLLM/Qwen
- Bright Data live public-web search
- Docker Sandbox real isolated execution
- Personal Brain API and Live Cognitive Cortex
- Evidence-gated external actions

Backend proof routes remain available at `/api/proof/{mode}` for smoke tests and technical review:

- `remember`: Cognee recall with dataset/provenance evidence.
- `observe`: Bright Data live search, with verified replay labeled only when live search is unavailable.
- `govern`: consequential action is proposed, policy blocks it, and the proof says `NOT_EXECUTED`.
- `share`: Agent A writes a harmless marker and Agent B recalls it from Cognee.

The exact current runtime state belongs in `docs/CURRENT_HANDOFF.md`.

## Battle of the Personal Brains Provenance

The September 21, 2026 hackathon accelerated and validated four integrations:

- Cognee
- Bright Data
- AWS Strands Agents
- Docker Sandboxes

Those integrations remain useful product capabilities, but ongoing development happens here in the living InnerOS repo.

Frozen event snapshot:

`Rafa-Innerchispa/inneros-personal-brain-battle-2026`

Source snapshot SHA:

`ba70fb87913615f613bacb3599c1f3d8738eea5b`

## Runtime

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8230
```

Server-side environment variables:

- `COGNEE_SERVICE_URL`
- `COGNEE_API_KEY`
- `COGNEE_DATASET=inneros-personal-brain`
- `BRIGHTDATA_API_KEY`
- `BRIGHTDATA_SERP_ZONE=inneros`
- optional `BRIGHTDATA_API_TOKEN` or `BRIGHTDATA_MCP_URL`
- optional `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_API_KEY`

Secrets are never embedded in the frontend or committed to Git.

External actions are evidence-gated. The system must not claim an action ran unless its executor returns evidence. Shared memory must remain curated and non-sensitive, while private InnerOS context stays under owner-controlled infrastructure.

## Bright Data Choice

For this demo, use **SERP API** first. It gives judges a fast and easy-to-explain "sees the world" proof for public search. Browser API is only needed for multi-step browser interaction, and Web Unlocker is only needed for a specific hard-to-access page extraction.

## Verification Targets

- Product tests: `python -m pytest`
- Python syntax: `python -m compileall app tests`
- Frontend syntax: `node --check app/static/app.js`
- Git whitespace: `git diff --check`

The demo should never claim a live route is active unless the backend reported it. Replays, missing OAuth, on-demand vLLM routes and blocked actions are intentionally labeled.

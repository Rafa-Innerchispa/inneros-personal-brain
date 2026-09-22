# InnerOS Personal Brain

**A sovereign cognitive layer for InnerOS that remembers, discovers, reasons, acts, verifies, and learns across agents.**

InnerOS Personal Brain is a **living InnerOS product**, not a hackathon snapshot. It combines shared long-term memory, live external context, local-first inference, agent orchestration, governed execution, and visible evidence.

The architecture was publicly demonstrated at **Battle of the Personal Brains, San Francisco, September 21, 2026**. The frozen submission from that event is preserved separately in:

`Rafa-Innerchispa/inneros-personal-brain-battle-2026`

See `docs/PRODUCT_BOUNDARY.md` for provenance and repository policy.

## Why

Most AI assistants lose continuity between sessions and isolate each agent in its own context. Personal Brain provides a reusable cognitive layer:

**Observe → Remember → Reason → Act → Verify → Learn**

The core can operate without Ralphi MCP. InnerOS private systems attach as an optional sovereign nervous system rather than being copied into external providers.

## Core architecture

| Component | Permanent role |
| --- | --- |
| Cognee | Shared long-term structured memory / knowledge graph |
| Bright Data | Live external web perception and evidence |
| AWS Strands Agents | Orchestration and tool routing |
| Local Qwen / vLLM | Sovereign model inference |
| Docker Sandboxes | Isolated, evidence-gated action execution |
| Ralphi MCP / InnerOS | Optional private tools, Mongo/Qdrant, coordination, apps and infrastructure |

```text
User / Agent
     |
     v
Personal Brain UI + API
     |
     +---- Strands ------------ orchestration
     |       |
     |       +---- Cognee ----- shared memory
     |       +---- Bright Data  live external evidence
     |       +---- Qwen/vLLM -- local reasoning
     |       +---- Docker ----- isolated action
     |
     +---- Ralphi MCP --------- optional InnerOS nervous system
              |
              +---- private memory / coordination / tools / infrastructure
```

## Memory model

Personal Brain intentionally keeps two memory tiers separate:

- **Cognee Shared Memory**: curated, durable, reusable knowledge that multiple agents can safely recall.
- **InnerOS Private Memory**: operational/private context retained under owner control in systems such as MongoDB and Qdrant.

Secrets, credentials, customer-private payloads, and private infrastructure details do not belong in shared semantic memory.

## Agent fabric

The product is designed so compatible agents can share the same curated memory fabric. The target proof is simple:

**Agent A learns → Agent B remembers.**

Strands, Codex, Cursor, Antigravity and other compatible clients can consume the same shared Cognee dataset through direct tools, MCP, or supported plugins while InnerOS retains its private operational layer.

## Current product evidence

Verified paths include:

- Cognee remember → graph → recall
- Strands → local vLLM/Qwen
- Bright Data live public-web search
- Docker Sandbox real isolated execution
- Personal Brain API and Live Cognitive Cortex
- Four-component end-to-end cognitive flow
- Evidence-gated external actions

The exact current runtime state belongs in `docs/CURRENT_HANDOFF.md`.

## Battle of the Personal Brains provenance

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

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8230
```

Runtime credentials belong in protected environment configuration, never in Git.

## Safety

External actions are evidence-gated. The system must not claim an action ran unless its executor returns evidence. Shared memory must remain curated and non-sensitive, while private InnerOS context stays under owner-controlled infrastructure.

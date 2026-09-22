# InnerOS Personal Brain

**ONE MEMORY. MULTIPLE AGENTS. LOCAL-FIRST.**

Built for **Battle of the Personal Brains, San Francisco, September 21, 2026**.

InnerOS Personal Brain is a live cognitive loop over the existing InnerOS / Ralphi IA ecosystem. Cognee is the portable shared memory brain, Bright Data is live perception, AWS Strands coordinates reasoning and tools, local Qwen/vLLM keeps inference sovereign, and Docker Sandboxes execute bounded actions only after policy checks.

## Winning Story

Most assistants start from zero. This one can:

- remember durable personal/project context through Cognee;
- observe the public web through Bright Data SERP REST or MCP search;
- reason through Strands with direct Cognee memory tools;
- govern actions before execution;
- act in a sandbox when allowed;
- learn verified outcomes back into Cognee.

The demo loop is:

```text
Observe -> Remember -> Reason -> Govern/Act -> Verify -> Learn
```

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

## Sponsor Stack

| Technology | Role | Proof surface |
| --- | --- | --- |
| Cognee | Shared graph memory and cross-agent recall | Product memory, official Cognee MCP, Strands memory tools |
| Bright Data | Live public-web perception | SERP REST via `BRIGHTDATA_API_KEY`/zone or MCP `search_engine` |
| AWS Strands Agents | Reasoning, tool orchestration, audit trail | Direct Cognee tools plus local model route |
| Local Qwen/vLLM | Sovereign inference | `LOCAL_LLM_BASE_URL`, local or AMD on-demand route |
| Docker Sandboxes | Governed execution | Bounded artifact action with evidence |
| InnerOS / Ralphi IA | Local coordination fabric | Private MCP/A2A route, not the core memory store |

## Judge Mode

The UI includes four proof buttons backed by `/api/proof/{mode}`:

- `REMEMBER`: Cognee recall with dataset/provenance evidence.
- `OBSERVE`: Bright Data live search, with verified replay clearly labeled only when live search is unavailable.
- `GOVERN`: consequential action is proposed, policy blocks it, and the proof says `NOT_EXECUTED`.
- `SHARE`: Agent A writes a harmless marker and Agent B recalls it from Cognee.

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

## Bright Data Choice

For this hackathon demo, use **SERP API** first. It gives judges a fast and easy-to-explain "sees the world" proof for public search. Browser API is only needed for multi-step browser interaction, and Web Unlocker is only needed for a specific hard-to-access page extraction.

## Verification Targets

- Product tests: `python -m pytest`
- Python syntax: `python -m compileall app tests`
- Frontend syntax: `node --check app/static/app.js`
- Git whitespace: `git diff --check`

The demo should never claim a live route is active unless the backend reported it. Replays, missing OAuth, on-demand vLLM routes and blocked actions are intentionally labeled.

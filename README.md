# InnerOS Personal Brain

**A personal AI that remembers, discovers, reasons, acts, verifies, and learns.**

Built for **Battle of the Personal Brains, San Francisco, September 21, 2026**.

## Why

Most AI assistants start each conversation from zero. InnerOS Personal Brain combines persistent personal memory with live external context and governed action execution:

**Remember → Discover → Reason → Act → Verify → Remember**

The hackathon application is a thin product layer over the existing InnerOS / Ralphi IA ecosystem. It does not copy private databases or provider secrets into this repository.

## Sponsor stack

| Technology | Role | Live evidence |
| --- | --- | --- |
| Cognee | Persistent structured memory and knowledge graph | Real Cloud remember + recall smoke passes |
| Bright Data | Live public-web intelligence | Existing InnerOS provider/MCP performs real searches |
| AWS Strands Agents | Reasoning and tool orchestration | Real Strands agent runs against local vLLM/Qwen3 |
| Docker Sandboxes | Isolated action execution | Runtime installed on KVM-capable host; owner login required before first sandbox |

## Architecture

```text
Personal Brain UI
       |
       v
   FastAPI
       |
       +---- Cognee Cloud -------- persistent graph memory
       |
       +---- InnerOS / Ralphi MCP - existing personal/project context
       |
       +---- Bright Data ---------- live public web
       |
       +---- AWS Strands ---------- reasoning/orchestration
                  |
                  v
             local vLLM
             Qwen3-Coder 30B
                  |
                  v
           Docker Sandbox
                  |
                  v
          evidence + outcome
                  |
                  +----> Cognee memory
```

## Demo runtime

Primary demo host uses:

- FastAPI / Uvicorn on port 8230
- AWS Strands Agents
- OpenAI-compatible vLLM endpoint on localhost:18000
- Cognee Cloud tenant through a protected runtime environment file
- Docker Sandboxes CLI v0.43.0 on an Ubuntu 24.04 KVM-capable host

Secrets are ignored by Git and never embedded in the frontend.

## Verified smokes

- Product tests: PASS
- Python compileall: PASS
- Strands → local vLLM → Qwen3: PASS
- Cognee Cloud health/OpenAPI: PASS
- Cognee remember → knowledge graph → recall: PASS
- FastAPI health/status/UI: PASS
- Personal Brain API Cognee → Strands → remember outcome: PASS
- Bright Data account/MCP/search: PASS through InnerOS provider
- Docker/KVM/sbx installation: PASS
- Docker account authentication: pending owner device approval

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8230
```

Runtime credentials belong in protected environment configuration, never in Git.

## Safety

External actions are evidence-gated. The system does not claim an action ran unless its executor returns evidence. Docker execution stays disabled until the sandbox runtime is authenticated and verified.

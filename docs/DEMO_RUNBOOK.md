# Judge Demo Runbook

## 0. Opening

> Most AI assistants start from zero. This one doesn't. It remembers my work, watches the live world, reasons about what matters to me, and can act in an isolated environment.

## 1. Prove memory

Ask:

> What marker proves that Cognee persistent memory is working for InnerOS Personal Brain?

Expected visual flow:

**Recall → Cognee → Strands**

The answer should recover `INNEROS_COGNEE_MEMORY_OK_20260921` from the live Cognee dataset.

Point out that the graph contains entities and relationships generated from the stored memory.

## 2. Prove the brain exists outside the demo

Show ChatGPT connected to the InnerOS / Ralphi IA MCP.

Ask a real contextual question about projects, events, or opportunities.

Explain:

> The web UI and ChatGPT are two clients of the same personal intelligence infrastructure.

Then point to the **Shared Memory Fabric** matrix:

- Cognee is the center and the dataset is `inneros-personal-brain`.
- Bright Data is the live-world input.
- Ralphi IA MCP is the ops/coordination layer.
- Codex, Cursor, Antigravity and Strands are all memory surfaces of the same brain.
- Gmail is shown as OAuth-gated when credentials are not configured, which is the
  correct secure state.

For local agent clients, start the Cognee MCP bridge:

```bash
python app/cognee_mcp_proxy.py
```

It serves `remember`, `recall`, and `forget` at
`http://127.0.0.1:8241/mcp` using server-side Cognee environment variables.

## 3. Prove live-world awareness

Use the existing Bright Data MCP/provider to run a live public-web query.

Show the provider evidence and current search result rather than a prepared screenshot.

If venue networking blocks the provider, show that the UI labels the fallback as
verified replay. Do not call replay data live.

For this demo the Bright Data path is **SERP API**. The backend supports both:

- REST SERP through `POST https://api.brightdata.com/request` with
  `BRIGHTDATA_API_KEY` and `BRIGHTDATA_SERP_ZONE=inneros`;
- Bright Data MCP `search_engine` through `BRIGHTDATA_API_TOKEN` or
  `BRIGHTDATA_MCP_URL`.

Use Browser API only for multi-step navigation, login-like flows, or page
interaction; use Web Unlocker only when a specific hard-to-access page must be
fetched or extracted.

## 4. Prove reasoning

In Personal Brain ask a question that combines remembered context with current information.

AWS Strands orchestrates the reasoning while inference remains local through the OpenAI-compatible vLLM endpoint.

## 5. Prove action

Enable Docker Sandboxes only after `sbx ls` succeeds.

Use **PREPARE ACTION**.

Expected flow:

**Strands → Docker Sandbox → artifact → verification → Cognee remember**

The Docker executor must report `executed`; do not present a fallback as live execution.

## 6. Close

> It doesn't just know my files. It remembers my context, sees what is happening now, decides what matters, acts safely, verifies the result, and learns from what happened.

# Cognee Agent Memory Fabric

Cognee is the shared long-term memory layer for InnerOS Personal Brain.

The important architectural rule is that **Cognee is not reached through only one
transport**. The same persistent dataset can be consumed by the product, by the
reasoning agent, by MCP clients, and by agent-specific plugins.

## Canonical shared dataset

`inneros-personal-brain`

This dataset is intentionally separate from Ralphi MCP's own MongoDB/Qdrant
memory. Ralphi MCP can add context, but Cognee remains independently usable.

## Surfaces

### 1. Product HTTP memory

Personal Brain uses Cognee Cloud directly for:

- recall before reasoning;
- remember after verified outcomes;
- curated project memory;
- graph-backed persistent context.

Runtime variables stay server-side:

- `COGNEE_SERVICE_URL`
- `COGNEE_API_KEY`
- `COGNEE_DATASET=inneros-personal-brain`

### 2. Strands direct agent memory

The Strands reasoning agent receives Cognee memory tools directly:

- `cognee_recall`
- `cognee_remember`

These tools call the same Cognee Cloud tenant and dataset as the product. This
is not routed through Ralphi MCP.

The UI reports these calls separately so a judge can see that Cognee is memory
inside the reasoning agent, not merely preloaded prompt context.

### 3. Cognee MCP

InnerOS already owns a reusable standalone Cognee MCP capability in
`innerops-agentic-platform`. Cognee also ships its own official MCP server.

The official server can run in Cloud Mode against the same tenant:

```bash
export COGNEE_SERVICE_URL="https://YOUR-TENANT.aws.cognee.ai"
export COGNEE_API_KEY="YOUR_SECRET"
python src/server.py --transport http --host 127.0.0.1 --port 8001 --path /mcp
```

It exposes the memory-oriented tools `remember`, `recall`, and `forget`.

Any MCP client can then point at:

```text
http://127.0.0.1:8001/mcp
```

Do not put credentials in Git or client-side code.

### 4. Claude Code native plugin

Cognee's plugin captures prompts, tool traces and assistant responses, recalls
context before user turns, and syncs session memory into permanent graph memory.

Install:

```bash
claude plugin marketplace add topoteretes/cognee-integrations
claude plugin install cognee-memory@cognee
```

Configure cloud mode in `~/.cognee/.env`:

```bash
COGNEE_BASE_URL="https://YOUR-TENANT.aws.cognee.ai"
COGNEE_API_KEY="YOUR_SECRET"
COGNEE_PLUGIN_DATASET="inneros-personal-brain"
```

Useful explicit skills:

```text
/cognee-memory:cognee-remember
/cognee-memory:cognee-search
/cognee-memory:cognee-sync
```

### 5. Codex native plugin

Enable hooks in `~/.codex/config.toml`:

```toml
[features]
hooks = true
```

Install:

```bash
codex plugin marketplace add topoteretes/cognee-integrations --ref main
codex plugin add cognee@cognee
```

Use the same `~/.cognee/.env` and the same
`COGNEE_PLUGIN_DATASET=inneros-personal-brain` to share memory.

### 6. Cursor and other MCP clients

Run the shared Cognee MCP endpoint and point the client at its HTTP URL.

Example Cursor MCP configuration:

```json
{
  "mcpServers": {
    "cognee": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

### 7. Antigravity

Cognee maintains a native Antigravity plugin with session storage, recall and
session-to-graph sync. It should use the same Cognee Cloud tenant and shared
dataset when enabled in the InnerOS development fleet.

## Two memory tiers

Cognee supports two useful tiers for agents:

1. **Session memory**: low-cost working context for one active agent/session.
2. **Permanent graph memory**: durable shared knowledge across tools and
   sessions.

Session memory can later be promoted into the permanent graph using Cognee's
`improve` flow.

## Demo story

The judge should be able to see:

```text
Cognee Cloud
   ├── Personal Brain product memory
   ├── Strands direct recall/remember tools
   ├── Cognee MCP → Cursor / MCP clients
   ├── Claude Code plugin
   ├── Codex plugin
   └── Antigravity plugin
```

Ralphi MCP is a separate optional connector:

```text
Ralphi MCP → InnerOS tools / Mongo / Qdrant / apps / infrastructure
```

This separation is deliberate. Losing Ralphi MCP must not erase the Personal
Brain's Cognee memory.

## Hackathon winning angle

The product should be presented as a personal intelligence loop, not a generic
assistant:

```text
Bright Data observes the live world
        |
        v
Cognee stores verified personal memory and durable facts
        |
        v
Strands reasons with local inference and Cognee agent tools
        |
        v
Docker executes bounded actions
        |
        v
Cognee remembers the verified result
```

Ralphi IA MCP sits beside the loop as the coordination and operations layer. It
can assign tasks, carry ecosystem context, and connect other InnerOS surfaces,
but Cognee remains the central brain so the demo still works without coupling
core memory to a single coordinator.

The UI exposes this as the **Shared Memory Fabric** matrix. A judge should be
able to verify:

- Cognee is the central memory dataset: `inneros-personal-brain`.
- Bright Data is the live search/perception source.
- Strands has direct Cognee recall/remember tools.
- Codex, Cursor and Antigravity use the same Cognee MCP/plugin route.
- Ralphi IA MCP is connected as coordination, not as the only memory owner.
- Gmail is prepared as an optional OAuth-gated signal source; no password or
  token is required in Git.

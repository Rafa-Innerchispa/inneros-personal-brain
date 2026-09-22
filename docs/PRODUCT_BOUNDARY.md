# Product Boundary and Provenance

## Repository roles

### Living product

Repository:

`Rafa-Innerchispa/inneros-personal-brain`

Purpose:

Permanent InnerOS product for shared agent memory, cognitive orchestration, local-first inference, external perception, governed action and visible evidence.

Policy:

- ongoing product development belongs here;
- integrations may outlive the event where they were first demonstrated;
- private InnerOS databases and secrets are not copied into public/demo layers;
- the Personal Brain core must remain operable without Ralphi MCP.

### Frozen hackathon snapshot

Repository:

`Rafa-Innerchispa/inneros-personal-brain-battle-2026`

Event:

Battle of the Personal Brains, San Francisco, September 21, 2026.

Canonical source snapshot:

- source repo: `Rafa-Innerchispa/inneros-personal-brain`
- source branch: `hackathon/personal-brains-20260921`
- source SHA: `ba70fb87913615f613bacb3599c1f3d8738eea5b`

The snapshot repository reproduces all 50 source files at identical Git blob SHAs and adds only `FROZEN_SNAPSHOT.md` to explain provenance.

## Development rule

Do not continue feature development in the frozen hackathon repository.

Reusable improvements discovered through the event belong in the living product repository and should retain provenance when relevant.

## Security boundary

The hackathon snapshot may demonstrate interfaces and integrations but must never become a dump of:

- credentials or API tokens;
- private customer data;
- private email content;
- private IP/network topology;
- full InnerOS operational databases;
- secrets from Cursor, Antigravity, Codex or server configuration.

Ralphi MCP, Mongo/Qdrant and other InnerOS-private capabilities remain optional external/private layers around the product core.

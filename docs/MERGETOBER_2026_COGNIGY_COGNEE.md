# Mergetober 2026 — Cognee memory for Cognigy.AI (pre-assignment dossier)

> **Status: RESEARCH / SPEC ONLY — NOT ASSIGNED — NO CODE / PR AUTHORIZED**  
> Updated: 2026-10-14 (America/Guayaquil)  
> Owner / GitHub: `Rafa-Innerchispa` (solo contest participation)  
> Contest: https://www.wemakedevs.org/hackathons/mergetober  
> External issue: **NOT YET FILED**; previous attempt through the ChatGPT GitHub connection returned GitHub `403 Resource not accessible by integration`.  
> Internal issue: not available because Issues are currently **disabled** on this repository (GitHub `410`).

## Purpose and restrictions

Submit a **new Cognee integration for Cognigy.AI** (Cognigy chat/voice agents can recall, remember, and forget long-term memories through Cognee). This is related to but distinct from InnerOS Personal Brain, which already integrates Cognee.

**Non-negotiable Mergetober rules:** solo entry, new or existing `INTEGRATIONS` + `hackathon` issue, ask `@NMZivkovic` for assignment with a design, **DO NOT WRITE THE INTEGRATION CODE OR OPEN A PR UNTIL ASSIGNED** (violation can ban future participation); only ask to be assigned to one task actually about to be built; all submitted code and accompanying article must be original and participant-understood/reviewed, no AI-generated/spam PR; code contributions have signed-off commits and the DCO acknowledgment; open PR during 2026-10-01 through 2026-10-31; publish an original real-world blog article and submit both links through WeMakeDevs when submissions open.

This document is **AI-assisted internal planning**, not a participant-authored official issue, submission article, or code contribution. The human participant should review and adapt the public issue and create/review the code themselves.

## Why this integration makes sense

Cognigy.AI's TypeScript Extension SDK supports custom Flow Nodes and secure **Connections**, making it possible to give existing Cognigy Flows an optional memory backend. Cognee's HTTP memory API exposes `remember`, `recall`, `forget`; Cognee's existing shared `integrations/chat-memory` documents consent, per-user scope, citations, and data deletion semantics.

The intended real-world use is a **returning customer** in a chat or voice Flow who consents to storing a *non-sensitive preference*. A second session recalls that preference, a different test user cannot access it, and an explicit forget operation removes it.

No Bellini footage, customer PII, PC Doctor private keys, local network topology, call recordings, customer emails or InnerOS credentials will be included in the demo.

## Path B official GitHub issue draft — for human review

**Title:**
`Hackathon [Feature]: Add Cognigy.AI memory Flow Nodes for Cognee (Remember / Recall / Forget)`

**Problem statement:**

Cognigy agents have Flows, agent sessions and external API access, but a developer currently has to hand-build the requests, credentials, scoping, and failure handling to use Cognee as a reusable long-term memory provider. A native Cognigy Extension can make Cognee's memory primitives independently installable and easy to use from chat and voice Flows without requiring each project to implement the same API adapter.

**Proposed solution:**

Create `integrations/cognigy/` in `topoteretes/cognee-integrations`, an extension built with Cognigy's `@cognigy/extension-tools` (`createNodeDescriptor`, `createExtension`), with:
- **Cognee Remember:** a Flow Node stores *selected*, consented text with session and provenance metadata in a user-scoped Cognee dataset; no automatic full-transcript ingestion;
- **Cognee Recall:** Flow Node searches relevant knowledge and writes bounded, attributed results to a configured Cognigy Context key; preserves the original message, handles empty results and timeouts;
- **Cognee Forget:** Flow Node explicitly deletes only the current user's scoped dataset and exposes the operation's success or failure for the Flow to acknowledge accurately.

Cognigy Connection fields hold server URL and authentication, not source-code literals. Use Cognee HTTP `POST /api/v1/remember`, `POST /api/v1/recall`, `POST /api/v1/forget`, verifying request and response shapes against the current maintained Cognee version. Cognee Cloud uses `X-Api-Key`; a self-hosted deployment may have other authentication. A Cognigy-hosted Flow can only access a self-hosted Cognee service via an *authorized reachable endpoint*; never expose InnerOS private LAN endpoints or make a public gateway by default.

**Scope, identity and privacy:**

Use one dataset per Cognigy end user (derived from an appropriately scoped, pseudonymous stable ID), distinct session identifiers, and consent gating for `remember`. The HTTP forget API may operate at dataset scope, so per-user datasets avoid accidental shared-memory deletion. Limit data to synthetic facts in tests; never log credentials or contents of private transcripts; bound HTTP timeouts/retries.

**Proposed structure:**

```text
integrations/cognigy/
  README.md
  src/
    module.ts
    connections/cogneeConnection.ts
    nodes/cogneeRemember.ts
    nodes/cogneeRecall.ts
    nodes/cogneeForget.ts
    lib/cogneeClient.ts
  examples/
    returning-caller/README.md
  tests/
    client.test.ts
    scope.test.ts
    consent.test.ts
    nodes.test.ts
    error-handling.test.ts
  package.json
  tsconfig.json
```

Also update `integrations/inventory.yml` to register the integration. Follow existing public Cognigy Extensions and Cognee `chat-memory` conventions where possible; do not duplicate the core memory engine.

**Acceptance criteria:**
1. Install the Cognigy Extension in a real Cognigy account and create a Cognee Connection.
2. Store one opt-in non-sensitive fact in session A; recall the correct fact in session B.
3. Verify that user B cannot see any of user A's memory.
4. Forget user A; subsequent recall finds no previously stored content; user B remains unaffected.
5. Mocked/unit tests for auth headers, URL selection, dataset scoping, consent, invalid payloads, timeouts, 401, 429, 5xx, and deletion semantics.
6. A working documented Flow or reproducible example with real Cognee + Cognigy installation steps.
7. Local-first: tests against self-hosted Cognee and locally runnable unit tests. Any cloud/live test should be explicitly approved/recorded and avoid unnecessary paid model usage.
8. Signed-off commits, DCO and participant-written article demonstrating the real use case.

**Assignment request (append in issue after human review):**

Hi @NMZivkovic (cc @dexters1), I'd like to build this as a new Mergetober integration. I have a Cognigy.AI account for live verification and already used Cognee as a durable agent memory layer. I would implement it as a Cognigy TypeScript Extension with opt-in Remember, scoped Recall, and safe Forget nodes, secure Connections, unit tests and a documented real-instance example. I searched the existing Cognee issue backlog and integration inventories for a Cognigy integration and found none as of October 14. Could you confirm the proposal is in scope, apply the `INTEGRATIONS` and `hackathon` labels, and assign the issue to `@Rafa-Innerchispa`? I will not start implementation or open a PR before assignment.

## Architecture (planning only)

```text
Cognigy.AI authenticated Flow
    ├── Consent/identity check
    ├── Cognee Recall Node ─────────────────┐
    ├── LLM / human-facing response          │
    ├── Cognee Remember Node ────────────────┤ HTTPS, timeouts, credentials in Connection
    └── Cognee Forget Node (user initiated) ─┘
                                           ↓
                             Cognee HTTP API (local via secure reachability,
                                  or Cognee Cloud if approved)
                                           ↓
                             User-scoped dataset / session
```

No bidirectional bulk import, no automatic upload of private InnerOS memory, no live voice transcripts or personal identifiers in shared memory.

## Verification matrix (for later, after assignment)

| Case | Expected result |
| --- | --- |
| No Cognee backend | Fail open for Recall; ordinary Cognigy Flow stays usable |
| 401 / invalid credential | Clear operator-only auth error; no secret leak |
| 429 / timeout / 5xx | Bounded retry or bounded failure; no hanging chat turn |
| Consent absent | Remember performs no write |
| Session A → Session B | Explicitly consented fact can be recalled |
| Two different user IDs | No cross-user memory |
| Forget user A | User A data removed only after confirmed backend outcome |
| Repeated Remember | Idempotency strategy verified against actual backend behavior |
| Output injection | Bounded text in configured Context key without prompt overwrite |
| Cognee local endpoint | Works only when reachable from Cognigy runtime; documented safely |

## Repository access / blocker

A test through the currently connected ChatGPT GitHub App produced:
- `POST /repos/topoteretes/cognee/issues`: `403 Resource not accessible by integration`. This means authorization/scope limitation, not that the repository is private.
- `POST /repos/Rafa-Innerchispa/inneros-personal-brain/issues`: `410 Issues has been disabled in this repository`.

The external repo requires proper **GitHub Issues: write** permission to a public repository *that is not owned by us*. Reauthorizing the same app might not permit editing arbitrary other organizations' repositories, depending on how the App is installed. GitHub access must be approved through the proper browser/OAuth flow, or via a separately authorized security-controlled GitHub relay (not by pasting PATs or secrets into ChatGPT). Only enable minimal needed scopes; do not request repo admin/write on Cognee to create an issue.

Enabling Issues on the owned Personal Brain repository is a separate optional admin operation; it is **not** a prerequisite to submitting the official Cognee issue. If that setting cannot be changed with current tool permissions, request a secured local admin action or later human UI action.

## References

- Contest rules: https://www.wemakedevs.org/hackathons/mergetober/rules
- Builder's toolkit: https://www.wemakedevs.org/hackathons/mergetober/resources
- Cognee integrators: https://github.com/topoteretes/cognee-integrations
- Cognee chat-memory: https://github.com/topoteretes/cognee-integrations/tree/main/integrations/chat-memory
- Cognigy extension SDK: https://support.cognigy.com/hc/en-us/articles/360016534459-Getting-Started-with-Extensions
- Cognigy public extensions examples: https://github.com/Cognigy/Extensions
- Cognee HTTP overview: https://docs.cognee.ai/api-reference/introduction
- InnerOS Personal Brain: https://github.com/Rafa-Innerchispa/inneros-personal-brain

## Status checklist

- [x] Contest registration (participant confirmed)
- [x] Read rules and identify hard stop
- [x] Locate prior InnerOS Cognee implementation
- [x] Deduplicate proposed Cognigy integration against official backlog and integration inventory (2026-10-14)
- [x] Prepare Path B issue technical draft and test matrix
- [ ] Human reviews/proposes issue in Cognee official repository (or properly authorized connector)
- [ ] `@NMZivkovic` formally assigns issue
- [ ] Only then begin coding, testing, PR and human-written article
- [ ] Open PR by Oct 31 and submit PR/blog links via event form

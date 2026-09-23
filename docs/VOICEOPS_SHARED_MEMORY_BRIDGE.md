# VoiceOps Shared Memory Bridge

Personal Brain exposes a narrow **loopback-only** contract so a local VoiceOps runtime can persist a verified operational outcome into the same curated memory fabric used by Cognee.

## Safety contract

- The write endpoint is available only from loopback.
- `verification_passed=true` is mandatory.
- `source_truth` must be `LIVE`, `REPLAY`, or `SYNTHETIC`.
- Payload text is passed through the existing shared-memory curator before storage.
- Secrets, local IPs, private filesystem paths, raw customer payloads, and private infrastructure details must not be written to shared memory.
- The endpoint returns a bounded receipt and memory identifier rather than echoing the stored text.
- This bridge does **not** authorize or execute actions. VoiceOps/FieldOps governance remains authoritative.

## Local endpoints

- `POST /api/internal/shared-memory/verified-outcome`
- `GET /api/internal/shared-memory/recall?q=...`

The endpoints are intentionally not a public Cognee API. They exist to support local cross-agent proof such as:

`VoiceOps verifies outcome -> Personal Brain curates/stores -> another agent recalls`

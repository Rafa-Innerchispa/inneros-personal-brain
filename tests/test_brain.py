from pathlib import Path

import pytest

from app.adapters import BrightDataAdapter, DemoMemoryAdapter
from app.brain import PersonalBrain
from app.cognee_agent_tools import CogneeAgentMemoryTools, CogneeMemoryStore
from app.memory_curator import curate_for_cognee
from app.memory_fabric import build_memory_fabric
from app.main import _is_loopback_host, _voiceops_public_health, _voiceops_shared_memory_receipt
from app.models import Evidence
from app.proof_modes import ProofModeRunner


class NoWeb:
    def __init__(self):
        self.calls = 0

    async def search(self, query: str, limit: int = 5):
        self.calls += 1
        return []


class FlakyIdentityWeb:
    def __init__(self):
        self.queries = []

    async def search(self, query: str, limit: int = 5):
        self.queries.append(query)
        if len(self.queries) == 1:
            return [
                Evidence(
                    source="brightdata",
                    summary="No high-confidence public organic result was returned.",
                    metadata={"no_public_matches": True, "query": query},
                )
            ]
        return [
            Evidence(
                source="brightdata",
                summary="Rafael Lopez Rafa-Innerchispa public profile",
                metadata={"title": "Rafael Lopez Rafa-Innerchispa", "url": "https://github.com/Rafa-Innerchispa"},
            )
        ]


class NoisyIdentityWeb:
    def __init__(self):
        self.calls = 0

    async def search(self, query: str, limit: int = 5):
        self.calls += 1
        return [
            Evidence(
                source="brightdata",
                summary="Rafael Lopez Rafa-Innerchispa public profile",
                metadata={"title": "Rafael Lopez Rafa-Innerchispa", "url": "https://github.com/Rafa-Innerchispa"},
            ),
            Evidence(
                source="brightdata",
                summary="A different Rafael Lopez, illustrator and muralist.",
                metadata={"title": "Rafael López | Illustrator", "url": "https://rafaellopez.com/"},
            ),
        ]


class FastTestBrain(PersonalBrain):
    async def _reason(self, prompt: str, context: str) -> str:
        return "TEST_REASONING_OK"


@pytest.mark.asyncio
async def test_auto_route_uses_all_main_sources_for_any_question():
    memory = DemoMemoryAdapter(seed=["InnerOS builds local-first AI systems."])
    web = NoWeb()
    brain = FastTestBrain(memory=memory, web=web)

    result = await brain.answer("What should I do next?", act=False)

    assert web.calls == 1
    assert result.memory_hits
    assert result.route["route_policy"] == "auto_all_sources"
    assert "cognee_shared_memory" in result.route["sources_used"]
    assert "brightdata_live_web" in result.route["sources_used"]
    assert "local_qwen_vllm" in result.route["sources_used"]


@pytest.mark.asyncio
async def test_brain_remembers_outcome():
    memory = DemoMemoryAdapter(seed=["InnerOS builds local-first AI systems."])
    brain = FastTestBrain(memory=memory, web=NoWeb())
    result = await brain.answer("What do I build?", act=True)

    assert result.answer
    assert result.memory_hits
    assert result.actions[0]["status"] in {"requires_runtime", "executed", "failed"}
    assert "remember:store-outcome" in result.trace
    assert len(memory.seed) == 2


@pytest.mark.asyncio
async def test_brain_emits_real_cognitive_stages():
    memory = DemoMemoryAdapter(seed=["Physical Guardian is an InnerOS project."])
    brain = FastTestBrain(memory=memory, web=NoWeb())
    events = []

    async def emit(event):
        events.append(event)

    result = await brain.answer("What is Physical Guardian?", act=False, emit=emit)

    assert result.answer == "TEST_REASONING_OK"
    technologies = [event["technology"] for event in events]
    stages = [event["stage"] for event in events]
    assert "cognee" in technologies
    assert "brightdata" in technologies
    assert "strands" in technologies
    assert "local_model" in technologies
    assert "remember" in stages
    assert "observe" in stages
    assert "reason" in stages
    assert "learn" in stages


def test_live_cortex_static_assets_exist():
    static = Path("app/static")
    assert (static / "index.html").exists()
    assert (static / "style.css").exists()
    assert (static / "app.js").exists()

    html = (static / "index.html").read_text(encoding="utf-8")
    assert "BATTLE OF THE PERSONAL BRAINS" in html
    assert "LIVE COGNITIVE CORTEX" in html
    assert "INNEROS / RALPHI" in html


def test_cognee_agent_memory_tools_fail_closed_without_credentials(monkeypatch):
    monkeypatch.delenv("COGNEE_SERVICE_URL", raising=False)
    monkeypatch.delenv("COGNEE_API_KEY", raising=False)
    tools = CogneeAgentMemoryTools()
    assert tools.ready is False
    assert tools.build() == []
    assert tools.usage()["direct_agent_tools"] is True


def test_live_cortex_explains_shared_agent_memory():
    html = Path("app/static/index.html").read_text(encoding="utf-8")
    js = Path("app/static/app.js").read_text(encoding="utf-8")
    assert "GRAPH · MCP · AGENTS" in html
    assert "agents-strip" not in html
    assert "CODEX · CURSOR · AG" not in html
    assert '"codex"' in js
    assert '"cursor"' in js
    assert '"antigravity"' in js
    assert "Curated Memory Bridge" in js
    assert "Cognee MCP" in js


def test_memory_fabric_centers_cognee_and_brightdata(monkeypatch):
    monkeypatch.delenv("COGNEE_SERVICE_URL", raising=False)
    monkeypatch.delenv("COGNEE_LIVE_VERIFIED", raising=False)
    monkeypatch.setenv("COGNEE_API_KEY", "secret-value")
    monkeypatch.setenv("BRIGHTDATA_API_TOKEN", "secret-value")
    monkeypatch.delenv("GMAIL_OAUTH_CLIENT_FILE", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    fabric = build_memory_fabric().as_dict()
    surfaces = {surface["key"]: surface for surface in fabric["surfaces"]}

    assert fabric["central_memory"] == "cognee"
    assert fabric["dataset"] == "inneros-personal-brain"
    assert fabric["security"]["secrets_in_frontend"] is False
    assert fabric["security"]["ralphi_required_for_core_memory"] is False
    assert fabric["brains"]["shared"]["label"] == "COGNEE SHARED MEMORY BRAIN"
    assert surfaces["personal_brain"]["state"] == "configured"
    assert surfaces["strands"]["transport"] == "direct Cognee agent tools"
    assert surfaces["brightdata"]["state"] == "ready"
    assert "SERP" in surfaces["brightdata"]["transport"]
    assert surfaces["ralphi"]["required_for_core"] is False
    assert surfaces["gmail"]["state"] == "pending_auth"


def test_live_cortex_renders_fabric_matrix():
    html = Path("app/static/index.html").read_text(encoding="utf-8")
    js = Path("app/static/app.js").read_text(encoding="utf-8")
    css = Path("app/static/style.css").read_text(encoding="utf-8")

    assert "SHARED MEMORY FABRIC" in html
    assert "fabricMatrix" in html
    assert "fabricOrder" in js
    assert "renderFabric" in js
    assert "brightdata" in js
    assert ".fabric-row" in css


def test_voiceops_is_visible_as_local_voice_route():
    html = Path("app/static/index.html").read_text(encoding="utf-8")
    js = Path("app/static/app.js").read_text(encoding="utf-8")

    assert "voiceEngineBtn" in html
    assert "Voice: Browser" in html
    assert "/api/voiceops/status" in js
    assert "/api/voiceops/tts" in js
    assert "/api/voiceops/transcribe" in js
    assert '"voiceops"' in js


def test_voiceops_public_health_accepts_string_whisper_and_filters_private_urls():
    status = _voiceops_public_health(
        {
            "ok": True,
            "whisper": "http://127.0.0.1:9001",
            "tts": {"ready": True, "default_engine": "xtts-v2"},
            "vllm": {"ok": True, "model": "Qwen"},
            "qdrant": {"ok": True, "collection": "inneros_kb", "points_count": 3},
            "mcp": {"profile": "voice_owner_compact", "visible_tool_count": 43, "full_catalog_access": True},
            "public_urls": ["https://voz.pcdoctor.ai"],
            "auth_required": True,
            "cloud_fallback": False,
        },
        {"voices": [{"id": "xtts:rafael", "label": "Rafael", "provider": "xtts-v2"}]},
    )

    assert status["ok"] is True
    assert status["whisper"]["configured"] is True
    assert status["tts"]["voices"][0]["id"] == "xtts:rafael"
    dumped = str(status)
    assert "127.0.0.1:9001" not in dumped
    assert "https://voz.pcdoctor.ai" in dumped


def test_cognee_memory_curator_redacts_secrets_and_private_infra():
    curated = curate_for_cognee(
        "api_key=03556641-5032-4717-b35c-da265f20e6e7 "
        "Bearer abcdefghijklmnopqrstuvwxyz123456 "
        "http://127.0.0.1:8241/mcp /home/rlopez/inneros/file.txt "
        "C:\\Users\\hrlg\\secret.txt"
    )

    assert "03556641" not in curated.text
    assert "Bearer abc" not in curated.text
    assert "127.0.0.1" not in curated.text
    assert "/home/rlopez" not in curated.text
    assert "C:\\Users\\hrlg" not in curated.text
    assert curated.policy["curated"] is True
    assert curated.policy["secret_redactions"] >= 2
    assert curated.policy["private_infra_redactions"] >= 2


def test_memory_fabric_reports_distributed_routes():
    fabric = build_memory_fabric().as_dict()
    routes = {route["key"]: route for route in fabric["route_status"]}

    assert routes["cognee_mcp"]["route_class"] == "LOCAL"
    assert routes["ralphi_mcp_inneros_fabric"]["route_class"] == "TAILSCALE"
    assert routes["qwen_vllm"]["route_class"] == "LOCAL_OR_AMD_ON_DEMAND"
    assert routes["voiceops"]["route_class"] == "LOCAL"
    assert "Windows localhost" in routes["qwen_vllm"]["evidence"]


def test_cognee_memory_store_is_fail_closed_without_credentials(monkeypatch):
    monkeypatch.delenv("COGNEE_API_KEY", raising=False)
    store = CogneeMemoryStore()

    assert store.ready is False
    assert store.status()["compatible_surface"] == "search/add"


@pytest.mark.asyncio
async def test_govern_proof_mode_blocks_consequential_action():
    runner = ProofModeRunner(memory=DemoMemoryAdapter(seed=[]), web=NoWeb())

    result = await runner.run("govern")

    assert result["status"] == "PASS"
    assert result["evidence"][0]["metadata"]["truth"] == "NOT_EXECUTED"
    assert "HUMAN APPROVAL REQUIRED" in result["summary"]


def test_brightdata_rest_serp_payload_extracts_organic_results():
    payload = {
        "parsed": {
            "organic_results": [
                {"title": "One", "description": "First result", "link": "https://example.com/1"},
                {"title": "Two", "description": "Second result", "link": "https://example.com/2"},
            ]
        }
    }

    organic = BrightDataAdapter._extract_rest_organic(payload)

    assert [item["title"] for item in organic] == ["One", "Two"]


@pytest.mark.asyncio
async def test_identity_questions_use_cognee_and_brightdata_in_auto_route():
    memory = DemoMemoryAdapter(seed=["Ralphi is building InnerOS Personal Brain for the hackathon."])
    web = NoWeb()
    brain = FastTestBrain(memory=memory, web=web)

    result = await brain.answer("quien soy yo y que estamos construyendo?", act=False)

    assert web.calls == 1
    assert result.memory_hits
    assert result.web_hits
    assert result.web_hits[0].metadata["no_public_matches"] is True
    assert result.route["route_policy"] == "identity_memory_web"
    assert result.route["evidence_refs"]["brightdata_query"] == "Rafael Lopez InnerChispa Rafa-Innerchispa"
    assert "local_qwen_vllm" in result.route["sources_used"]


@pytest.mark.asyncio
async def test_identity_questions_retry_brightdata_when_first_serp_has_no_matches():
    memory = DemoMemoryAdapter(seed=["Ralphi is building InnerOS Personal Brain for the hackathon."])
    web = FlakyIdentityWeb()
    brain = FastTestBrain(memory=memory, web=web)

    result = await brain.answer("quien soy yo Rafael Lopez InnerChispa?", act=False)

    assert len(web.queries) == 2
    assert web.queries[0] == "Rafael Lopez InnerChispa Rafa-Innerchispa"
    assert web.queries[1] == "Rafa-Innerchispa"
    assert result.web_hits[0].metadata["title"] == "Rafael Lopez Rafa-Innerchispa"
    assert result.route["evidence_refs"]["brightdata_query"] == "Rafa-Innerchispa"


@pytest.mark.asyncio
async def test_identity_questions_filter_unrelated_same_name_web_hits():
    memory = DemoMemoryAdapter(seed=["Ralphi is building InnerOS Personal Brain for the hackathon."])
    web = NoisyIdentityWeb()
    brain = FastTestBrain(memory=memory, web=web)

    result = await brain.answer("quien soy yo Rafael Lopez InnerChispa?", act=False)

    assert web.calls == 1
    assert len(result.web_hits) == 1
    assert result.web_hits[0].metadata["url"] == "https://github.com/Rafa-Innerchispa"


@pytest.mark.asyncio
async def test_project_memory_questions_use_brightdata_in_auto_route():
    memory = DemoMemoryAdapter(seed=["InnerOS Personal Brain uses Cognee, Bright Data, Qwen and Docker."])
    web = NoWeb()
    brain = FastTestBrain(memory=memory, web=web)

    result = await brain.answer(
        "What do you remember about what I am building, and what should I focus on next?",
        act=False,
    )

    assert web.calls == 1
    assert result.route["route_policy"] == "personal_memory_web"
    assert result.web_hits[0].metadata["no_public_matches"] is True
    assert "brightdata_live_web" in result.route["sources_used"]


def test_voiceops_shared_memory_receipt_requires_verified_outcome():
    with pytest.raises(ValueError, match="verification_passed_required"):
        _voiceops_shared_memory_receipt(
            {
                "correlation_id": "voiceops-001",
                "summary": "work order created",
                "evidence_ref": "evidence://voiceops/001",
                "source_truth": "LIVE",
                "verification_passed": False,
            }
        )


def test_voiceops_shared_memory_receipt_curates_secrets_and_builds_safe_receipt():
    text, metadata, receipt = _voiceops_shared_memory_receipt(
        {
            "correlation_id": "voiceops-002",
            "summary": "Verified action completed using api_key=super-secret at 127.0.0.1",
            "evidence_ref": "evidence://voiceops/002",
            "source_truth": "LIVE",
            "verification_passed": True,
        }
    )

    assert "super-secret" not in text
    assert "127.0.0.1" not in text
    assert metadata["source"] == "voiceops"
    assert metadata["verification_passed"] is True
    assert receipt["stored"] is True
    assert receipt["source_truth"] == "LIVE"
    assert len(receipt["memory_id"]) == 20


def test_shared_memory_internal_route_is_loopback_only():
    assert _is_loopback_host("127.0.0.1") is True
    assert _is_loopback_host("::1") is True
    assert _is_loopback_host("192.168.1.4") is False
    assert _is_loopback_host("203.0.113.9") is False

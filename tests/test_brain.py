from pathlib import Path

import pytest

from app.adapters import BrightDataAdapter, DemoMemoryAdapter
from app.brain import PersonalBrain
from app.cognee_agent_tools import CogneeAgentMemoryTools, CogneeMemoryStore
from app.memory_fabric import build_memory_fabric
from app.proof_modes import ProofModeRunner


class NoWeb:
    def __init__(self):
        self.calls = 0

    async def search(self, query: str, limit: int = 5):
        self.calls += 1
        return []


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
    assert "CODEX" in html
    assert "CURSOR" in html
    assert "ANTIGRAVITY" in html
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


def test_memory_fabric_reports_distributed_routes():
    fabric = build_memory_fabric().as_dict()
    routes = {route["key"]: route for route in fabric["route_status"]}

    assert routes["cognee_mcp"]["route_class"] == "LOCAL"
    assert routes["ralphi_mcp_inneros_fabric"]["route_class"] == "TAILSCALE"
    assert routes["qwen_vllm"]["route_class"] == "LOCAL_OR_AMD_ON_DEMAND"
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
    assert result.route["evidence_refs"]["brightdata_query"] == '"Rafael Lopez" "InnerChispa"'
    assert "local_qwen_vllm" in result.route["sources_used"]


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

from pathlib import Path

import pytest

from app.adapters import DemoMemoryAdapter
from app.brain import PersonalBrain


class NoWeb:
    async def search(self, query: str, limit: int = 5):
        return []


class FastTestBrain(PersonalBrain):
    async def _reason(self, prompt: str, context: str) -> str:
        return "TEST_REASONING_OK"


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
    assert "EXTERNAL NERVOUS SYSTEM" in html

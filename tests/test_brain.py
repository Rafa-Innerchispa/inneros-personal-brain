import pytest

from app.adapters import DemoMemoryAdapter
from app.brain import PersonalBrain


class NoWeb:
    async def search(self, query: str, limit: int = 5):
        return []


@pytest.mark.asyncio
async def test_brain_remembers_outcome():
    memory = DemoMemoryAdapter(seed=["Rafael builds local-first AI systems."])
    brain = PersonalBrain(memory=memory, web=NoWeb())
    result = await brain.answer("What do I build?", act=True)

    assert result.answer
    assert result.memory_hits
    assert result.actions[0]["status"] in {"requires_runtime", "executed", "failed"}
    assert "remember:store-outcome" in result.trace
    assert len(memory.seed) == 2

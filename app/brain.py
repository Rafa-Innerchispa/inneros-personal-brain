from __future__ import annotations

import os
from dataclasses import dataclass

from app.models import BrainResponse, Evidence


@dataclass
class PersonalBrain:
    memory: object
    web: object

    async def answer(self, prompt: str, act: bool = False) -> BrainResponse:
        trace = ["remember:query-memory"]
        memory_hits: list[Evidence] = await self.memory.search(prompt)

        trace.append("discover:query-live-web")
        web_hits: list[Evidence] = await self.web.search(prompt)

        context = "\n".join(
            [f"MEMORY: {x.summary}" for x in memory_hits]
            + [f"WEB: {x.summary}" for x in web_hits]
        )

        answer = await self._reason(prompt, context)
        actions: list[dict] = []

        if act:
            trace.append("act:prepare-safe-action")
            actions.append(
                {
                    "type": "proposal",
                    "status": "requires_human_approval",
                    "summary": "Prepared a bounded next action; no external write executed automatically.",
                }
            )

        trace.append("verify:record-evidence")
        await self.memory.remember(
            f"Personal Brain handled: {prompt}\nResult: {answer[:500]}",
            {"trace": trace, "action_count": len(actions)},
        )
        trace.append("remember:store-outcome")

        return BrainResponse(
            answer=answer,
            memory_hits=memory_hits,
            web_hits=web_hits,
            actions=actions,
            trace=trace,
        )

    async def _reason(self, prompt: str, context: str) -> str:
        try:
            from strands import Agent
            from strands.models.openai import OpenAIModel

            model = OpenAIModel(
                client_args={
                    "api_key": os.getenv("LOCAL_LLM_API_KEY", "local"),
                    "base_url": os.getenv("LOCAL_LLM_BASE_URL", "http://192.168.1.5:8000/v1"),
                },
                model_id=os.getenv(
                    "LOCAL_LLM_MODEL",
                    "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
                ),
            )
            agent = Agent(
                model=model,
                system_prompt=(
                    "You are InnerOS Personal Brain. Use memory and live-web evidence. "
                    "Be concise, distinguish remembered facts from live findings, and never "
                    "claim an external action was executed unless evidence says so."
                ),
            )
            result = agent(f"USER REQUEST:\n{prompt}\n\nEVIDENCE:\n{context}")
            return str(result)
        except Exception:
            if context:
                return (
                    "I combined available personal memory and live context. "
                    f"For this request, the strongest evidence I found was:\n{context[:1800]}"
                )
            return "I do not have enough evidence yet. Add memory or enable live web search."

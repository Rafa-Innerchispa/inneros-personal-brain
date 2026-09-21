from __future__ import annotations

import os
from dataclasses import dataclass

from app.models import BrainResponse, Evidence
from app.sandbox import DockerSandboxExecutor


@dataclass
class PersonalBrain:
    memory: object
    web: object

    async def answer(self, prompt: str, act: bool = False) -> BrainResponse:
        trace = ["remember:query-memory"]
        memory_hits: list[Evidence] = await self.memory.search(prompt)

        trace.append("discover:query-live-web")
        web_hits: list[Evidence] = await self.web.search(prompt)

        reason_memory_hits = memory_hits
        if act:
            historical_failure_terms = (
                "sandboxing issue",
                "failed due to",
                "could not be created",
                "requires_runtime",
                "docker action did not complete",
            )
            reason_memory_hits = [
                x for x in memory_hits
                if not any(term in x.summary.lower() for term in historical_failure_terms)
            ]

        context = "\n".join(
            [f"MEMORY: {x.summary}" for x in reason_memory_hits]
            + [f"WEB: {x.summary}" for x in web_hits]
        )

        answer = await self._reason(prompt, context)
        actions: list[dict] = []

        if act:
            trace.append("act:docker-sandbox")
            executor = DockerSandboxExecutor()
            sandbox_result = executor.prepare_artifact(
                f"User request: {prompt}\n\nReasoned answer:\n{answer}"
            )
            actions.append(sandbox_result)
            if sandbox_result.get("ok") and sandbox_result.get("status") == "executed":
                answer += (
                    "\n\nEXECUTION EVIDENCE: Docker Sandbox executed the action successfully. "
                    f"Artifact: {sandbox_result.get('artifact', 'created')}."
                )
            else:
                answer += (
                    "\n\nEXECUTION EVIDENCE: The current Docker action did not complete. "
                    f"Status: {sandbox_result.get('status', 'unknown')}."
                )

        trace.append("verify:record-evidence")
        await self.memory.remember(
            f"Personal Brain handled: {prompt}\nResult: {answer[:500]}",
            {"trace": trace, "actions": actions},
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
            from strands import Agent, tool
            from strands.models.openai import OpenAIModel

            @tool
            def evidence_marker(value: str = "ok") -> str:
                """Return a harmless marker for OpenAI-compatible tool schemas."""
                return value

            model = OpenAIModel(
                client_args={
                    "api_key": os.getenv("LOCAL_LLM_API_KEY", "local"),
                    "base_url": os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8000/v1"),
                },
                model_id=os.getenv(
                    "LOCAL_LLM_MODEL",
                    "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
                ),
                params={"tool_choice": "none"},
            )
            agent = Agent(
                model=model,
                tools=[evidence_marker],
                system_prompt=(
                    "You are InnerOS Personal Brain. Use memory and live-web evidence. "
                    "Be concise and distinguish remembered facts from live findings. "
                    "Historical memories can describe older execution failures; treat those only as historical. "
                    "Do not predict or describe the outcome of the current action because execution happens "
                    "after reasoning and the verified executor result will be appended separately."
                ),
            )
            result = agent(
                f"USER REQUEST:\n{prompt}\n\n"
                "CURRENT EXECUTION HAS NOT RUN YET. Discuss the opportunity and reasoning only. "
                "Do not state that the current action succeeded or failed.\n\n"
                f"EVIDENCE:\n{context}"
            )
            return str(result)
        except Exception as exc:
            if context:
                return (
                    "I combined available personal memory and live context. "
                    f"For this request, the strongest evidence I found was:\n{context[:1800]}\n\n"
                    f"[Strands fallback: {type(exc).__name__}]"
                )
            return (
                "I do not have enough evidence yet. Add memory or enable live web search. "
                f"[Strands fallback: {type(exc).__name__}]"
            )

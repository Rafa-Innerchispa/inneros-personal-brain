from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from typing import Awaitable, Callable

from app.models import BrainResponse, Evidence
from app.cognee_agent_tools import CogneeAgentMemoryTools
from app.sandbox import DockerSandboxExecutor


EventEmitter = Callable[[dict], Awaitable[None] | None]


@dataclass
class PersonalBrain:
    memory: object
    web: object

    async def _emit(self, emitter: EventEmitter | None, event: dict) -> None:
        if emitter is None:
            return
        result = emitter(event)
        if inspect.isawaitable(result):
            await result

    async def answer(
        self,
        prompt: str,
        act: bool = False,
        emit: EventEmitter | None = None,
    ) -> BrainResponse:
        trace = ["remember:query-memory"]
        await self._emit(emit, {
            "stage": "remember",
            "technology": "cognee",
            "state": "active",
            "message": "Recalling persistent memory from Cognee",
        })
        memory_hits: list[Evidence] = await self.memory.search(prompt)
        await self._emit(emit, {
            "stage": "remember",
            "technology": "cognee",
            "state": "complete",
            "message": f"Recovered {len(memory_hits)} relevant memory items",
            "count": len(memory_hits),
        })

        trace.append("discover:query-live-web")
        await self._emit(emit, {
            "stage": "observe",
            "technology": "brightdata",
            "state": "active",
            "message": "Searching the live web with Bright Data",
        })
        web_hits: list[Evidence] = await self.web.search(prompt)
        replay = any(bool(x.metadata.get("verified_replay")) for x in web_hits)
        await self._emit(emit, {
            "stage": "observe",
            "technology": "brightdata",
            "state": "complete",
            "message": (
                f"Loaded {len(web_hits)} verified replay results"
                if replay
                else f"Found {len(web_hits)} live web results"
            ),
            "count": len(web_hits),
            "mode": "verified-replay" if replay else "live",
        })

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
                x
                for x in memory_hits
                if not any(term in x.summary.lower() for term in historical_failure_terms)
            ]

        context = "\n".join(
            [f"MEMORY: {x.summary}" for x in reason_memory_hits]
            + [f"WEB: {x.summary}" for x in web_hits]
        )

        await self._emit(emit, {
            "stage": "reason",
            "technology": "strands",
            "state": "active",
            "message": "AWS Strands is orchestrating the reasoning path",
        })
        await self._emit(emit, {
            "stage": "reason",
            "technology": "local_model",
            "state": "active",
            "message": "Local Qwen/vLLM is synthesizing the answer",
        })
        reasoned = await self._reason(prompt, context)
        if isinstance(reasoned, tuple):
            answer, agent_memory_usage = reasoned
        else:
            answer, agent_memory_usage = reasoned, {}
        if agent_memory_usage.get("direct_agent_tools"):
            await self._emit(emit, {
                "stage": "remember",
                "technology": "cognee",
                "state": "complete",
                "message": (
                    "Cognee is attached directly to the Strands agent "
                    f"(recall calls: {agent_memory_usage.get('recall_calls', 0)}, "
                    f"remember calls: {agent_memory_usage.get('remember_calls', 0)})"
                ),
                "agent_memory": agent_memory_usage,
            })
        await self._emit(emit, {
            "stage": "reason",
            "technology": "local_model",
            "state": "complete",
            "message": "Local inference complete",
        })
        await self._emit(emit, {
            "stage": "reason",
            "technology": "strands",
            "state": "complete",
            "message": "Reasoning plan complete",
        })

        actions: list[dict] = []
        if act:
            trace.append("act:docker-sandbox")
            await self._emit(emit, {
                "stage": "act",
                "technology": "docker",
                "state": "active",
                "message": "Executing a bounded action in Docker Sandbox",
            })
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
                await self._emit(emit, {
                    "stage": "act",
                    "technology": "docker",
                    "state": "complete",
                    "message": f"Artifact executed: {sandbox_result.get('artifact', 'created')}",
                })
            else:
                answer += (
                    "\n\nEXECUTION EVIDENCE: The current Docker action did not complete. "
                    f"Status: {sandbox_result.get('status', 'unknown')}."
                )
                await self._emit(emit, {
                    "stage": "act",
                    "technology": "docker",
                    "state": "error",
                    "message": f"Action status: {sandbox_result.get('status', 'unknown')}",
                })

        trace.append("verify:record-evidence")
        await self._emit(emit, {
            "stage": "learn",
            "technology": "cognee",
            "state": "active",
            "message": "Writing the verified outcome back to persistent memory",
        })
        await self.memory.remember(
            f"Personal Brain handled: {prompt}\nResult: {answer[:500]}",
            {"trace": trace, "actions": actions},
        )
        trace.append("remember:store-outcome")
        await self._emit(emit, {
            "stage": "learn",
            "technology": "cognee",
            "state": "complete",
            "message": "Outcome stored in Cognee",
        })

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

            cognee_agent_memory = CogneeAgentMemoryTools()
            memory_tools = cognee_agent_memory.build()

            model = OpenAIModel(
                client_args={
                    "api_key": os.getenv("LOCAL_LLM_API_KEY", "local"),
                    "base_url": os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8000/v1"),
                },
                model_id=os.getenv(
                    "LOCAL_LLM_MODEL",
                    "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
                ),
            )
            agent = Agent(
                model=model,
                tools=[evidence_marker, *memory_tools],
                system_prompt=(
                    "You are InnerOS Personal Brain. Cognee is your durable shared memory. "
                    "When Cognee tools are available, call cognee_recall before answering any question "
                    "about prior projects, decisions, preferences, architecture, or earlier outcomes. "
                    "Use cognee_remember only for durable verified facts, explicit remember requests, "
                    "or verified outcomes; never store credentials or raw untrusted web text. "
                    "Use the supplied memory and live-web evidence too. Be concise and distinguish "
                    "remembered facts from live findings. Historical memories can describe older "
                    "execution failures; treat those only as historical. Do not predict or describe "
                    "the outcome of the current action because execution happens after reasoning and "
                    "the verified executor result will be appended separately."
                ),
            )
            result = agent(
                f"USER REQUEST:\n{prompt}\n\n"
                "CURRENT EXECUTION HAS NOT RUN YET. Discuss the opportunity and reasoning only. "
                "Do not state that the current action succeeded or failed.\n\n"
                f"EVIDENCE:\n{context}"
            )
            return str(result), cognee_agent_memory.usage()
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

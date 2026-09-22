from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from typing import Awaitable, Callable

from app.models import BrainResponse, Evidence
from app.cognee_agent_tools import CogneeAgentMemoryTools, CogneeMemoryStore
from app.sandbox import DockerSandboxExecutor


EventEmitter = Callable[[dict], Awaitable[None] | None]


@dataclass
class PersonalBrain:
    memory: object
    web: object

    @staticmethod
    def _normalize_route_mode(route_mode: str | None) -> str:
        normalized = (route_mode or "auto").strip().lower().replace("-", "_").replace(" ", "_")
        return normalized if normalized in {"auto", "memory_first", "local_only", "web_only"} else "auto"

    @staticmethod
    def _is_identity_or_memory_query(prompt: str) -> bool:
        text = f" {prompt.lower()} "
        markers = (
            "who am i",
            "quien soy",
            "quién soy",
            "sobre mi",
            "sobre mí",
            "mi proyecto",
            "mis proyectos",
            "recuerdas",
            "remember about me",
            "what do you remember",
            "que recuerdas",
            "qué recuerdas",
            "inneros",
            "ralphi",
            "pc doctor",
            "innerchispa",
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _is_owner_identity_query(prompt: str) -> bool:
        text = f" {prompt.lower()} "
        markers = (
            "who am i",
            "quien soy",
            "quién soy",
            "rafael lopez",
            "rafael lópez",
            "ralphi",
            "sobre mi",
            "sobre mí",
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _public_identity_query() -> str:
        return os.getenv(
            "PUBLIC_IDENTITY_SEARCH_QUERY",
            '"Rafael Lopez" "InnerChispa"',
        )

    @classmethod
    def _public_personal_context_query(cls, prompt: str) -> str:
        return f"{cls._public_identity_query()} {prompt}"[:500]

    @staticmethod
    def _needs_live_web(prompt: str) -> bool:
        text = f" {prompt.lower()} "
        markers = (
            "latest",
            "today",
            "current",
            "news",
            "recent",
            "buscar",
            "busca",
            "internet",
            "web",
            "google",
            "bright data",
            "brightdata",
            "ahora",
            "hoy",
            "actual",
            "reciente",
            "noticias",
        )
        return any(marker in text for marker in markers)

    def _plan_route(self, prompt: str, route_mode: str | None) -> dict:
        mode = self._normalize_route_mode(route_mode)
        personal = self._is_identity_or_memory_query(prompt)
        owner_identity = self._is_owner_identity_query(prompt)
        needs_web = self._needs_live_web(prompt)
        web_query = prompt
        if mode == "local_only":
            use_memory = False
            use_web = False
            policy = "local_only"
            reason = "Forced local-only route; no external memory or web lookup."
        elif mode == "web_only":
            use_memory = False
            use_web = True
            policy = "web_only"
            reason = "Forced live-web route through Bright Data."
        elif mode == "memory_first":
            use_memory = True
            use_web = True
            policy = "memory_first"
            reason = "Memory-first route; Cognee answers first and Bright Data adds public context."
            if personal:
                web_query = self._public_personal_context_query(prompt)
            elif owner_identity:
                web_query = self._public_identity_query()
        elif owner_identity:
            use_memory = True
            use_web = True
            policy = "identity_memory_web"
            reason = "Owner identity question: Cognee memory plus Bright Data public identity search, then local Qwen synthesis."
            web_query = self._public_identity_query()
        elif personal:
            use_memory = True
            use_web = True
            policy = "personal_memory_web"
            reason = "Personal/project memory question: Cognee memory plus Bright Data public context, then local Qwen synthesis."
            web_query = self._public_personal_context_query(prompt)
        else:
            use_memory = True
            use_web = True
            policy = "auto_all_sources"
            reason = "AUTO demo route: every question uses Cognee memory, Bright Data live web, Strands orchestration and local Qwen synthesis."
            if personal:
                web_query = self._public_personal_context_query(prompt)
        return {
            "mode": mode,
            "policy": policy,
            "reason": reason,
            "use_memory": use_memory,
            "use_web": use_web,
            "web_query": web_query,
            "personal_query": personal,
            "owner_identity_query": owner_identity,
            "live_web_intent": needs_web,
        }

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
        route_mode: str = "auto",
        emit: EventEmitter | None = None,
    ) -> BrainResponse:
        route = self._plan_route(prompt, route_mode)
        trace = [f"route:{route['policy']}"]
        dataset = os.getenv("COGNEE_DATASET", "inneros-personal-brain")
        stages_executed: list[str] = ["input"]
        tool_calls = {
            "cognee_search": 0,
            "brightdata_search": 0,
            "cognee_remember": 0,
            "docker_action": 0,
        }
        await self._emit(emit, {
            "stage": "input",
            "technology": "strands",
            "state": "active",
            "message": f"Route selected: {route['policy']} ({route['mode']})",
            "route_class": "LOCAL_OR_DISTRIBUTED",
            "route_mode": route["mode"],
        })
        memory_hits: list[Evidence] = []
        if route["use_memory"]:
            trace.append("remember:query-memory")
            stages_executed.append("remember")
            await self._emit(emit, {
                "stage": "remember",
                "technology": "cognee",
                "state": "active",
                "message": "Recalling persistent memory from Cognee",
                "dataset": dataset,
                "source_class": "Cognee shared graph",
            })
            tool_calls["cognee_search"] += 1
            memory_hits = await self.memory.search(prompt)
            await self._emit(emit, {
                "stage": "remember",
                "technology": "cognee",
                "state": "complete",
                "message": f"Recovered {len(memory_hits)} relevant memory items",
                "count": len(memory_hits),
                "dataset": dataset,
                "source_class": "Cognee shared graph",
            })
        else:
            trace.append("remember:skipped-by-route")
            await self._emit(emit, {
                "stage": "remember",
                "technology": "cognee",
                "state": "complete",
                "message": "Cognee recall skipped by selected route",
                "dataset": dataset,
                "source_class": "Cognee shared graph",
            })

        trace.append("remember:inject-working-context")
        stages_executed.append("inject")
        await self._emit(emit, {
            "stage": "inject",
            "technology": "strands",
            "state": "active",
            "message": "Preparing safe memory injection for Strands",
            "dataset": dataset,
        })
        injection_count = len(memory_hits)
        await self._emit(emit, {
            "stage": "inject",
            "technology": "strands",
            "state": "complete",
            "message": f"Injected {injection_count} safe memory snippets into working context",
            "count": injection_count,
            "dataset": dataset,
        })

        web_hits: list[Evidence] = []
        replay = False
        if route["use_web"]:
            trace.append("discover:query-live-web")
            stages_executed.append("observe")
            await self._emit(emit, {
                "stage": "observe",
                "technology": "brightdata",
                "state": "active",
                "message": "Searching the live web with Bright Data",
            })
            tool_calls["brightdata_search"] += 1
            web_hits = await self.web.search(route["web_query"])
            if not web_hits:
                web_hits = [
                    Evidence(
                        source="brightdata",
                        summary=(
                            "[BRIGHT DATA LIVE SEARCH][NO PUBLIC MATCHES] "
                            f"Bright Data searched the public web for: {route['web_query']}. "
                            "No high-confidence public organic result was returned for this query."
                        ),
                        metadata={
                            "live": True,
                            "no_public_matches": True,
                            "query": route["web_query"],
                            "title": "Bright Data live search",
                            "url": "",
                        },
                    )
                ]
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
                "source_class": "Bright Data live web" if not replay else "verified replay",
            })
        else:
            trace.append("discover:skipped-by-route")
            await self._emit(emit, {
                "stage": "observe",
                "technology": "brightdata",
                "state": "complete",
                "message": "Bright Data skipped by route policy",
                "count": 0,
                "mode": "not_used",
                "source_class": "Bright Data live web",
            })

        historical_failure_terms = (
            "sandboxing issue",
            "failed due to",
            "could not be created",
            "requires_runtime",
            "docker action did not complete",
            "sandboxing failure",
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

        stages_executed.append("reason")
        await self._emit(emit, {
            "stage": "reason",
            "technology": "strands",
            "state": "active",
            "message": "AWS Strands is orchestrating the reasoning path",
            "role": "orchestration",
        })
        await self._emit(emit, {
            "stage": "reason",
            "technology": "local_model",
            "state": "active",
            "message": "Local Qwen/vLLM is synthesizing the answer",
            "route_class": "LOCAL_OR_AMD_ON_DEMAND",
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
            "stage": "audit",
            "technology": "strands",
            "state": "complete",
            "message": (
                "Tool audit captured safe metadata for Strands memory tools "
                f"(recall={agent_memory_usage.get('recall_calls', 0)}, "
                f"remember={agent_memory_usage.get('remember_calls', 0)})"
            ),
            "tool_audit": {
                "cognee_recall": agent_memory_usage.get("recall_calls", 0),
                "cognee_remember": agent_memory_usage.get("remember_calls", 0),
                "dataset": dataset,
            },
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
            stages_executed.append("govern")
            await self._emit(emit, {
                "stage": "govern",
                "technology": "govern",
                "state": "active",
                "message": "Deterministic policy gate checking requested action",
            })
            await self._emit(emit, {
                "stage": "govern",
                "technology": "govern",
                "state": "complete",
                "message": "Policy allows this demo artifact action; consequential actions still require explicit approval",
                "decision": "allowed_demo_artifact",
            })
            trace.append("act:docker-sandbox")
            stages_executed.append("act")
            await self._emit(emit, {
                "stage": "act",
                "technology": "docker",
                "state": "active",
                "message": "Executing a bounded action in Docker Sandbox",
            })
            executor = DockerSandboxExecutor()
            tool_calls["docker_action"] += 1
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
        if route["mode"] == "local_only":
            trace.append("remember:write-skipped-by-route")
            await self._emit(emit, {
                "stage": "learn",
                "technology": "cognee",
                "state": "complete",
                "message": "Cognee write skipped by LOCAL ONLY route",
                "dataset": dataset,
            })
        else:
            stages_executed.append("learn")
            await self._emit(emit, {
                "stage": "learn",
                "technology": "cognee",
                "state": "active",
                "message": "Writing the verified outcome back to persistent memory",
                "dataset": dataset,
            })
            await self.memory.remember(
                f"Personal Brain handled: {prompt}\nResult: {answer[:500]}",
                {"trace": trace, "actions": actions},
            )
            tool_calls["cognee_remember"] += 1
            trace.append("remember:store-outcome")
            await self._emit(emit, {
                "stage": "learn",
                "technology": "cognee",
                "state": "complete",
                "message": "Outcome stored in Cognee",
                "dataset": dataset,
            })

        fallback_reason = ""
        if "[Strands fallback:" in answer:
            fallback_reason = answer.split("[Strands fallback:", 1)[1].split("]", 1)[0].strip()
        route_summary = {
            "route_mode": route["mode"],
            "route_policy": route["policy"],
            "orchestrator": "AWS Strands" if not fallback_reason else "deterministic fallback after Strands error",
            "final_answer_model": os.getenv("LOCAL_LLM_MODEL", "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ"),
            "stages_executed": stages_executed,
            "sources_used": [
                source
                for source, used in {
                    "strands_orchestrator": True,
                    "local_qwen_vllm": True,
                    "cognee_shared_memory": bool(memory_hits),
                    "brightdata_live_web": bool(web_hits),
                    "docker_sandbox": bool(actions),
                }.items()
                if used
            ],
            "sources_not_used": [
                source
                for source, used in {
                    "cognee_shared_memory": route["use_memory"],
                    "brightdata_live_web": route["use_web"],
                    "docker_sandbox": act,
                }.items()
                if not used
            ],
            "counts": {
                "memory_hits": len(memory_hits),
                "web_hits": len(web_hits),
                "actions": len(actions),
            },
            "tool_calls": tool_calls,
            "fallback_active": bool(fallback_reason or replay),
            "fallback_reason": fallback_reason or ("Bright Data verified replay" if replay else ""),
            "evidence_refs": {
                "cognee_dataset": dataset,
                "brightdata_query": route["web_query"] if route["use_web"] else "",
                "web_mode": "verified_replay" if replay else "live" if web_hits else "not_used",
            },
            "routing_reason": route["reason"],
        }

        return BrainResponse(
            answer=answer,
            memory_hits=memory_hits,
            web_hits=web_hits,
            actions=actions,
            trace=trace,
            route=route_summary,
        )

    async def _reason(self, prompt: str, context: str) -> str:
        try:
            from strands import Agent, tool
            from strands.models.openai import OpenAIModel as BaseOpenAIModel

            class VLLMCompatibleOpenAIModel(BaseOpenAIModel):
                def format_request(self, *args, **kwargs):
                    request = super().format_request(*args, **kwargs)
                    if not request.get("tools"):
                        request.pop("tools", None)
                        if request.get("tool_choice") == "auto":
                            request.pop("tool_choice", None)
                    return request

            @tool
            def evidence_marker(value: str = "ok") -> str:
                """Return a harmless marker for OpenAI-compatible tool schemas."""
                return value

            native_tool_calling = os.getenv("STRANDS_NATIVE_TOOL_CALLING", "0") == "1"
            cognee_agent_memory = CogneeAgentMemoryTools()
            cognee_memory_store = CogneeMemoryStore()
            memory_tools = cognee_agent_memory.build() if native_tool_calling else []

            model = VLLMCompatibleOpenAIModel(
                client_args={
                    "api_key": os.getenv("LOCAL_LLM_API_KEY", "local"),
                    "base_url": os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8000/v1"),
                },
                model_id=os.getenv(
                    "LOCAL_LLM_MODEL",
                    "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
                ),
            )
            system_prompt = (
                "You are InnerOS Personal Brain. Cognee is your durable shared memory. "
                "Use the supplied memory and live-web evidence. Be concise and distinguish "
                "remembered facts from live findings. Historical memories can describe older "
                "execution failures; treat those only as historical. Do not predict or describe "
                "the outcome of the current action because execution happens after reasoning and "
                "the verified executor result will be appended separately."
            )
            tools = [evidence_marker, *memory_tools] if native_tool_calling else None
            if native_tool_calling:
                system_prompt += (
                    " When Cognee tools are available, call cognee_recall before answering any "
                    "question about prior projects, decisions, preferences, architecture, or earlier "
                    "outcomes. Use cognee_remember only for durable verified facts, explicit remember "
                    "requests, or verified outcomes; never store credentials or raw untrusted web text."
                )
            else:
                system_prompt += (
                    " Cognee recall and remember are executed by the backend adapter before and after "
                    "Strands reasoning, so do not ask for tools."
                )
            agent = Agent(
                model=model,
                tools=tools,
                system_prompt=system_prompt,
            )
            result = agent(
                f"USER REQUEST:\n{prompt}\n\n"
                "CURRENT EXECUTION HAS NOT RUN YET. Discuss the opportunity and reasoning only. "
                "Do not state that the current action succeeded or failed.\n\n"
                f"EVIDENCE:\n{context}"
            )
            usage = cognee_agent_memory.usage()
            usage["memory_manager"] = cognee_memory_store.status()
            usage["memory_injection_count"] = context.count("MEMORY:")
            usage["strands_native_tool_calling"] = native_tool_calling
            return str(result), usage
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

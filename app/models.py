from __future__ import annotations

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str
    summary: str
    metadata: dict = Field(default_factory=dict)


class BrainRequest(BaseModel):
    prompt: str
    act: bool = False


class BrainResponse(BaseModel):
    answer: str
    memory_hits: list[Evidence] = Field(default_factory=list)
    web_hits: list[Evidence] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)

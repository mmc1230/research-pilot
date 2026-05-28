from typing import Any, TypedDict


class AgentState(TypedDict):
    question: str
    source_type: str
    source_id: str
    session_id: str
    intent: str
    collection_name: str
    retrieved_chunks: list[dict[str, Any]]
    tool_requests: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]
    warnings: list[str]
    logs: list[dict[str, Any]]

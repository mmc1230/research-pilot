from app.agents.graph import build_graph
from app.storage import sqlite


def run_chat(question: str, source_type: str, source_id: str | None = None, session_id: str | None = None) -> dict:
    graph = build_graph()
    initial_state = {
        "question": question,
        "source_type": source_type,
        "source_id": str(source_id or ""),
        "session_id": session_id or "",
        "intent": "",
        "collection_name": "",
        "retrieved_chunks": [],
        "tool_requests": [],
        "tool_results": [],
        "answer": "",
        "citations": [],
        "warnings": [],
        "logs": [],
    }
    result = graph.invoke(initial_state)
    sqlite.add_message(result["session_id"], "user", question)
    sqlite.add_message(result["session_id"], "assistant", result["answer"])
    return result

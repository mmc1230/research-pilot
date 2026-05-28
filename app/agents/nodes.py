import json
from uuid import uuid4

from app.agents.state import AgentState
from app.config import get_settings
from app.storage import sqlite
from app.tools import code_tools, csv_tools, file_tools, search_tools  # noqa: F401
from app.tools.tool_registry import registry


def _summarize(value, limit: int = 500) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str)
    return text[:limit]


def _log(state: AgentState, event: str, payload: dict) -> None:
    state["logs"].append({"event": event, "payload": payload})


def input_node(state: AgentState) -> AgentState:
    if not state.get("session_id"):
        state["session_id"] = uuid4().hex
    sqlite.create_session(state["session_id"], state.get("source_type", ""), state.get("source_id", ""))
    _log(state, "input", {"question": state["question"], "source_type": state["source_type"]})
    return state


def intent_router_node(state: AgentState) -> AgentState:
    source_type = state.get("source_type", "").lower()
    if source_type == "paper":
        intent = "paper_reading"
    elif source_type in {"project", "code"}:
        intent = "code_understanding"
    elif source_type == "csv":
        intent = "experiment_analysis"
    else:
        q = state["question"].lower()
        if any(word in q for word in ["rmse", "r2", "csv", "metric", "model"]):
            intent = "experiment_analysis"
        elif any(word in q for word in ["function", "class", "module", "code", "file"]):
            intent = "code_understanding"
        elif any(word in q for word in ["paper", "method", "abstract", "experiment"]):
            intent = "paper_reading"
        else:
            intent = "general_research_question"
    state["intent"] = intent
    _log(state, "intent_router", {"intent": intent})
    return state


def retrieval_node(state: AgentState) -> AgentState:
    source_id = state.get("source_id")
    if source_id:
        doc = sqlite.get_document(source_id)
        if doc:
            state["collection_name"] = doc["collection_name"]
    if state.get("collection_name") and state["intent"] in {"paper_reading", "code_understanding"}:
        result = registry.call(
            "search_vector_store",
            query=state["question"],
            collection_name=state["collection_name"],
            k=5,
        )
        state["retrieved_chunks"] = result["chunks"]
        sqlite.add_tool_call(
            state["session_id"],
            "search_vector_store",
            {"query": state["question"], "collection_name": state["collection_name"], "k": 5},
            _summarize(result),
        )
        _log(state, "retrieval", {"chunk_count": len(result["chunks"])})
    return state


def tool_router_node(state: AgentState) -> AgentState:
    requests = []
    source_id = state.get("source_id")
    doc = sqlite.get_document(source_id) if source_id else None
    if state["intent"] == "experiment_analysis" and doc:
        requests.append({"tool_name": "analyze_metrics_csv", "args": {"csv_path": doc["file_path"]}})
    elif state["intent"] == "code_understanding" and doc and doc["doc_type"] == "project":
        requests.append({"tool_name": "get_document_metadata", "args": {"document_id": doc["id"]}})
    elif doc:
        requests.append({"tool_name": "get_document_metadata", "args": {"document_id": doc["id"]}})
    state["tool_requests"] = requests
    _log(state, "tool_router", {"requests": requests})
    return state


def tool_execution_node(state: AgentState) -> AgentState:
    results = []
    for request in state.get("tool_requests", []):
        name = request["tool_name"]
        args = request.get("args", {})
        try:
            result = registry.call(name, **args)
            results.append({"tool_name": name, "args": args, "result": result})
            sqlite.add_tool_call(state["session_id"], name, args, _summarize(result))
        except Exception as exc:
            err = {"error": str(exc)}
            results.append({"tool_name": name, "args": args, "result": err})
            sqlite.add_tool_call(state["session_id"], name, args, _summarize(err))
    state["tool_results"] = results
    _log(state, "tool_execution", {"count": len(results)})
    return state


def _context_from_chunks(chunks: list[dict]) -> str:
    parts = []
    for idx, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        label = f"[Chunk {idx} source={meta.get('filename') or chunk.get('source')} page={meta.get('page')}]"
        parts.append(f"{label}\n{chunk.get('content', '')[:1200]}")
    return "\n\n".join(parts)


def _llm_answer(question: str, context: str, tool_results: list[dict], intent: str) -> str | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0.1)
        prompt = (
            "You are ResearchPilot, a rigorous research assistant. Answer with clear structure, "
            "grounding claims in evidence. If evidence is insufficient, say so.\n\n"
            f"Intent: {intent}\nQuestion: {question}\n\nEvidence:\n{context}\n\n"
            f"Tool results:\n{json.dumps(tool_results, ensure_ascii=False, default=str)[:6000]}"
        )
        return llm.invoke(prompt).content
    except Exception as exc:
        return f"LLM call failed, using available evidence only. Error: {exc}"


def _fallback_answer(state: AgentState, context: str) -> str:
    question = state["question"]
    chunks = state.get("retrieved_chunks", [])
    tool_results = state.get("tool_results", [])
    if state["intent"] == "experiment_analysis" and tool_results:
        analysis = tool_results[0]["result"]
        best = analysis.get("best_by_metric", {})
        lines = ["## Experiment Analysis", f"Question: {question}", ""]
        lines.append(f"Detected metrics: {', '.join(analysis.get('metric_columns', [])) or 'none'}")
        for metric, item in best.items():
            row_label = item["row"].get("model") or item["row"].get("method") or item["best_index"]
            lines.append(f"- {metric}: best is `{row_label}` with value `{item['best_value']}` ({item['direction']} is better).")
        if analysis.get("anomalies"):
            lines.append(f"- Potential anomalies detected: {len(analysis['anomalies'])}.")
        return "\n".join(lines)
    if state["intent"] == "code_understanding":
        lines = ["## Code Understanding", f"Question: {question}", ""]
        if chunks:
            lines.append("Relevant code evidence:")
            for idx, chunk in enumerate(chunks[:5], start=1):
                meta = chunk.get("metadata", {})
                lines.append(f"- Chunk {idx}: `{meta.get('source')}`")
        if tool_results:
            lines.append("")
            lines.append(f"Tool evidence: `{tool_results[0]['tool_name']}` returned metadata for the selected project.")
        lines.append("Use the cited files above as the starting point for deeper inspection.")
        return "\n".join(lines)
    if chunks:
        lines = ["## Paper Answer", f"Question: {question}", ""]
        lines.append("The most relevant evidence is:")
        for idx, chunk in enumerate(chunks[:4], start=1):
            snippet = " ".join(chunk.get("content", "").split())[:500]
            lines.append(f"- Chunk {idx}: {snippet}")
        lines.append("")
        lines.append("A full LLM synthesis requires `OPENAI_API_KEY`; current answer is evidence extraction only.")
        return "\n".join(lines)
    return "I do not have enough retrieved evidence or tool output to answer this rigorously."


def answer_generation_node(state: AgentState) -> AgentState:
    context = _context_from_chunks(state.get("retrieved_chunks", []))
    llm_answer = _llm_answer(state["question"], context, state.get("tool_results", []), state["intent"])
    state["answer"] = llm_answer or _fallback_answer(state, context)
    state["citations"] = [
        {
            "index": idx,
            "source": chunk.get("source"),
            "page": chunk.get("page"),
            "section": chunk.get("section"),
            "snippet": " ".join(chunk.get("content", "").split())[:300],
        }
        for idx, chunk in enumerate(state.get("retrieved_chunks", []), start=1)
    ]
    _log(state, "answer_generation", {"answer_chars": len(state["answer"])})
    return state


def verification_node(state: AgentState) -> AgentState:
    has_evidence = bool(state.get("retrieved_chunks") or state.get("tool_results"))
    if not has_evidence:
        state["warnings"].append("No retrieved chunks or tool results were available; answer may be incomplete.")
    elif "requires `OPENAI_API_KEY`" in state["answer"]:
        state["warnings"].append("Offline fallback mode used; set OPENAI_API_KEY for synthesized research answers.")
    _log(state, "verification", {"warnings": state["warnings"]})
    return state


def output_node(state: AgentState) -> AgentState:
    _log(state, "output", {"citations": len(state.get("citations", []))})
    return state

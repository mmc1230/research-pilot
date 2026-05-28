from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    answer_generation_node,
    input_node,
    intent_router_node,
    output_node,
    retrieval_node,
    tool_execution_node,
    tool_router_node,
    verification_node,
)
from app.agents.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("input_node", input_node)
    graph.add_node("intent_router_node", intent_router_node)
    graph.add_node("retrieval_node", retrieval_node)
    graph.add_node("tool_router_node", tool_router_node)
    graph.add_node("tool_execution_node", tool_execution_node)
    graph.add_node("answer_generation_node", answer_generation_node)
    graph.add_node("verification_node", verification_node)
    graph.add_node("output_node", output_node)

    graph.set_entry_point("input_node")
    graph.add_edge("input_node", "intent_router_node")
    graph.add_edge("intent_router_node", "retrieval_node")
    graph.add_edge("retrieval_node", "tool_router_node")
    graph.add_edge("tool_router_node", "tool_execution_node")
    graph.add_edge("tool_execution_node", "answer_generation_node")
    graph.add_edge("answer_generation_node", "verification_node")
    graph.add_edge("verification_node", "output_node")
    graph.add_edge("output_node", END)
    return graph.compile()

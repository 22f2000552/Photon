"""LangGraph orchestration.

Two graphs because procurement is asynchronous in real life:

  sourcing_graph  : scout -> outreach          (runs when an RFQ is launched)
  analysis_graph  : collect -> analyze          (runs once replies are in)

Each node opens its own DB session, does its work through the agent
modules, and passes lightweight state (ids + summaries) forward.
"""
from typing import TypedDict

from langgraph.graph import END, StateGraph

from ..database import SessionLocal
from ..models import RFQ
from .analyst import run_analyst
from .outreach import run_outreach
from .scout import run_scout


class RFQState(TypedDict, total=False):
    rfq_id: int
    scout_count: int
    outreach_count: int
    quote_count: int
    shortlist: list
    explanation: str


def _scout_node(state: RFQState) -> RFQState:
    with SessionLocal() as db:
        rfq = db.get(RFQ, state["rfq_id"])
        result = run_scout(db, rfq)
        db.commit()
        return {"scout_count": len(result)}


def _outreach_node(state: RFQState) -> RFQState:
    with SessionLocal() as db:
        rfq = db.get(RFQ, state["rfq_id"])
        sent = run_outreach(db, rfq)
        db.commit()
        return {"outreach_count": len(sent)}


def _collect_node(state: RFQState) -> RFQState:
    with SessionLocal() as db:
        rfq = db.get(RFQ, state["rfq_id"])
        return {"quote_count": len(rfq.quotes)}


def _analyze_node(state: RFQState) -> RFQState:
    with SessionLocal() as db:
        rfq = db.get(RFQ, state["rfq_id"])
        result = run_analyst(db, rfq)
        db.commit()
        return {"shortlist": result["shortlist"], "explanation": result["explanation"]}


def _build_sourcing_graph():
    graph = StateGraph(RFQState)
    graph.add_node("scout", _scout_node)
    graph.add_node("outreach", _outreach_node)
    graph.set_entry_point("scout")
    graph.add_edge("scout", "outreach")
    graph.add_edge("outreach", END)
    return graph.compile()


def _build_analysis_graph():
    graph = StateGraph(RFQState)
    graph.add_node("collect", _collect_node)
    graph.add_node("analyze", _analyze_node)
    graph.set_entry_point("collect")
    graph.add_conditional_edges(
        "collect",
        lambda s: "analyze" if s.get("quote_count", 0) > 0 else END,
        {"analyze": "analyze", END: END},
    )
    graph.add_edge("analyze", END)
    return graph.compile()


sourcing_graph = _build_sourcing_graph()
analysis_graph = _build_analysis_graph()


def launch_rfq(rfq_id: int) -> RFQState:
    return sourcing_graph.invoke({"rfq_id": rfq_id})


def analyze_rfq(rfq_id: int) -> RFQState:
    return analysis_graph.invoke({"rfq_id": rfq_id})

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from langgraph.graph import END, START, StateGraph

from src_api.state import HouseholdProfileState
from src_api.agents.calculate_grid_draw_and_expense_api import APICalculateGridDrawAndExpenseAgent
from src_api.agents.compare_against_similar_households_api import APICompareAgainstSimilarHouseholdsAgent
from src_api.agents.energy_recommendations_api import APIEnergyRecommendationsAgent
from src_api.agents.solar_roi_analysis_api import APISolarROIAnalysisAgent

router = APIRouter(prefix="/api", tags=["household-energy"])


def build_api_graph(node_mapping: Dict[str, Any], start_node: str, edges: Optional[list[tuple[str, str]]] = None):
    graph = StateGraph(HouseholdProfileState)
    for node_name, processor in node_mapping.items():
        graph.add_node(node_name, processor)

    graph.add_edge(START, start_node)
    if edges:
        for source, target in edges:
            graph.add_edge(source, target)

    return graph.compile()


def make_initial_state(profile_data: Dict[str, Any], renewable_assets: Optional[Dict[str, Any]] = None) -> HouseholdProfileState:
    return {
        "profile_data": {**profile_data},
        "occupancy_data": {},
        "appliance_data": {**profile_data},
        "building_envelope": {},
        "renewable_assets": dict(renewable_assets or {}),
        "energy_metrics": {},
        "comparison_summary": {},
        "solar_roi": {},
        "recommendations": {},
        "messages": [],
        "errors": [],
        "current_agent": None,
        "workflow_stage": "Start",
    }


def invoke_graph(graph, initial_state: HouseholdProfileState) -> Dict[str, Any]:
    try:
        return graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _wrap_agent_processor(agent: Any):
    def processor(state: HouseholdProfileState) -> Any:
        return agent.process(state)

    return processor


@router.post("/grid-draw")
def calculate_grid_draw(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile_data = payload.get("profile_data", {})
    renewable_assets = payload.get("renewable_assets", {})
    tariff = payload.get("electricity_tariff_per_kWh") or profile_data.get("electricity_tariff_per_kWh")

    if tariff is None:
        raise HTTPException(status_code=400, detail="Missing electricity_tariff_per_kWh in request payload.")

    initial_state = make_initial_state(profile_data, renewable_assets)
    agent_a = APICalculateGridDrawAndExpenseAgent(tariff=tariff, next_node="compare_against_similar_households")
    agent_b = APICompareAgainstSimilarHouseholdsAgent()

    graph = build_api_graph(
        {
            "calculate_grid_draw_and_expense": _wrap_agent_processor(agent_a),
            "compare_against_similar_households": _wrap_agent_processor(agent_b),
        },
        start_node="calculate_grid_draw_and_expense",
        edges=[("calculate_grid_draw_and_expense", "compare_against_similar_households")],
    )

    return invoke_graph(graph, initial_state)


@router.post("/solar-roi")
def solar_roi_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile_data = payload.get("profile_data", {})
    renewable_assets = payload.get("renewable_assets", {})

    initial_state = make_initial_state(profile_data, renewable_assets)
    agent = APISolarROIAnalysisAgent(next_node=END)

    graph = build_api_graph(
        {"solar_roi_analysis": _wrap_agent_processor(agent)},
        start_node="solar_roi_analysis",
    )

    return invoke_graph(graph, initial_state)


@router.post("/recommendations")
def energy_recommendations(payload: Dict[str, Any]) -> Dict[str, Any]:
    print("----------------------------------------------------------------------------------------")
    profile_data = payload.get("profile_data", {})
    renewable_assets = payload.get("renewable_assets", {})
    tariff = payload.get("electricity_tariff_per_kWh") or profile_data.get("electricity_tariff_per_kWh")

    if tariff is None:
        raise HTTPException(status_code=400, detail="Missing electricity_tariff_per_kWh in request payload.")

    initial_state = make_initial_state(profile_data, renewable_assets)
    agent_a = APICalculateGridDrawAndExpenseAgent(tariff=tariff, next_node="compare_against_similar_households")
    agent_b = APICompareAgainstSimilarHouseholdsAgent(next_node="solar_roi_analysis")
    agent_c = APISolarROIAnalysisAgent(next_node="energy_recommendations")
    agent_d = APIEnergyRecommendationsAgent()

    graph = build_api_graph(
        {
            "calculate_grid_draw_and_expense": _wrap_agent_processor(agent_a),
            "compare_against_similar_households": _wrap_agent_processor(agent_b),
            "solar_roi_analysis": _wrap_agent_processor(agent_c),
            "energy_recommendations": _wrap_agent_processor(agent_d),
        },
        start_node="calculate_grid_draw_and_expense",
        edges=[
            ("calculate_grid_draw_and_expense", "compare_against_similar_households"),
            ("compare_against_similar_households", "solar_roi_analysis"),
            ("solar_roi_analysis", "energy_recommendations"),
        ],
    )

    return invoke_graph(graph, initial_state)

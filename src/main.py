import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, Type

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START

from state import HouseholdProfileState

load_dotenv()

SRC_ROOT = Path(__file__).parent
AGENTS_DIR = SRC_ROOT / "agents"


def load_agent_class(agent_filename: str, class_name: str) -> Type[Any]:
    module_path = AGENTS_DIR / agent_filename
    if not module_path.exists():
        raise FileNotFoundError(f"Agent module not found: {module_path}")

    spec = importlib.util.spec_from_file_location(class_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {class_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


collect_household_agent = load_agent_class("collect_household_data.agent.py", "CollectHouseholdProfileAgent")()
capture_occupancy_agent = load_agent_class("capture_occupancy_details.agent.py", "CaptureOccupancyDetailsAgent")()
capture_appliances_agent = load_agent_class("capture_household_appliances.agent.py", "CaptureHouseholdAppliancesAgent")()
check_renewable_energy_assets_agent = load_agent_class("check_renewable_energy_assets.agent.py", "CheckRenewableEnergyAssetsAgent")()
assess_building_envelope_agent = load_agent_class("assess_building_envelope.agent.py", "AssessBuildingEnvelopeAgent")()
gross_energy_calculation_agent = load_agent_class("gross_energy_calculation.agent.py", "GrossEnergyCalculationAgent")()
apply_insulation_adjustments_agent = load_agent_class("apply_insulation_adjustments.agent.py", "ApplyInsulationAdjustmentsAgent")()
calculate_grid_draw_and_expense_agent = load_agent_class("calculate_grid_draw_and_expense.agent.py", "CalculateGridDrawAndExpenseAgent")()
compare_similar_households_agent = load_agent_class("compare_against_similar_households.agent.py", "CompareAgainstSimilarHouseholdsAgent")()
solar_roi_analysis_agent = load_agent_class("solar_roi_analysis.agent.py", "SolarROIAnalysisAgent")()
energy_recommendations_agent = load_agent_class("energy_recommendations.agent.py", "EnergyRecommendationsAgent")()


def build_workflow():
    workflow = StateGraph(HouseholdProfileState)
    workflow.add_node("collect_household_profile", collect_household_agent.process)
    workflow.add_node("capture_occupancy_details", capture_occupancy_agent.process)
    workflow.add_node("capture_household_appliances", capture_appliances_agent.process)
    workflow.add_node("check_renewable_energy_assets", check_renewable_energy_assets_agent.process)
    workflow.add_node("assess_building_envelope", assess_building_envelope_agent.process)
    workflow.add_node("apply_insulation_adjustments", apply_insulation_adjustments_agent.process)
    workflow.add_node("gross_energy_calculation", gross_energy_calculation_agent.process)
    workflow.add_node("calculate_grid_draw_and_expense", calculate_grid_draw_and_expense_agent.process)
    workflow.add_node("compare_against_similar_households", compare_similar_households_agent.process)
    workflow.add_node("solar_roi_analysis", solar_roi_analysis_agent.process)
    workflow.add_node("energy_recommendations", energy_recommendations_agent.process)
    workflow.add_edge(START, "collect_household_profile")

    
    return workflow.compile()


def initialize_profile(profile_data: Dict[str, Any]):
    initial_state: HouseholdProfileState = {
        "profile_data": profile_data,
        "occupancy_data": {},
        "appliance_data": {},
        "building_envelope": {},
        "renewable_assets": {},
        "energy_metrics": {},
        "comparison_summary": {},
        "solar_roi": {},
        "recommendations": {},
        "messages": [],
        "errors": [],
        "current_agent": None,
        "workflow_stage": "Start",
    }

    graph = build_workflow()
    return graph.invoke(initial_state)


if __name__ == "__main__":
    sample_profile = {
        "house_type": "Apartment",
        "floor_area_sqft": 900,
        "num_bedrooms": 2,
        "num_floors": 1,
        "city_tier": "Tier 3",
        "climate_zone": "Hot & Dry",
    }

    result = initialize_profile(sample_profile)
    print(json.dumps(result, indent=2, ensure_ascii=False))

import json
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from langgraph.graph import StateGraph, START, END
from state import HouseholdProfileState
from agents.collect_household_profile_agent import CollectHouseholdProfileAgent
from agents.capture_occupancy_details_agent import CaptureOccupancyDetailsAgent
from agents.capture_household_appliances import CaptureHouseholdAppliancesAgent
from agents.check_renewable_energy_assets_agent import CheckRenewableEnergyAssetsAgent
from agents.assess_building_envelope_agent import AssessBuildingEnvelopeAgent
from agents.gross_energy_calculation_agent import GrossEnergyCalculationAgent
from agents.apply_insulation_adjustments import ApplyInsulationAdjustmentsAgent
from agents.calculate_grid_draw_and_expense_agent import CalculateGridDrawAndExpenseAgent
from agents.compare_against_similar_households_agent import CompareAgainstSimilarHouseholdsAgent
from agents.solar_roi_analysis_agent import SolarROIAnalysisAgent
from agents.energy_recommendations_agent import EnergyRecommendationsAgent

# Load environment variables (for OpenAI API key)
load_dotenv()

# Initialize agents
collect_household_agent = CollectHouseholdProfileAgent()
capture_occupancy_agent = CaptureOccupancyDetailsAgent()
capture_appliances_agent = CaptureHouseholdAppliancesAgent()
check_renewable_energy_assets_agent = CheckRenewableEnergyAssetsAgent()
assess_building_envelope_agent = AssessBuildingEnvelopeAgent()
gross_energy_calculation_agent = GrossEnergyCalculationAgent()
apply_insulation_adjustments_agent = ApplyInsulationAdjustmentsAgent()
calculate_grid_draw_and_expense_agent = CalculateGridDrawAndExpenseAgent()
compare_similar_households_agent = CompareAgainstSimilarHouseholdsAgent()
solar_roi_analysis_agent = SolarROIAnalysisAgent()
energy_recommendations_agent = EnergyRecommendationsAgent()

def collect_household_profile_node(state: HouseholdProfileState) -> HouseholdProfileState:    
    return collect_household_agent.process(state)

def capture_occupancy_details_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return capture_occupancy_agent.process(state)

def capture_appliances_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return capture_appliances_agent.process(state)

def check_renewable_energy_assets_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return check_renewable_energy_assets_agent.process(state)

def assess_building_envelope_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return assess_building_envelope_agent.process(state)

def gross_energy_calculation_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return gross_energy_calculation_agent.process(state)


def apply_insulation_adjustments_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return apply_insulation_adjustments_agent.process(state)

def calculate_grid_draw_and_expense_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return calculate_grid_draw_and_expense_agent.process(state)

def compare_against_similar_households_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return compare_similar_households_agent.process(state)

def solar_roi_analysis_node(state: HouseholdProfileState) -> HouseholdProfileState:
    return solar_roi_analysis_agent.process(state)

def energy_recommendations_node(state: HouseholdProfileState) -> HouseholdProfileState:  
    return energy_recommendations_agent.process(state)

def build_workflow():
   
    workflow = StateGraph(HouseholdProfileState)
    
    # Add nodes
    """  
    workflow.add_node("collect_household_profile", collect_household_profile_node)
    workflow.add_node("capture_occupancy_details", capture_occupancy_details_node)
    workflow.add_node("capture_appliances", capture_appliances_node)
    workflow.add_node("check_renewable_energy_assets", check_renewable_energy_assets_node)
    workflow.add_node("assess_building_envelope", assess_building_envelope_node)
    workflow.add_node("gross_energy_calculation", gross_energy_calculation_node)
    workflow.add_node("apply_insulation_adjustments", apply_insulation_adjustments_node)
    workflow.add_node("calculate_grid_draw_and_expense", calculate_grid_draw_and_expense_node)
    workflow.add_node("compare_against_similar_households", compare_against_similar_households_node)
    workflow.add_node("solar_roi_analysis", solar_roi_analysis_node)
    workflow.add_node("energy_recommendations", energy_recommendations_node)
    # Add edges
    workflow.add_edge(START, "collect_household_profile")
    workflow.add_edge("collect_household_profile", "capture_occupancy_details")
    workflow.add_edge("capture_occupancy_details", "capture_appliances") 
    workflow.add_edge("capture_appliances", "check_renewable_energy_assets")
    workflow.add_edge("check_renewable_energy_assets", "assess_building_envelope")
    workflow.add_edge("assess_building_envelope", "gross_energy_calculation")
    workflow.add_edge("gross_energy_calculation", "apply_insulation_adjustments")
    workflow.add_edge("apply_insulation_adjustments", "calculate_grid_draw_and_expense")
    workflow.add_edge("calculate_grid_draw_and_expense", "compare_against_similar_households")
    workflow.add_edge("compare_against_similar_households", "solar_roi_analysis")
    workflow.add_edge("solar_roi_analysis", "energy_recommendations")
    workflow.add_edge("energy_recommendations", END)
    """

    
   
    workflow.add_node("energy_recommendations", energy_recommendations_node)

    workflow.add_edge(START, "energy_recommendations")
    workflow.add_edge("energy_recommendations", END)

    # Compile the graph
    graph = workflow.compile()
    
    return graph


def initializeProfile(profile_data: dict):
    initial_state: HouseholdProfileState = {
        "profile_data" : profile_data,
        "messages": [],
        "errors": [],
        "current_agent": '',
        "workflow_stage": 'Start'
    }
    
    # Build and run workflow
    graph = build_workflow()
    final_state = graph.invoke(initial_state)   
    return final_state
"""
def _display_results(state: HouseholdProfileState):
  
    print("\n[PROFILE COLLECTION RESULTS]")
    print("-" * 60)
    
    summary = collect_household_agent.get_summary(state)
    
    # Display profile
    print("\n[COLLECTED PROFILE]")
    for key, value in summary['profile'].items():
        if value is not None:
            print("   {}: {}".format(key.replace('_', ' ').title(), value))
    
    # Display validation status
    print("\n[VALIDATION STATUS]")
    stage = summary['stage']
    if stage == "profile_validated":
        print("   Status: [PASSED]")
    else:
        print("   Status: [FAILED]")
    
    # Display analysis
    print("\n[INITIAL ANALYSIS]")
    print("   Similar households found: {}".format(summary['analysis']['similar_households_found']))
    
    # Display similar households
    similar = state.get('similar_households', [])
    if similar:
        print("\n[SIMILAR HOUSEHOLDS SAMPLES]")
        for i, h in enumerate(similar[:3], 1):
            print("   {}. {} - {} bedrooms, {} occupants, {:.1f} kWh/day, ${:.0f}/month".format(
                i,
                h.get('house_type', 'N/A'),
                h.get('num_bedrooms', 'N/A'),
                h.get('num_occupants', 'N/A'),
                h.get('daily_energy_consumption_kWh', 0),
                h.get('monthly_energy_consumption_kWh', 0) * 8  # Assuming ₹8/kWh
            ))
    
    # Display messages from agent
    if summary['messages']:
        print("\n[AGENT MESSAGES]")
        for msg in summary['messages']:
            print("   {}".format(msg))
    
    # Display errors if any
    if summary['errors']:
        print("\n[VALIDATION ERRORS]")
        for error in summary['errors']:
            print("   - {}".format(error))
    
    print("\n" + "="*60)
"""

def main():   
    profile_data= {
    "house_type": "Apartment",
    "num_bedrooms": 2,
    "climate_zone": "Hot & Dry",
    "city_tier": "Tier 3",
    "num_occupants": 3,
    "has_ac": 1,
    "num_ac_units": 2,
    "ac_start_rating": 5,
    "ac_usage_hrs_per_day": 10.0,
    "num_ceiling_fans": 4,
    "water_heater_type": "Solar + Backup",
    "water_heater_capacity_L": 15,
    "water_heater_usage_hrs_per_day": 4.0,
    "has_refrigerator": 1,
    "fridge_capacity_L": 330,
    "fridge_star_rating": 4,
    "has_washing_machine": 1,
    "washing_machine_type": "Top Load",
    "washing_cycles_per_week": 9,
    "num_computers": 2,
    "computer_usage_hrs_per_day": 15.0,
    "num_tvs": 1,
    "tv_screen_size_inch": 55,
    "tv_usage_hrs_per_day": 5.0,
    "has_dishwasher": 1,
    "dishwasher_cycles_per_week": 9,
    "has_microwave": 1,
    "has_solar_panels": 1,
    "solar_capacity_kWp": 2,
    "has_battery_storage": 0,
    "battery_capacity_kWh": 0,
    "appliance_energy_kWh": {
      "ac_kWh_per_day": 20.0,
      "ceiling_fans_kWh_per_day": 3.9,
      "water_heater_kWh_per_day": 3.6,
      "refrigerator_kWh_per_day": 1.815,
      "microwave_kWh_per_day": 1.2,
      "dishwasher_kWh_per_day": 1.929,
      "washing_machine_kWh_per_day": 1.671,
      "tv_kWh_per_day": 0.7,
      "computer_kWh_per_day": 3.6
    },
    "daily_energy_consumption_kWh": 38.415,
    "energy_assumptions": [
      "AC energy assumed at 1.00 kW per unit based on a 5-star rating.",
      "Ceiling fan energy assumed at 65 W per fan for 15.0 hours/day.",
      "Water heater energy assumed at 0.90 kW (Solar + Backup, 15 L) for 4.0 hours/day.",
      "Refrigerator energy assumed at 0.55 kWh per 100 L per day based on a 4-star rating.",
      "Microwave energy assumed at 1.2 kW for 1.0 hour/day.",
      "Dishwasher energy assumed at 1.5 kWh per cycle, averaged over 9.0 cycles/week.",
      "Washing machine energy assumed at 1.3 kWh per cycle for a Top Load machine.",
      "TV energy assumed at 0.14 kW per unit for 5.0 hours/day based on a 55-inch screen.",
      "Computer energy assumed at 120 W per device for 15.0 hours/day.",
      "Climate zone 'Hot & Dry' adjusts gross energy by a factor of 1.05.",
      "Insulation quality was unknown or missing; assumed Average with a factor of 1.00.",
      "Solar generation estimated from 6.5 peak sun hours per day at 1 kW per kWp for 2.00 kWp capacity."
    ],
    "adjusted_daily_energy_kWh": 40.336,
    "energy_adjustment_factors": {
      "climate_factor": 1.05,
      "insulation_factor": 1.0,
      "combined_factor": 1.05
    },
    "energy_adjustment_climate_zone": "Hot & Dry",
    "energy_adjustment_insulation_quality": "Average",
    "solar_generation_kWh_per_day": 13.0,
    "net_grid_draw_kWh_per_day": 25.415,
    "monthly_grid_bill_kWh": 762.45,
    "grid_draw_assumptions": [
      "Solar generation estimated from 6.5 peak sun hours per day at 1 kW per kWp for 2.00 kWp capacity."
    ],
    'solar_roi_analysis': {
        'base_energy_source': 'adjusted_daily_energy_kWh', 
        'base_daily_energy_kWh': 42.73, 
        'grid_cost_per_kWh': 1.0, 
        'capital_cost_per_kWp': 700.0, 
        'scenarios': [{'solar_capacity_kWp': 1.0, 'daily_generation_kWh': 5.5, 'annual_generation_kWh': 2007.5, 'annual_energy_offset_kWh': 2007.5, 'annual_savings': 2007.5, 'capital_cost': 700.0, 'payback_years': 0.35, 'net_savings_25y': 49487.5}, {'solar_capacity_kWp': 3.0, 'daily_generation_kWh': 16.5, 'annual_generation_kWh': 6022.5, 'annual_energy_offset_kWh': 6022.5, 'annual_savings': 6022.5, 'capital_cost': 2100.0, 'payback_years': 0.35, 'net_savings_25y': 148462.5}, {'solar_capacity_kWp': 5.0, 'daily_generation_kWh': 27.5, 'annual_generation_kWh': 10037.5, 'annual_energy_offset_kWh': 10037.5, 'annual_savings': 10037.5, 'capital_cost': 3500.0, 'payback_years': 0.35, 'net_savings_25y': 247437.5}, {'solar_capacity_kWp': 10.0, 'daily_generation_kWh': 55.0, 'annual_generation_kWh': 20075.0, 'annual_energy_offset_kWh': 15596.08, 'annual_savings': 15596.09, 'capital_cost': 7000.0, 'payback_years': 0.45, 'net_savings_25y': 382902.13}], 'assumptions': ['Solar ROI is based on estimated annual generation from peak sun hours.', 'Capital cost is assumed constant per kWp and does not include maintenance or financing.', '25-year savings assume stable grid tariffs and no system degradation.']
        }
  }
    state_1 = initializeProfile(profile_data)   
    print("updated state", state_1)
    

if __name__ == "__main__":
    main()
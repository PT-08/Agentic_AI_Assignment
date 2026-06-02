from typing import TypedDict, Optional, List, Dict, Any, Literal


class HouseholdProfileState(TypedDict, total=False):
    profile_data: Dict[str, Any]
    occupancy_data: Dict[str, Any]
    appliance_data: Dict[str, Any]
    building_envelope: Dict[str, Any]
    renewable_assets: Dict[str, Any]
    energy_metrics: Dict[str, Any]
    comparison_summary: Dict[str, Any]
    solar_roi: Dict[str, Any]
    recommendations: Dict[str, Any]
    messages: List[str]
    errors: List[str]
    current_agent: Optional[str]
    workflow_stage: Literal['Start', 'In progress', 'Error', 'Complete']

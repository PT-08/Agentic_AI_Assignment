from typing import TypedDict, Optional, List, Dict, Any, Literal


class HouseholdProfileState(TypedDict, total=False):
    profile_data: Dict
    similar_households_comparison: Optional[Dict]
    energy_recommendations: Optional[str]
    solar_roi_analysis: Optional[Dict]
    assumptions: Optional[List[str]]
    messages: List[str]
    errors: List[str]
    current_agent: Optional[str]
    workflow_stage: Literal['Start', 'In progress', 'Error', 'Complete']

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState
from utils import (
    normalize_input,
    VALID_HOUSE_TYPES,
    VALID_CLIMATE_ZONES,
    VALID_CITY_TIERS
)


class CollectHouseholdProfileAgent:
    
    def __init__(self):
        self.agent_name = "Agent1_CollectProfile"
    
    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Process household profile collection workflow."""
        
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])
        
        try:
            # Step 0: Collect inputs from terminal with selection menus.
            state['profile_data']['house_type'] = self._prompt_selection(
                "Select house type:", VALID_HOUSE_TYPES
            )
            state['profile_data']['climate_zone'] = self._prompt_selection(
                "Select climate zone:", VALID_CLIMATE_ZONES
            )
            state['profile_data']['city_tier'] = self._prompt_selection(
                "Select city tier:", VALID_CITY_TIERS
            )
            state['profile_data']['num_bedrooms'] = self._prompt_number(
                "Enter number of bedrooms:"
            )           
            state['profile_data']['floor_area_sqft'] = self._prompt_number(
                "Enter floor area in square feet (optional, press Enter to skip):",
                allow_blank=True
            )
            state['workflow_stage'] = "In progress"
            state['messages'].append(
                "[SUCCESS] Profile collected for {} ({} bedrooms, {})".format(
                    state.get('profile_data').get('house_type'),
                    state.get('profile_data').get('num_bedrooms'),
                    state.get('profile_data').get('climate_zone')
                )
            )
            
        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append("[ERROR] {}".format(str(e)))
        
        return state    
    
    def _prompt_selection(self, prompt: str, options: list[str]) -> str:
        """Show a numbered list of options and accept a selection."""
        while True:
            print(f"\n{prompt}")
            for index, option in enumerate(options, start=1):
                print(f"  {index}. {option}")
            selection = input("Enter choice number or exact value: ").strip()
            if not selection:
                print("Please select a value.")
                continue

            if selection.isdigit():
                index = int(selection) - 1
                if 0 <= index < len(options):
                    return options[index]
                print(f"Invalid selection: {selection}. Please enter a number between 1 and {len(options)}.")
                continue

            normalized = normalize_input(selection, options)
            if normalized:
                return normalized
            print(f"Invalid selection: '{selection}'. Please choose one of the listed values.")

    def _prompt_number(self, prompt: str, allow_blank: bool = False) -> int | None:
        """Prompt for a numeric value, optionally allowing blank input."""
        while True:
            value = input(f"{prompt} ").strip()
            if allow_blank and value == "":
                return None
            try:
                number = int(value)
                if number <= 0:
                    print("Please enter a positive integer.")
                    continue
                return number
            except ValueError:
                print("Invalid number. Please enter a valid whole number.")

    def get_summary(self, state: HouseholdProfileState) -> Dict[str, Any]:
        """Get summary of collected profile."""
        return {
            'agent': self.agent_name,
            'stage': state.get('workflow_stage'),
            'profile': {
                'house_type': state.get('profile_data', {}).get('house_type'),
                'bedrooms': state.get('profile_data', {}).get('num_bedrooms'),
                'climate_zone': state.get('profile_data', {}).get('climate_zone'),
                'city_tier': state.get('profile_data', {}).get('city_tier'),
                'occupants': state.get('profile_data', {}).get('num_occupants'),
                'floor_area': state.get('profile_data', {}).get('floor_area_sqft'),
            },
            'messages': state.get('messages', []),
            'errors': state.get('errors', []),
        }

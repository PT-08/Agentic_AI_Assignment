import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path so state can be imported in this module.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class CaptureOccupancyDetailsAgent:
    def __init__(self):
        self.agent_name = "Agent_CaptureOccupancyDetails"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Collect occupancy details and store them in profile_data."""
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        try:
            num_adults = self._prompt_number("Enter number of adults living in the household:")
            num_children = self._prompt_number("Enter number of children living in the household:")

            profile_data = state.get('profile_data') or {}
            profile_data['num_adults'] = num_adults
            profile_data['num_children'] = num_children
            profile_data['num_occupants'] = num_adults + num_children
            state['profile_data'] = profile_data

            state['workflow_stage'] = 'Complete'
            state['messages'].append("[SUCCESS] Occupancy details captured.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append("[ERROR] {}".format(str(e)))
            state['workflow_stage'] = 'Error'

        return state

    def _prompt_number(self, prompt: str) -> int:
        while True:
            value = input(f"{prompt} ").strip()
            if not value:
                print("Please enter a value.")
                continue
            try:
                number = int(value)
                if number < 0:
                    print("Please enter zero or a positive integer.")
                    continue
                return number
            except ValueError:
                print("Invalid number. Please enter a whole number.")

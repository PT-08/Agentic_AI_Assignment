import sys
from pathlib import Path

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class AssessBuildingEnvelopeAgent:
    def __init__(self):
        self.agent_name = "Agent_AssessBuildingEnvelope"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Capture building envelope details and store them in profile_data."""
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}

        try:
            profile_data['insulation_quality'] = self._prompt_selection(
                "Select insulation quality:",
                ["Excellent", "Good", "Average", "Poor"]
            )
            profile_data['window_type'] = self._prompt_selection(
                "Select window type:",
                ["Single Pane", "Double Pane", "Triple Pane"]
            )
            profile_data['roof_type'] = self._prompt_selection(
                "Select roof type:",
                ["Sloped Tiled", "Flat RCC", "Green Roof", "Insulated RCC"]
            )

            state['profile_data'] = profile_data
            state['workflow_stage'] = 'In progress'
            state['messages'].append("[SUCCESS] Building envelope details captured.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append("[ERROR] {}".format(str(e)))
            state['workflow_stage'] = 'Error'

        return state

    def _prompt_selection(self, prompt: str, options: list[str]) -> str:
        while True:
            print(f"\n{prompt}")
            for index, option in enumerate(options, start=1):
                print(f"  {index}. {option}")
            selection = input("Enter choice number or exact value: ").strip()
            if not selection:
                print("This field is required. Please choose an option.")
                continue

            if selection.isdigit():
                index = int(selection) - 1
                if 0 <= index < len(options):
                    return options[index]
                print(f"Invalid selection: {selection}. Please enter a number between 1 and {len(options)}.")
                continue

            normalized = selection.strip()
            for option in options:
                if option.lower() == normalized.lower():
                    return option

            print(f"Invalid selection: '{selection}'. Please choose one of the listed values.")

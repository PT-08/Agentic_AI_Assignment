import sys
from pathlib import Path

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class CheckRenewableEnergyAssetsAgent:
    def __init__(self):
        self.agent_name = "Agent_CheckRenewableEnergyAssets"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Capture renewable energy asset details and store them in profile_data."""
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}

        try:
            has_solar_panels = self._prompt_yes_no("Do you have solar panels installed?")
            profile_data['has_solar_panels'] = 1 if has_solar_panels else 0
            if has_solar_panels:
                profile_data['solar_capacity_kWp'] = self._prompt_number(
                    "Enter solar capacity in kWp:", min_value=0
                )
            else:
                profile_data['solar_capacity_kWp'] = 0

            has_battery_storage = self._prompt_yes_no("Do you have battery storage installed?")
            profile_data['has_battery_storage'] = 1 if has_battery_storage else 0
            if has_battery_storage:
                profile_data['battery_capacity_kWh'] = self._prompt_number(
                    "Enter battery capacity in kWh:", min_value=0
                )
            else:
                profile_data['battery_capacity_kWh'] = 0

            state['profile_data'] = profile_data
            state['workflow_stage'] = 'In progress'
            state['messages'].append("[SUCCESS] Renewable energy asset details captured.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append("[ERROR] {}".format(str(e)))
            state['workflow_stage'] = 'Error'

        return state

    def _prompt_yes_no(self, prompt: str) -> bool:
        while True:
            value = input(f"{prompt} (yes/no): ").strip().lower()
            if value in {"yes", "y"}:
                return True
            if value in {"no", "n"}:
                return False
            print("Please answer yes or no.")

    def _prompt_number(self, prompt: str, min_value: int = 0, max_value: int | None = None) -> int:
        while True:
            value = input(f"{prompt} ").strip()
            if not value:
                print("Please enter a value.")
                continue
            try:
                number = int(value)
                if number < min_value:
                    print(f"Please enter a number greater than or equal to {min_value}.")
                    continue
                if max_value is not None and number > max_value:
                    print(f"Please enter a number less than or equal to {max_value}.")
                    continue
                return number
            except ValueError:
                print("Invalid number. Please enter a whole number.")

import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class CaptureHouseholdAppliancesAgent:
    def __init__(self):
        self.agent_name = "Agent_CaptureHouseholdAppliances"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Capture household appliance details and store them in profile_data."""
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}

        try:
            has_ac = self._prompt_yes_no("Do you have AC(s) in the household?")
            profile_data['has_ac'] = 1 if has_ac else 0
            if has_ac:
                profile_data['num_ac_units'] = self._prompt_number(
                    "Enter number of AC units:", min_value=1
                )
                profile_data['ac_start_rating'] = self._prompt_number(
                    "Enter AC star rating (1-5):", min_value=1, max_value=5
                )
                profile_data['ac_usage_hrs_per_day'] = self._prompt_float(
                    "Enter average AC usage per day (hours):", min_value=0, max_value=24
                )
            else:
                profile_data['num_ac_units'] = 0
                profile_data['ac_start_rating'] = 0
                profile_data['ac_usage_hrs_per_day'] = 0

            profile_data['num_ceiling_fans'] = self._prompt_number(
                "Enter number of ceiling fans:", min_value=0
            )

            water_heater_type = self._prompt_selection(
                "Select water heater type:",
                ["Solar + Backup", "Electric Geyser", "Heat Pump", "None"]
            )
            profile_data['water_heater_type'] = water_heater_type
            if water_heater_type == "None":
                profile_data['water_heater_capacity_L'] = 0
                profile_data['water_heater_usage_hrs_per_day'] = 0
            else:
                profile_data['water_heater_capacity_L'] = self._prompt_number(
                    "Enter water heater capacity in litres:", min_value=1, max_value=50
                )
                profile_data['water_heater_usage_hrs_per_day'] = self._prompt_float(
                    "Enter average water heater usage hours per day:", min_value=0, max_value=24
                )

            has_refrigerator = self._prompt_yes_no("Do you have a refrigerator?")
            profile_data['has_refrigerator'] = 1 if has_refrigerator else 0
            if has_refrigerator:
                profile_data['fridge_capacity_L'] = self._prompt_number(
                    "Enter refrigerator capacity in litres:", min_value=1, max_value=1000
                )
                profile_data['fridge_star_rating'] = self._prompt_number(
                    "Enter refrigerator star rating (1-5):", min_value=1, max_value=5
                )
            else:
                profile_data['fridge_capacity_L'] = 0
                profile_data['fridge_star_rating'] = 0

            has_washing_machine = self._prompt_yes_no("Do you have a washing machine?")
            profile_data['has_washing_machine'] = 1 if has_washing_machine else 0
            if has_washing_machine:
                profile_data['washing_machine_type'] = self._prompt_selection(
                    "Select washing machine type:", ["Top Load", "Semi-Automatic"]
                )
                profile_data['washing_cycles_per_week'] = self._prompt_number(
                    "Enter average washing cycles per week:", min_value=0
                )
            else:
                profile_data['washing_machine_type'] = None
                profile_data['washing_cycles_per_week'] = 0

            profile_data['num_computers'] = self._prompt_number(
                "Enter number of computers:", min_value=0
            )
            if profile_data['num_computers'] > 0:
                profile_data['computer_usage_hrs_per_day'] = self._prompt_float(
                    "Enter average computer usage hours per day:", min_value=0, max_value=24
                )
            else:
                profile_data['computer_usage_hrs_per_day'] = 0

            profile_data['num_tvs'] = self._prompt_number(
                "Enter number of TVs:", min_value=0
            )
            if profile_data['num_tvs'] > 0:
                profile_data['tv_screen_size_inch'] = self._prompt_number(
                    "Enter average TV screen size in inches:", min_value=1
                )
                profile_data['tv_usage_hrs_per_day'] = self._prompt_float(
                    "Enter average TV usage hours per day:", min_value=0, max_value=24
                )
            else:
                profile_data['tv_screen_size_inch'] = 0
                profile_data['tv_usage_hrs_per_day'] = 0

            has_dishwasher = self._prompt_yes_no("Do you have a dishwasher?")
            profile_data['has_dishwasher'] = 1 if has_dishwasher else 0
            profile_data['dishwasher_cycles_per_week'] = self._prompt_number(
                "Enter dishwasher cycles per week:", min_value=0
            ) if has_dishwasher else 0

            has_microwave = self._prompt_yes_no("Do you have a microwave?")
            profile_data['has_microwave'] = 1 if has_microwave else 0

            state['profile_data'] = profile_data
            state['workflow_stage'] = 'In progress'
            state['messages'].append("[SUCCESS] Household appliance details captured.")

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

    def _prompt_selection(self, prompt: str, options: list[str]) -> str:
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

            normalized = selection.strip()
            for option in options:
                if option.lower() == normalized.lower():
                    return option
            print(f"Invalid selection: '{selection}'. Please choose one of the listed values.")

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

    def _prompt_float(self, prompt: str, min_value: float = 0.0, max_value: float | None = None) -> float:
        while True:
            value = input(f"{prompt} ").strip()
            if not value:
                print("Please enter a value.")
                continue
            try:
                number = float(value)
                if number < min_value:
                    print(f"Please enter a value greater than or equal to {min_value}.")
                    continue
                if max_value is not None and number > max_value:
                    print(f"Please enter a value less than or equal to {max_value}.")
                    continue
                return number
            except ValueError:
                print("Invalid value. Please enter a numeric value.")

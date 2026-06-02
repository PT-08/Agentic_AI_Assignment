
import sys
from pathlib import Path
from typing import Any, Dict, List

from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent.parent))
from state import HouseholdProfileState


class CaptureHouseholdAppliancesAgent:
    def __init__(self):
        self.agent_name = "CaptureHouseholdAppliancesAgent"

    def process(self, state: HouseholdProfileState) -> Command:
        appliance_data = dict(state.get("appliance_data", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            # 1. ACs
            appliance_data["has_ac"] = self._prompt_yes_no("Do you have AC units installed?")
            if appliance_data["has_ac"]:
                appliance_data["num_ac_units"] = self._prompt_int("Enter number of AC units:", min_value=1)
                appliance_data["ac_star_rating"] = self._prompt_int("Enter AC star rating (1-5):", min_value=1, max_value=5)
                appliance_data["ac_usage_hrs_per_day"] = float(self._prompt_float("Average AC usage hours per day (per AC):", min_value=0, max_value=24))
            else:
                appliance_data["num_ac_units"] = 0
                appliance_data["ac_star_rating"] = 0
                appliance_data["ac_usage_hrs_per_day"] = 0.0

            # 2. Fans
            appliance_data["num_ceiling_fans"] = self._prompt_int("Number of ceiling fans:", min_value=0)

            # 3. Water heater
            wh_types = ["Solar + Backup", "Electric Geyser", "Heat Pump", "None"]
            appliance_data["water_heater_type"] = self._prompt_choice("Water heater type", wh_types)
            if appliance_data["water_heater_type"] == "None":
                appliance_data["water_heater_capacity_L"] = 0
                appliance_data["water_heater_usage_hrs_per_day"] = 0.0
            else:
                appliance_data["water_heater_capacity_L"] = self._prompt_int("Water heater capacity in litres (max 50):", min_value=0, max_value=50)
                appliance_data["water_heater_usage_hrs_per_day"] = float(self._prompt_float("Average water heater usage hours per day:", min_value=0, max_value=24))

            # 4. Refrigerator
            appliance_data["has_refrigerator"] = self._prompt_yes_no("Do you have a refrigerator?")
            if appliance_data["has_refrigerator"]:
                appliance_data["fridge_capacity_L"] = self._prompt_int("Enter refrigerator capacity in litres (avg total):", min_value=1, max_value=1000)
                appliance_data["fridge_star_rating"] = self._prompt_int("Average fridge star rating (1-5):", min_value=1, max_value=5)
            else:
                appliance_data["fridge_capacity_L"] = 0
                appliance_data["fridge_star_rating"] = 0

            # 5. Washing machine
            appliance_data["has_washing_machine"] = self._prompt_yes_no("Do you have a washing machine?")
            if not appliance_data["has_washing_machine"]:
                appliance_data["washing_machine_type"] = None
                appliance_data["washing_cycles_per_week"] = 0
            else:
                wm_types = ["Top Load", "Semi-Automatic"]
                appliance_data["washing_machine_type"] = self._prompt_choice("Washing machine type", wm_types)
                appliance_data["washing_cycles_per_week"] = self._prompt_int("Average washing cycles per week:", min_value=0)

            # 6. Computers
            appliance_data["num_computers"] = self._prompt_int("Count of computers:", min_value=0)
            if appliance_data["num_computers"] > 0:
                appliance_data["computer_usage_hrs_per_day"] = float(self._prompt_float("Average computer usage hours per day:", min_value=0, max_value=24))
            else:
                appliance_data["computer_usage_hrs_per_day"] = 0.0

            # 7. TV
            appliance_data["num_tvs"] = self._prompt_int("Number of TVs:", min_value=0)
            if appliance_data["num_tvs"] > 0:
                appliance_data["tv_screen_size_inch"] = self._prompt_int("Average TV screen size (inch):", min_value=1)
                appliance_data["tv_usage_hrs_per_day"] = float(self._prompt_float("Average TV usage hours per day:", min_value=0, max_value=24))
            else:
                appliance_data["tv_screen_size_inch"] = 0
                appliance_data["tv_usage_hrs_per_day"] = 0.0

            # 8. Dishwasher
            appliance_data["has_dishwasher"] = self._prompt_yes_no("Do you have a dishwasher?")
            if appliance_data["has_dishwasher"]:
                appliance_data["dishwasher_cycles_per_week"] = self._prompt_int("Dishwasher cycles per week:", min_value=0)
            else:
                appliance_data["dishwasher_cycles_per_week"] = 0

            # 9. Microwave
            appliance_data["has_microwave"] = self._prompt_yes_no("Do you have a microwave?")

            updates["appliance_data"] = appliance_data
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Household appliances captured.")
        except Exception as exc:
            errors.append(str(exc))
            updates["workflow_stage"] = "Error"
            messages.append(f"[ERROR] {exc}")

        updates["messages"] = messages
        updates["errors"] = errors
        return Command(update=updates, goto=self.route(updates))

    def route(self, state: HouseholdProfileState) -> str:
        if state.get("errors"):
            return "END"
        return "assess_building_envelope"

    def _colored_input(self, prompt: str) -> str:
        return input(f"\x1b[1;36m{prompt}\x1b[0m ")

    def _prompt_yes_no(self, prompt: str) -> int:
        while True:
            answer = self._colored_input(prompt + " (yes/no):").strip().lower()
            if answer in {"yes", "y"}:
                return 1
            if answer in {"no", "n"}:
                return 0
            print("Please answer yes or no.")

    def _prompt_int(self, prompt: str, min_value: int = 0, max_value: int = None) -> int:
        while True:
            answer = self._colored_input(prompt)
            try:
                value = int(answer)
                if value < min_value:
                    print(f"Please enter a number greater than or equal to {min_value}.")
                    continue
                if max_value is not None and value > max_value:
                    print(f"Please enter a number less than or equal to {max_value}.")
                    continue
                return value
            except ValueError:
                print("Invalid number. Please enter a whole number.")

    def _prompt_float(self, prompt: str, min_value: float = 0.0, max_value: float = None) -> float:
        while True:
            answer = self._colored_input(prompt)
            try:
                value = float(answer)
                if value < min_value:
                    print(f"Please enter a number greater than or equal to {min_value}.")
                    continue
                if max_value is not None and value > max_value:
                    print(f"Please enter a number less than or equal to {max_value}.")
                    continue
                return value
            except ValueError:
                print("Invalid number. Please enter a numeric value.")

    def _prompt_choice(self, prompt: str, options: List[str]) -> str:
        # Present numbered options and accept either index or text (case-insensitive)
        while True:
            print("Options:")
            for i, opt in enumerate(options, start=1):
                print(f"  {i}. {opt}")
            answer = self._colored_input(f"{prompt} (enter number or text):").strip()
            # try numeric selection
            if answer.isdigit():
                idx = int(answer)
                if 1 <= idx <= len(options):
                    return options[idx - 1]
                print(f"Please enter a number between 1 and {len(options)}.")
                continue
            # text match (case-insensitive)
            for opt in options:
                if answer.lower() == opt.lower():
                    return opt
            print(f"Please choose a valid option by number or exact text.")

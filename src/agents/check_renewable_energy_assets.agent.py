
import sys
from pathlib import Path
from typing import Any, Dict

from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent.parent))
from state import HouseholdProfileState

class CheckRenewableEnergyAssetsAgent:
    def __init__(self):
        self.agent_name = "CheckRenewableEnergyAssetsAgent"

    def process(self, state: HouseholdProfileState) -> Command:
        renewable_assets = dict(state.get("renewable_assets", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            renewable_assets["has_solar_panels"] = self._prompt_yes_no("Do you have rooftop solar panels installed?")
            if renewable_assets["has_solar_panels"]:
                renewable_assets["solar_capacity_kWp"] = self._prompt_int("Enter rooftop solar capacity in kWp:", min_value=0)
            else:
                renewable_assets["solar_capacity_kWp"] = 0

            renewable_assets["has_battery_storage"] = self._prompt_yes_no("Do you have battery storage installed?")
            if renewable_assets["has_battery_storage"]:
                renewable_assets["battery_capacity_kWh"] = self._prompt_int("Enter battery storage capacity in kWh:", min_value=0)
            else:
                renewable_assets["battery_capacity_kWh"] = 0

            updates["renewable_assets"] = renewable_assets
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Renewable energy assets recorded.")
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
        return "gross_energy_calculation"

    def _colored_input(self, prompt: str) -> str:
        return input(f"[1;36m{prompt}[0m ")

    def _prompt_yes_no(self, prompt: str) -> int:
        while True:
            answer = self._colored_input(prompt + " (yes/no):").strip().lower()
            if answer in {"yes", "y"}:
                return 1
            if answer in {"no", "n"}:
                return 0
            print("Please answer yes or no.")

    def _prompt_int(self, prompt: str, min_value: int = 0) -> int:
        while True:
            answer = self._colored_input(prompt)
            try:
                value = int(answer)
                if value < min_value:
                    print(f"Please enter a number greater than or equal to {min_value}.")
                    continue
                return value
            except ValueError:
                print("Invalid number. Please enter a whole number.")

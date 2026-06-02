
import sys
from pathlib import Path
from typing import Any, Dict

from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent.parent))
from state import HouseholdProfileState

class CaptureOccupancyDetailsAgent:
    def __init__(self):
        self.agent_name = "CaptureOccupancyDetailsAgent"

    def process(self, state: HouseholdProfileState) -> Command:
        profile_data = dict(state.get("profile_data", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            num_adults = self._prompt_int("Enter number of adults living in the household:", min_value=0)
            num_children = self._prompt_int("Enter number of children living in the household:", min_value=0)

            profile_data["num_adults"] = num_adults
            profile_data["num_children"] = num_children
            profile_data["num_occupants"] = num_adults + num_children

            updates["profile_data"] = profile_data
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Occupancy details recorded.")
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
        return "capture_household_appliances"

    def _colored_input(self, prompt: str) -> str:
        return input(f"[1;36m{prompt}[0m ")

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


import sys
from pathlib import Path
from typing import Any, Dict, List

from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent.parent))
from state import HouseholdProfileState

class AssessBuildingEnvelopeAgent:
    def __init__(self):
        self.agent_name = "AssessBuildingEnvelopeAgent"

    def process(self, state: HouseholdProfileState) -> Command:
        building_envelope = dict(state.get("building_envelope", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            building_envelope["insulation_quality"] = self._prompt_choice(
                "Select insulation quality:",
                ["Excellent", "Good", "Average", "Poor"],
            )
            building_envelope["window_type"] = self._prompt_choice(
                "Select window type:",
                ["Single Pane", "Double Pane", "Triple Pane"],
            )
            building_envelope["roof_type"] = self._prompt_choice(
                "Select roof type:",
                ["Sloped Tiled", "Flat RCC", "Insulated RCC"],
            )

            updates["building_envelope"] = building_envelope
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Building envelope details captured.")
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
        return "check_renewable_energy_assets"

    def _colored_input(self, prompt: str) -> str:
        return input(f"[1;36m{prompt}[0m ")

    def _prompt_choice(self, prompt: str, options: List[str]) -> str:
        while True:
            print(f"[1;33m{prompt}[0m")
            for index, option in enumerate(options, start=1):
                print(f"  {index}. {option}")
            answer = self._colored_input("Enter choice number or exact value:")
            if answer.isdigit():
                index = int(answer) - 1
                if 0 <= index < len(options):
                    return options[index]
            else:
                normalized = answer.strip().lower()
                for option in options:
                    if normalized == option.lower():
                        return option
            print("Invalid selection. Please choose a valid option.")


import sys
from pathlib import Path
from typing import Any, Dict

from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent.parent))
from state import HouseholdProfileState

class ApplyInsulationAdjustmentsAgent:
    def __init__(self):
        self.agent_name = "ApplyInsulationAdjustmentsAgent"

    def process(self, state: HouseholdProfileState) -> Command:
        profile_data = dict(state.get("profile_data", {}))
        building_envelope = dict(state.get("building_envelope", {}))
        energy_metrics = dict(state.get("energy_metrics", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            base_kwh = float(energy_metrics.get("daily_energy_consumption_kWh", 0.0))
            climate_zone = str(profile_data.get("climate_zone", "Temperate"))
            insulation_quality = str(building_envelope.get("insulation_quality", "Average"))

            climate_factor = self._climate_factor(climate_zone)
            insulation_factor = self._insulation_factor(insulation_quality)
            combined_factor = climate_factor * insulation_factor

            adjusted = round(base_kwh * combined_factor, 3)

            energy_metrics["adjusted_daily_energy_kWh"] = adjusted
            energy_metrics["energy_adjustment_factors"] = {
                "climate_factor": round(climate_factor, 3),
                "insulation_factor": round(insulation_factor, 3),
                "combined_factor": round(combined_factor, 3),
            }
            energy_metrics.setdefault("energy_assumptions", [])
            energy_metrics["energy_assumptions"].append(
                f"Applied climate factor {climate_factor:.3f} and insulation factor {insulation_factor:.3f}."
            )

            updates["energy_metrics"] = energy_metrics
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Climate and insulation adjustments applied.")
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
        return "calculate_grid_draw_and_expense"

    def _climate_factor(self, climate_zone: str) -> float:
        mapping = {
            "hot & dry": 1.05,
            "hot & humid": 1.10,
            "temperate": 1.00,
            "composite": 1.02,
            "cold": 1.15,
        }
        return mapping.get(climate_zone.strip().lower(), 1.00)

    def _insulation_factor(self, insulation_quality: str) -> float:
        mapping = {
            "excellent": 0.90,
            "good": 0.95,
            "average": 1.00,
            "poor": 1.10,
        }
        return mapping.get(insulation_quality.strip().lower(), 1.00)

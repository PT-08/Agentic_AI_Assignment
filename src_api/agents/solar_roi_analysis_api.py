from typing import Any, Dict, List, Optional

from langgraph.graph import END
from langgraph.types import Command

from src_api.state import HouseholdProfileState


class APISolarROIAnalysisAgent:
    def __init__(self, next_node: Optional[str] = None):
        self.agent_name = "SolarROIAnalysisAgent"
        self.next_node = next_node

    def process(self, state: HouseholdProfileState) -> Command:
        energy_metrics = dict(state.get("energy_metrics", {}))
        profile_data = dict(state.get("profile_data", {}))
        renewable_assets = dict(state.get("renewable_assets", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            tariff = float(profile_data.get("electricity_tariff_per_kWh", 8.0))
            base_kwh = float(
                energy_metrics.get("adjusted_daily_energy_kWh", energy_metrics.get("daily_energy_consumption_kWh", 0.0))
            )
            climate = (profile_data.get("climate_zone") or "").strip().lower()
            peak_sun = self._peak_sun_hours_for_climate(climate)

            solar_gen = float(energy_metrics.get("solar_generation_kWh_per_day", 0.0))
            solar_capacity = float(
                profile_data.get("solar_capacity_kWp") or renewable_assets.get("solar_capacity_kWp", 0.0) or 0.0
            )
            if solar_gen <= 0 and solar_capacity > 0:
                solar_gen = self._estimate_solar_generation_kwh_per_day(solar_capacity, peak_sun)

            assumptions: List[str] = list(energy_metrics.get("assumptions", []))
            assumptions.append(f"Using peak sun hours = {peak_sun} for climate '{profile_data.get('climate_zone')}'.")
            assumptions.append(f"Using base daily consumption = {round(base_kwh,3)} kWh/day.")
            if solar_capacity > 0:
                assumptions.append(
                    f"Using existing solar capacity = {solar_capacity} kWp -> est {round(solar_gen,3)} kWh/day."
                )

            scenarios = []
            for capacity in [1.0, 3.0, 5.0]:
                annual_generation = capacity * peak_sun * 365
                annual_savings = min(annual_generation, base_kwh * 365) * tariff
                scenarios.append(
                    {
                        "capacity_kWp": capacity,
                        "annual_generation_kWh": round(annual_generation, 2),
                        "annual_savings": round(annual_savings, 2),
                    }
                )

            updates["solar_roi"] = {"scenarios": scenarios, "assumptions": assumptions}
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Solar ROI analysis completed.")
        except Exception as exc:
            errors.append(str(exc))
            updates["workflow_stage"] = "Error"
            messages.append(f"[ERROR] {exc}")

        updates["messages"] = messages
        updates["errors"] = errors
        return Command(update=updates, goto=self.route(updates))

    def route(self, state: HouseholdProfileState):
        if state.get("errors"):
            return END
        if self.next_node is None:
            return END
        return self.next_node

    def _peak_sun_hours_for_climate(self, climate_zone: str) -> float:
        mapping = {
            "hot & dry": 6.5,
            "hot & humid": 5.5,
            "temperate": 4.5,
            "composite": 5.0,
            "cold": 3.5,
        }
        return mapping.get(climate_zone.lower(), 4.5)

    def _estimate_solar_generation_kwh_per_day(self, solar_capacity_kWp: float, peak_sun_hours: float) -> float:
        try:
            return float(solar_capacity_kWp) * float(peak_sun_hours)
        except Exception:
            return 0.0

from pathlib import Path
from typing import Any, Dict, List, Optional

from langgraph.graph import END
from langgraph.types import Command

from src_api.state import HouseholdProfileState


class APICalculateGridDrawAndExpenseAgent:
    def __init__(self, tariff: float, next_node: Optional[str] = None):
        self.agent_name = "CalculateGridDrawAndExpenseAgent"
        self.api_tariff = float(tariff)
        self.next_node = next_node

    def process(self, state: HouseholdProfileState) -> Command:
        renewable_assets = dict(state.get("renewable_assets", {}))
        energy_metrics = dict(state.get("energy_metrics", {}))
        profile_data = dict(state.get("profile_data", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            tariff = float(self.api_tariff)
            profile_data["electricity_tariff_per_kWh"] = tariff

            daily_consumption = float(
                profile_data.get("daily_energy_consumption_kWh")
                or energy_metrics.get("adjusted_daily_energy_kWh")
                or energy_metrics.get("daily_energy_consumption_kWh")
                or 0.0
            )

            has_solar = bool(profile_data.get("has_solar_panels") or renewable_assets.get("has_solar_panels"))
            solar_capacity = 0.0
            if has_solar:
                solar_capacity = float(
                    profile_data.get("solar_capacity_kWp")
                    or renewable_assets.get("solar_capacity_kWp", 0.0)
                    or 0.0
                )

            assumptions: List[str] = list(energy_metrics.get("assumptions", []))
            climate = (profile_data.get("climate_zone") or "").strip().lower()
            peak_sun = self._peak_sun_hours_for_climate(climate)
            assumptions.append(
                f"Assume peak sun hours = {peak_sun} for climate zone '{profile_data.get('climate_zone')}'."
            )

            solar_kwh = self._estimate_solar_generation_kwh_per_day(solar_capacity, peak_sun)
            assumptions.append(
                f"Estimated solar generation = {round(solar_kwh,3)} kWh/day from {solar_capacity} kWp capacity."
            )

            net_draw = max(daily_consumption - solar_kwh, 0.0)
            monthly_bill = round(net_draw * 30.0 * tariff, 2)

            energy_metrics["daily_energy_consumption_kWh"] = daily_consumption
            energy_metrics["solar_generation_kWh_per_day"] = round(solar_kwh, 3)
            energy_metrics["solar_peak_sun_hours"] = peak_sun
            energy_metrics["net_grid_draw_kWh_per_day"] = round(net_draw, 3)
            energy_metrics["monthly_grid_bill"] = monthly_bill
            energy_metrics["assumptions"] = assumptions

            updates["profile_data"] = profile_data
            updates["energy_metrics"] = energy_metrics
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Grid draw and expense estimated.")
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

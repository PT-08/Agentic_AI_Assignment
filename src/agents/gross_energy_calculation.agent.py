import sys
from pathlib import Path
from typing import Any, Dict

from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent.parent))
from state import HouseholdProfileState


class GrossEnergyCalculationAgent:
    def __init__(self):
        self.agent_name = "GrossEnergyCalculationAgent"

    def process(self, state: HouseholdProfileState) -> Command:
        appliance_data = dict(state.get("appliance_data", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            energy_breakdown = {
                "ac_kWh_per_day": self._calc_ac(appliance_data),
                "ceiling_fans_kWh_per_day": self._calc_fans(appliance_data),
                "water_heater_kWh_per_day": self._calc_water_heater(appliance_data),
                "refrigerator_kWh_per_day": self._calc_refrigerator(appliance_data),
                "microwave_kWh_per_day": self._calc_microwave(appliance_data),
                "dishwasher_kWh_per_day": self._calc_dishwasher(appliance_data),
                "washing_machine_kWh_per_day": self._calc_washing_machine(appliance_data),
                "tv_kWh_per_day": self._calc_tvs(appliance_data),
                "computer_kWh_per_day": self._calc_computers(appliance_data),
            }
            total_kwh = round(sum(energy_breakdown.values()), 3)

            updates["energy_metrics"] = {
                "energy_breakdown": energy_breakdown,
                "daily_energy_consumption_kWh": total_kwh,
                "energy_assumptions": self._assumptions(appliance_data),
            }
            updates["workflow_stage"] = "In progress"
            messages.append("[SUCCESS] Gross energy consumption calculated.")
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
        return "apply_insulation_adjustments"

    def _calc_ac(self, data: Dict[str, Any]) -> float:
        if int(data.get("has_ac", 0)) != 1:
            return 0.0
        units = int(data.get("num_ac_units", 0))
        hours = float(data.get("ac_usage_hrs_per_day", 0))
        rating = int(data.get("ac_start_rating", 3))
        rating = max(1, min(rating, 5))
        power_kw = 1.8 - 0.2 * (rating - 1)
        return round(units * power_kw * hours, 3)

    def _calc_fans(self, data: Dict[str, Any]) -> float:
        fans = int(data.get("num_ceiling_fans", 0))
        hours = 15.0
        power_kw = 0.065
        return round(fans * power_kw * hours, 3)

    def _calc_water_heater(self, data: Dict[str, Any]) -> float:
        heater_type = str(data.get("water_heater_type", "None")).strip()
        if heater_type.lower() in {"none", "", "null"}:
            return 0.0
        capacity = float(data.get("water_heater_capacity_L", 0))
        hours = float(data.get("water_heater_usage_hrs_per_day", 0))
        base_kw = {
            "Solar + Backup": 1.5,
            "Electric Geyser": 3.0,
            "Heat Pump": 1.2,
        }.get(heater_type, 2.5)
        return round(base_kw * max(capacity, 50.0) / 100.0 * hours, 3)

    def _calc_refrigerator(self, data: Dict[str, Any]) -> float:
        if int(data.get("has_refrigerator", 0)) != 1:
            return 0.0
        capacity = float(data.get("fridge_capacity_L", 0))
        rating = int(data.get("fridge_star_rating", 3))
        rating = max(1, min(rating, 5))
        base_per_100l = 0.9 - 0.12 * (rating - 1)
        return round(max(capacity / 100.0 * base_per_100l, 0.0), 3)

    def _calc_microwave(self, data: Dict[str, Any]) -> float:
        if int(data.get("has_microwave", 0)) != 1:
            return 0.0
        return 1.2

    def _calc_dishwasher(self, data: Dict[str, Any]) -> float:
        if int(data.get("has_dishwasher", 0)) != 1:
            return 0.0
        cycles = float(data.get("dishwasher_cycles_per_week", 0))
        return round(cycles / 7.0 * 1.5, 3)

    def _calc_washing_machine(self, data: Dict[str, Any]) -> float:
        if int(data.get("has_washing_machine", 0)) != 1:
            return 0.0
        cycles = float(data.get("washing_machine_cycles_per_week", 0))
        machine_type = str(data.get("washing_machine_type", "Top Load")).strip()
        energy_per_cycle = 1.3 if machine_type.lower() == "top load" else 1.0
        return round(cycles / 7.0 * energy_per_cycle, 3)

    def _calc_tvs(self, data: Dict[str, Any]) -> float:
        tv_count = int(data.get("num_tvs", 0))
        if tv_count <= 0:
            return 0.0
        size = float(data.get("tv_screen_size_inch", 40))
        hours = float(data.get("tv_usage_hrs_per_day", 0))
        if size <= 32:
            power_kw = 0.06
        elif size <= 43:
            power_kw = 0.09
        elif size <= 55:
            power_kw = 0.14
        else:
            power_kw = 0.18
        return round(tv_count * power_kw * hours, 3)

    def _calc_computers(self, data: Dict[str, Any]) -> float:
        computers = int(data.get("num_computers", 0))
        if computers <= 0:
            return 0.0
        hours = float(data.get("computer_usage_hrs_per_day", 0))
        power_kw = 0.12
        return round(computers * power_kw * hours, 3)

    def _assumptions(self, data: Dict[str, Any]) -> list[str]:
        return [
            "AC assumed 1.8 kW for 1-star and decreases by 0.2 kW per extra star.",
            "Ceiling fans assumed 65 W each, running 15 hours per day.",
            "Water heaters assumed 1.2-3.0 kW base power scaled by tank size.",
            "Refrigerators assumed 0.9 kWh per 100 L for 1-star ratings.",
            "Microwave assumed at 1.2 kW for one hour daily.",
            "Dishwasher assumed 1.5 kWh per cycle.",
            "Washing machine assumed 1.3 kWh per cycle for Top Load and 1.0 kWh otherwise.",
            "TV energy estimated by screen size band and daily usage hours.",
            "Computers assumed 120 W each while running.",
        ]

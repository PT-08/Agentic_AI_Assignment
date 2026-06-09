from typing import Any, Dict, List, Optional

from langgraph.graph import END
from langgraph.types import Command

from src_api.state import HouseholdProfileState


class APICalculateGridDrawAndExpenseAgent:
    def __init__(self, tariff: float, next_node: Optional[str] = None):
        self.agent_name = "CalculateGridDrawAndExpenseAgent"
        self.api_tariff = float(tariff)
        self.next_node = next_node

    def calculate(self, state: HouseholdProfileState) -> Command:
        profile_data = dict(state.get("profile_data", {}))
        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            tariff = float(self.api_tariff)
            profile_data["electricity_tariff_per_kWh"] = tariff

            # Calculate gross energy consumption from appliance data
            energy_breakdown = {
                "ac_kWh_per_day": self._calc_ac(profile_data),
                "ceiling_fans_kWh_per_day": self._calc_fans(profile_data),
                "water_heater_kWh_per_day": self._calc_water_heater(profile_data),
                "refrigerator_kWh_per_day": self._calc_refrigerator(profile_data),
                "microwave_kWh_per_day": self._calc_microwave(profile_data),
                "dishwasher_kWh_per_day": self._calc_dishwasher(profile_data),
                "washing_machine_kWh_per_day": self._calc_washing_machine(profile_data),
                "tv_kWh_per_day": self._calc_tvs(profile_data),
                "computer_kWh_per_day": self._calc_computers(profile_data),
            }
            daily_consumption = round(sum(energy_breakdown.values()), 3)
            
            ## Applying insulation adjustments 
            climate = (profile_data.get("climate_zone") or "").strip().lower()
            insulation_quality = str(profile_data.get("insulation_quality", "Average"))
            (adjusted, combined_factor, climate_factor, insulation_factor) = self._apply_insulation_adjustments(daily_consumption=daily_consumption, climate_zone=climate, insulation_quality=insulation_quality)
            

            # Calculate solar generation
            assumptions: List[str] = [
                "AC assumed 1.8 kW for 1-star and decreases by 0.2 kW per extra star.",
                "Ceiling fans assumed 65 W each, running 15 hours per day.",
                "Water heaters assumed 1.2-3.0 kW base power scaled by tank size.",
                "Refrigerators assumed 0.9 kWh per 100 L for 1-star ratings.",
                "Microwave assumed at 1.2 kW for one hour daily.",
                "Dishwasher assumed 1.5 kWh per cycle.",
                "Washing machine assumed 1.3 kWh per cycle for Top Load and 1.0 kWh otherwise.",
                "TV energy estimated by screen size band and daily usage hours.",
                "Computers assumed 120 W each while running.",
                "Applied climate factor {climate_factor:.3f} and insulation factor {insulation_factor:.3f}."
            ]

            peak_sun = self._peak_sun_hours_for_climate(climate)
            assumptions.append(
                f"Assume peak sun hours = {peak_sun} for climate zone '{profile_data.get('climate_zone')}'."
            )

            has_solar = bool(profile_data.get("has_solar_panels", 0))
            solar_capacity = 0.0
            if has_solar:
                solar_capacity = float(profile_data.get("solar_capacity_kWp", 0.0))

            solar_kwh = self._estimate_solar_generation_kwh_per_day(solar_capacity, peak_sun)
            assumptions.append(
                f"Estimated solar generation = {round(solar_kwh, 3)} kWh/day from {solar_capacity} kWp capacity."
            )

            net_draw = max(daily_consumption - solar_kwh, 0.0)
            monthly_bill = round(net_draw * 30.0 * tariff, 2)

            energy_metrics = {
                "energy_breakdown": energy_breakdown,
                "daily_energy_consumption_kWh": daily_consumption,
                "monthly_energy_consumption_kWh": daily_consumption * 30,
                "adjusted_daily_energy_kWh": adjusted,
                "climate_factor": round(climate_factor, 3),
                "insulation_factor": round(insulation_factor, 3),
                "combined_factor": round(combined_factor, 3),
                "solar_generation_kWh_per_day": round(solar_kwh, 3),
                "solar_peak_sun_hours": peak_sun,
                "net_grid_draw_kWh_per_day": round(net_draw, 3),
                "monthly_grid_bill": monthly_bill,
                "assumptions": assumptions,
            }

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

    def _calc_ac(self, data: Dict[str, Any]) -> float:
        if int(data.get("has_ac", 0)) != 1:
            return 0.0
        units = int(data.get("num_ac_units", 0))
        hours = float(data.get("ac_usage_hrs_per_day", 0))
        rating = int(data.get("ac_star_rating", data.get("ac_start_rating", 3)))
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
        cycles = float(data.get("washing_cycles_per_week", 0))
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

    def _peak_sun_hours_for_climate(self, climate_zone: str) -> float:
        mapping = {
            "hot & dry": 6.5,
            "hot & humid": 5.5,
            "temperate": 4.5,
            "composite": 5.0,
            "cold": 3.5,
        }
        return mapping.get(climate_zone.lower(), 4.5)

    def _apply_insulation_adjustments(self, daily_consumption: float, climate_zone: str, insulation_quality) -> float:
        climate_factor = self._climate_factor(climate_zone)
        insulation_factor = self._insulation_factor(insulation_quality)
        combined_factor = climate_factor * insulation_factor
        adjusted = round(daily_consumption * combined_factor, 3)
        return (adjusted, combined_factor, climate_factor, insulation_factor)
        
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
    
       
        
    def _estimate_solar_generation_kwh_per_day(self, solar_capacity_kWp: float, peak_sun_hours: float) -> float:
        try:
            return float(solar_capacity_kWp) * float(peak_sun_hours)
        except Exception:
            return 0.0

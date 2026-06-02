import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class GrossEnergyCalculationAgent:
    def __init__(self):
        self.agent_name = "Agent_GrossEnergyCalculation"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Calculate estimated daily appliance energy consumption in kWh."""
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}
        energy_breakdown: Dict[str, float] = {}
        assumptions: list[str] = []
        total_kwh = 0.0

        try:
            ac_kwh = self._calculate_ac(profile_data, assumptions)
            energy_breakdown['ac_kWh_per_day'] = ac_kwh
            total_kwh += ac_kwh

            fan_kwh = self._calculate_ceiling_fans(profile_data, assumptions)
            energy_breakdown['ceiling_fans_kWh_per_day'] = fan_kwh
            total_kwh += fan_kwh

            heater_kwh = self._calculate_water_heater(profile_data, assumptions)
            energy_breakdown['water_heater_kWh_per_day'] = heater_kwh
            total_kwh += heater_kwh

            fridge_kwh = self._calculate_refrigerator(profile_data, assumptions)
            energy_breakdown['refrigerator_kWh_per_day'] = fridge_kwh
            total_kwh += fridge_kwh

            microwave_kwh = self._calculate_microwave(profile_data, assumptions)
            energy_breakdown['microwave_kWh_per_day'] = microwave_kwh
            total_kwh += microwave_kwh

            dishwasher_kwh = self._calculate_dishwasher(profile_data, assumptions)
            energy_breakdown['dishwasher_kWh_per_day'] = dishwasher_kwh
            total_kwh += dishwasher_kwh

            washing_machine_kwh = self._calculate_washing_machine(profile_data, assumptions)
            energy_breakdown['washing_machine_kWh_per_day'] = washing_machine_kwh
            total_kwh += washing_machine_kwh

            tv_kwh = self._calculate_tvs(profile_data, assumptions)
            energy_breakdown['tv_kWh_per_day'] = tv_kwh
            total_kwh += tv_kwh

            computer_kwh = self._calculate_computers(profile_data, assumptions)
            energy_breakdown['computer_kWh_per_day'] = computer_kwh
            total_kwh += computer_kwh

            state['profile_data'] = profile_data
            state['profile_data']['appliance_energy_kWh'] = {
                key: self._round_kwh(value) for key, value in energy_breakdown.items()
            }
            state['profile_data']['daily_energy_consumption_kWh'] = self._round_kwh(total_kwh)
            state['profile_data']['energy_assumptions'] = assumptions

            state['workflow_stage'] = 'Complete'
            state['messages'].append("[SUCCESS] Gross energy consumption calculated.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append("[ERROR] {}".format(str(e)))
            state['workflow_stage'] = 'Error'

        return state

    def _calculate_ac(self, profile_data: Dict, assumptions: list[str]) -> float:
        if profile_data.get('has_ac') != 1:
            assumptions.append("No AC units present, AC consumption set to 0 kWh/day.")
            return 0.0

        num_units = int(profile_data.get('num_ac_units', 0))
        hours = float(profile_data.get('ac_usage_hrs_per_day', 0.0))
        star_rating = int(profile_data.get('ac_start_rating', 1))

        power_kw = self._ac_power_kw(star_rating)
        energy = num_units * power_kw * hours

        assumptions.append(
            f"AC energy assumed at {power_kw:.2f} kW per unit based on a {star_rating}-star rating."
        )
        return energy

    def _ac_power_kw(self, star_rating: int) -> float:
        rating = max(1, min(star_rating, 5))
        return 1.5 - 0.125 * (rating - 1)

    def _calculate_ceiling_fans(self, profile_data: Dict, assumptions: list[str]) -> float:
        num_fans = int(profile_data.get('num_ceiling_fans', 0))
        if num_fans <= 0:
            assumptions.append("No ceiling fans present, fan consumption set to 0 kWh/day.")
            return 0.0

        hours = 15.0
        power_kw = 0.065
        energy = num_fans * power_kw * hours
        assumptions.append(
            f"Ceiling fan energy assumed at {power_kw*1000:.0f} W per fan for {hours} hours/day."
        )
        return energy

    def _calculate_water_heater(self, profile_data: Dict, assumptions: list[str]) -> float:
        heater_type = profile_data.get('water_heater_type')
        if heater_type is None or str(heater_type).strip().lower() == 'none':
            assumptions.append("No water heater in use, water heater consumption set to 0 kWh/day.")
            return 0.0

        capacity = float(profile_data.get('water_heater_capacity_L', 0.0))
        hours = float(profile_data.get('water_heater_usage_hrs_per_day', 0.0))
        type_power_kw = {
            'Solar + Backup': 1.5,
            'Electric Geyser': 3.0,
            'Heat Pump': 1.2,
        }.get(heater_type, 2.5)

        capacity_scale = max(capacity, 1.0) / 25.0
        power_kw = type_power_kw * capacity_scale
        energy = power_kw * hours

        assumptions.append(
            f"Water heater energy assumed at {power_kw:.2f} kW ({heater_type}, {capacity:.0f} L) for {hours:.1f} hours/day."
        )
        return energy

    def _calculate_refrigerator(self, profile_data: Dict, assumptions: list[str]) -> float:
        if profile_data.get('has_refrigerator') != 1:
            assumptions.append("No refrigerator present, refrigerator consumption set to 0 kWh/day.")
            return 0.0

        capacity = float(profile_data.get('fridge_capacity_L', 0.0))
        star_rating = int(profile_data.get('fridge_star_rating', 1))
        effective_rating = max(1, min(star_rating, 5))
        base_kwh_per_100l = 0.85 - 0.10 * (effective_rating - 1)
        energy = capacity / 100.0 * base_kwh_per_100l

        assumptions.append(
            f"Refrigerator energy assumed at {base_kwh_per_100l:.2f} kWh per 100 L per day based on a {effective_rating}-star rating."
        )
        return energy

    def _calculate_microwave(self, profile_data: Dict, assumptions: list[str]) -> float:
        if profile_data.get('has_microwave') != 1:
            assumptions.append("No microwave present, microwave consumption set to 0 kWh/day.")
            return 0.0

        hours = 1.0
        power_kw = 1.2
        energy = power_kw * hours

        assumptions.append(
            f"Microwave energy assumed at {power_kw:.1f} kW for {hours:.1f} hour/day."
        )
        return energy

    def _calculate_dishwasher(self, profile_data: Dict, assumptions: list[str]) -> float:
        if profile_data.get('has_dishwasher') != 1:
            assumptions.append("No dishwasher present, dishwasher consumption set to 0 kWh/day.")
            return 0.0

        cycles_week = float(profile_data.get('dishwasher_cycles_per_week', 0.0))
        energy_per_cycle = 1.5
        energy = cycles_week / 7.0 * energy_per_cycle

        assumptions.append(
            f"Dishwasher energy assumed at {energy_per_cycle:.1f} kWh per cycle, averaged over {cycles_week:.1f} cycles/week."
        )
        return energy

    def _calculate_washing_machine(self, profile_data: Dict, assumptions: list[str]) -> float:
        if profile_data.get('has_washing_machine') != 1:
            assumptions.append("No washing machine present, washing machine consumption set to 0 kWh/day.")
            return 0.0

        machine_type = profile_data.get('washing_machine_type')
        cycles_week = float(profile_data.get('washing_cycles_per_week', 0.0))
        energy_per_cycle = 1.3 if machine_type == 'Top Load' else 0.9
        energy = cycles_week / 7.0 * energy_per_cycle

        assumptions.append(
            f"Washing machine energy assumed at {energy_per_cycle:.1f} kWh per cycle for a {machine_type} machine."
        )
        return energy

    def _calculate_tvs(self, profile_data: Dict, assumptions: list[str]) -> float:
        num_tvs = int(profile_data.get('num_tvs', 0))
        if num_tvs <= 0:
            assumptions.append("No TVs present, TV consumption set to 0 kWh/day.")
            return 0.0

        size = float(profile_data.get('tv_screen_size_inch', 40.0))
        hours = float(profile_data.get('tv_usage_hrs_per_day', 0.0))
        power_kw = self._tv_power_kw(size)
        energy = num_tvs * power_kw * hours

        assumptions.append(
            f"TV energy assumed at {power_kw:.2f} kW per unit for {hours:.1f} hours/day based on a {size:.0f}-inch screen."
        )
        return energy

    def _tv_power_kw(self, size_inch: float) -> float:
        if size_inch <= 32:
            return 0.06
        if size_inch <= 43:
            return 0.09
        if size_inch <= 55:
            return 0.14
        return 0.18

    def _calculate_computers(self, profile_data: Dict, assumptions: list[str]) -> float:
        num_computers = int(profile_data.get('num_computers', 0))
        if num_computers <= 0:
            assumptions.append("No computers present, computer consumption set to 0 kWh/day.")
            return 0.0

        hours = float(profile_data.get('computer_usage_hrs_per_day', 0.0))
        power_kw = 0.12
        energy = num_computers * power_kw * hours

        assumptions.append(
            f"Computer energy assumed at {power_kw*1000:.0f} W per device for {hours:.1f} hours/day."
        )
        return energy

    def _round_kwh(self, value: float) -> float:
        return round(max(value, 0.0), 3)

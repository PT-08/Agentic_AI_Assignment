import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class CalculateGridDrawAndExpenseAgent:
    def __init__(self):
        self.agent_name = "Agent_CalculateGridDrawAndExpense"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Estimate daily net grid draw and monthly bill from available solar capacity."""
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}
        assumptions: list[str] = []

        try:
            base_kwh = float(profile_data.get('daily_energy_consumption_kWh', 0.0))
            if 'daily_energy_consumption_kWh' not in profile_data:
                assumptions.append(
                    "Daily energy consumption was missing from state; assumed 0 kWh/day for net grid draw."
                )

            has_solar = int(profile_data.get('has_solar_panels', 0)) == 1
            solar_capacity = float(profile_data.get('solar_capacity_kWp', 0.0))

            if has_solar and solar_capacity > 0.0:
                solar_generation = self._estimate_solar_generation_kwh_per_day(solar_capacity, assumptions)
            elif has_solar:
                assumptions.append(
                    "Solar panels were reported, but solar capacity was missing or zero; assumed 0 kWh/day solar generation."
                )
                solar_generation = 0.0
            else:
                assumptions.append(
                    "No solar panels installed; net grid draw equals daily consumption."
                )
                solar_generation = 0.0

            net_grid_draw = max(base_kwh - solar_generation, 0.0)
            monthly_bill = net_grid_draw * 30.0

            profile_data['solar_generation_kWh_per_day'] = self._round_kwh(solar_generation)
            profile_data['net_grid_draw_kWh_per_day'] = self._round_kwh(net_grid_draw)
            profile_data['monthly_grid_bill_kWh'] = self._round_kwh(monthly_bill)
            profile_data['energy_assumptions'] = profile_data.get('energy_assumptions', []) + assumptions
            profile_data['grid_draw_assumptions'] = assumptions

            state['profile_data'] = profile_data
            state['workflow_stage'] = 'Complete'
            state['messages'].append("[SUCCESS] Net grid draw and monthly bill estimated from solar offset.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append("[ERROR] {}".format(str(e)))
            state['workflow_stage'] = 'Error'

        return state

    def _estimate_solar_generation_kwh_per_day(self, solar_capacity_kWp: float, assumptions: list[str]) -> float:
        peak_sun_hours = 6.5
        generation = solar_capacity_kWp * peak_sun_hours
        assumptions.append(
            f"Solar generation estimated from {peak_sun_hours:.1f} peak sun hours per day at 1 kW per kWp for {solar_capacity_kWp:.2f} kWp capacity."
        )
        return generation

    def _round_kwh(self, value: float) -> float:
        return round(max(value, 0.0), 3)

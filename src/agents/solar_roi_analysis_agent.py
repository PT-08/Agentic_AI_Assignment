import sys
from pathlib import Path
from typing import Dict, Any

import pandas as pd

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class SolarROIAnalysisAgent:
    def __init__(self):
        self.agent_name = "Agent_SolarROIAnalysis"
        self.scenario_sizes = [1.0, 3.0, 5.0, 10.0]
        self.capital_cost_per_kwp = 700.0
        self.default_cost_per_kwh = 1.0
        self.annual_days = 365

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}
        assumptions: list[str] = []

        if not profile_data:
            error = "No profile data found in state.profile_data."
            state['errors'].append(error)
            state['messages'].append(f"[ERROR] {error}")
            state['workflow_stage'] = 'Error'
            return state

        try:
            base_daily_kwh, source = self._base_daily_energy(profile_data, assumptions)
            cost_per_kwh = self._estimate_cost_per_kwh(profile_data, assumptions)
            sun_hours = self._solar_irradiance_hours(profile_data.get('climate_zone', ''), assumptions)

            scenarios = self._evaluate_scenarios(base_daily_kwh, cost_per_kwh, sun_hours)
            summary = self._build_summary(scenarios, base_daily_kwh, source, cost_per_kwh)

            profile_data['solar_roi_analysis'] = summary
            profile_data['energy_assumptions'] = profile_data.get('energy_assumptions', []) + assumptions
            state['profile_data'] = profile_data
            state['workflow_stage'] = 'Complete'
            state['messages'].append("[SUCCESS] Solar ROI analysis completed.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append(f"[ERROR] {str(e)}")
            state['workflow_stage'] = 'Error'

        return state

    def _base_daily_energy(self, profile_data: Dict[str, Any], assumptions: list[str]) -> tuple[float, str]:
        if 'adjusted_daily_energy_kWh' in profile_data:
            assumptions.append(
                "Using adjusted daily energy consumption from state because climate and insulation adjustments were applied."
            )
            return float(profile_data.get('adjusted_daily_energy_kWh', 0.0)), 'adjusted_daily_energy_kWh'

        if 'daily_energy_consumption_kWh' in profile_data:
            assumptions.append(
                "Using gross daily energy consumption from state because adjusted consumption was not available."
            )
            return float(profile_data.get('daily_energy_consumption_kWh', 0.0)), 'daily_energy_consumption_kWh'

        assumptions.append(
            "Daily energy consumption was missing from state; assumed 0 kWh/day for ROI calculation."
        )
        return 0.0, 'assumed'

    def _estimate_cost_per_kwh(self, profile_data: Dict[str, Any], assumptions: list[str]) -> float:
        net_draw = float(profile_data.get('net_grid_draw_kWh_per_day', 0.0))
        monthly_bill = float(profile_data.get('monthly_grid_bill_kWh', 0.0))

        if net_draw > 0 and monthly_bill > 0:
            derived_cost = monthly_bill / (net_draw * 30.0)
            if derived_cost > 0:
                assumptions.append(
                    f"Estimated grid cost from state data as {derived_cost:.2f} per kWh."
                )
                return derived_cost

        assumptions.append(
            f"Could not derive grid cost from state data; assuming {self.default_cost_per_kwh:.2f} per kWh."
        )
        return self.default_cost_per_kwh

    def _solar_irradiance_hours(self, climate_zone: str, assumptions: list[str]) -> float:
        zone = str(climate_zone or '').strip().lower()
        mapping = {
            'hot & dry': 5.5,
            'hot & humid': 5.0,
            'temperate': 4.5,
            'composite': 4.8,
            'cold': 3.8,
        }
        peak_hours = mapping.get(zone, 4.5)
        if zone in mapping:
            assumptions.append(
                f"Solar generation is estimated with {peak_hours:.1f} peak sun hours per day for climate zone '{climate_zone}'."
            )
        else:
            assumptions.append(
                "Climate zone was unknown or missing; assumed 4.5 peak sun hours per day for solar generation."
            )
        return peak_hours

    def _evaluate_scenarios(self, base_daily: float, cost_per_kwh: float, sun_hours: float) -> pd.DataFrame:
        rows = []
        annual_consumption = base_daily * self.annual_days

        for capacity in self.scenario_sizes:
            daily_generation = capacity * sun_hours
            annual_generation = daily_generation * self.annual_days
            annual_offset = min(annual_generation, annual_consumption)
            annual_savings = annual_offset * cost_per_kwh
            capital_cost = capacity * self.capital_cost_per_kwp
            payback_years = capital_cost / annual_savings if annual_savings > 0 else float('inf')
            net_savings_25y = annual_savings * 25 - capital_cost

            rows.append({
                'solar_capacity_kWp': capacity,
                'daily_generation_kWh': self._round_value(daily_generation),
                'annual_generation_kWh': self._round_value(annual_generation),
                'annual_energy_offset_kWh': self._round_value(annual_offset),
                'annual_savings': self._round_value(annual_savings),
                'capital_cost': self._round_value(capital_cost),
                'payback_years': round(payback_years, 2) if payback_years != float('inf') else None,
                'net_savings_25y': self._round_value(net_savings_25y)
            })

        return pd.DataFrame(rows)

    def _build_summary(self, scenarios: pd.DataFrame, base_daily: float, source: str, cost_per_kwh: float) -> Dict[str, Any]:
        return {
            'base_energy_source': source,
            'base_daily_energy_kWh': self._round_value(base_daily),
            'grid_cost_per_kWh': self._round_value(cost_per_kwh),
            'capital_cost_per_kWp': self._round_value(self.capital_cost_per_kwp),
            'scenarios': scenarios.to_dict(orient='records'),
            'assumptions': [
                'Solar ROI is based on estimated annual generation from peak sun hours.',
                'Capital cost is assumed constant per kWp and does not include maintenance or financing.',
                '25-year savings assume stable grid tariffs and no system degradation.'
            ]
        }

    def _round_value(self, value: float) -> float:
        return round(max(value, 0.0), 2)

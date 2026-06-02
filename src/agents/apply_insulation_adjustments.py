import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class ApplyInsulationAdjustmentsAgent:
    def __init__(self):
        self.agent_name = "Agent_ApplyInsulationAdjustments"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        """Apply climate and insulation adjustments to gross energy consumption."""
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}
        assumptions: list[str] = []

        try:
            base_kwh = float(profile_data.get('daily_energy_consumption_kWh', 0.0))
            if 'daily_energy_consumption_kWh' not in profile_data:
                assumptions.append(
                    "Gross energy consumption was missing from state; assumed 0 kWh/day for adjustments."
                )

            climate_zone = str(profile_data.get('climate_zone', '')).strip()
            insulation_quality = str(profile_data.get('insulation_quality', '')).strip()

            climate_factor = self._climate_factor(climate_zone, assumptions)
            insulation_factor = self._insulation_factor(insulation_quality, assumptions)

            adjusted_kwh = base_kwh * climate_factor * insulation_factor

            profile_data['adjusted_daily_energy_kWh'] = self._round_kwh(adjusted_kwh)
            profile_data['energy_adjustment_factors'] = {
                'climate_factor': self._round_kwh(climate_factor),
                'insulation_factor': self._round_kwh(insulation_factor),
                'combined_factor': self._round_kwh(climate_factor * insulation_factor),
            }
            profile_data['energy_adjustment_climate_zone'] = climate_zone or 'Temperate'
            profile_data['energy_adjustment_insulation_quality'] = insulation_quality or 'Average'
            profile_data['energy_assumptions'] = profile_data.get('energy_assumptions', []) + assumptions

            state['profile_data'] = profile_data
            state['workflow_stage'] = 'Complete'
            state['messages'].append("[SUCCESS] Climate and insulation adjustments applied to gross energy consumption.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append("[ERROR] {}".format(str(e)))
            state['workflow_stage'] = 'Error'

        return state

    def _climate_factor(self, climate_zone: str, assumptions: list[str]) -> float:
        zone = climate_zone.lower()
        mapping = {
            'hot & dry': 1.05,
            'hot & humid': 1.10,
            'temperate': 1.00,
            'composite': 1.02,
            'cold': 1.15,
        }

        if zone in mapping:
            assumptions.append(
                f"Climate zone '{climate_zone}' adjusts gross energy by a factor of {mapping[zone]:.2f}."
            )
            return mapping[zone]

        assumptions.append(
            "Climate zone was unknown or missing; assumed Temperate with a factor of 1.00."
        )
        return mapping['temperate']

    def _insulation_factor(self, insulation_quality: str, assumptions: list[str]) -> float:
        quality = insulation_quality.lower()
        mapping = {
            'excellent': 0.90,
            'good': 0.95,
            'average': 1.00,
            'poor': 1.10,
        }

        if quality in mapping:
            assumptions.append(
                f"Insulation quality '{insulation_quality}' adjusts energy by a factor of {mapping[quality]:.2f}."
            )
            return mapping[quality]

        assumptions.append(
            "Insulation quality was unknown or missing; assumed Average with a factor of 1.00."
        )
        return mapping['average']

    def _round_kwh(self, value: float) -> float:
        return round(max(value, 0.0), 3)

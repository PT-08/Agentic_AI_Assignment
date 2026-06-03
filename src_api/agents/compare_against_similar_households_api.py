import pandas as pd
from pathlib import Path
from typing import Any, Dict, List

from langgraph.graph import END
from langgraph.types import Command

from src_api.state import HouseholdProfileState


class APICompareAgainstSimilarHouseholdsAgent:
    def __init__(self):
        self.agent_name = "CompareAgainstSimilarHouseholdsAgent"
        self.comparison_columns = [
            'house_type', 'num_bedrooms', 'floor_area_sqft', 'num_floors',
            'num_occupants', 'num_adults', 'num_children',
            'climate_zone', 'city_tier', 'insulation_quality',
            'window_type', 'roof_type', 'has_ac', 'num_ac_units',
            'ac_star_rating', 'ac_usage_hrs_per_day', 'num_ceiling_fans',
            'water_heater_type', 'water_heater_capacity_L',
            'water_heater_usage_hrs_per_day', 'has_refrigerator',
            'fridge_capacity_L', 'fridge_star_rating', 'has_microwave',
            'has_dishwasher', 'dishwasher_cycles_per_week',
            'has_washing_machine', 'washing_machine_type',
            'washing_cycles_per_week', 'has_dryer', 'num_tvs',
            'tv_screen_size_inch', 'tv_usage_hrs_per_day', 'num_computers',
            'computer_usage_hrs_per_day', 'has_solar_panels', 'solar_capacity_kWp',
            'has_battery_storage', 'battery_capacity_kWh'
        ]

        self.categorical_filters = [
            'house_type', 'climate_zone', 'city_tier',
            'insulation_quality', 'window_type', 'roof_type',
            'water_heater_type', 'washing_machine_type'
        ]

        self.numeric_features = [
            'num_bedrooms', 'floor_area_sqft', 'num_floors',
            'num_occupants', 'num_adults', 'num_children',
            'has_ac', 'num_ac_units', 'ac_star_rating',
            'ac_usage_hrs_per_day', 'num_ceiling_fans',
            'water_heater_capacity_L', 'water_heater_usage_hrs_per_day',
            'has_refrigerator', 'fridge_capacity_L', 'fridge_star_rating',
            'has_microwave', 'has_dishwasher', 'dishwasher_cycles_per_week',
            'has_washing_machine', 'washing_cycles_per_week', 'has_dryer',
            'num_tvs', 'tv_screen_size_inch', 'tv_usage_hrs_per_day',
            'num_computers', 'computer_usage_hrs_per_day',
            'has_solar_panels', 'solar_capacity_kWp',
            'has_battery_storage', 'battery_capacity_kWh'
        ]

    def process(self, state: HouseholdProfileState) -> Command:
        profile_data = state.get('profile_data') or {}
        messages = list(state.get('messages', []))
        errors = list(state.get('errors', []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            if not profile_data:
                raise ValueError("No profile data found in state.profile_data.")

            csv_path = Path(__file__).resolve().parents[2] / "household_energy_requirement.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Dataset not found at {csv_path}")

            dataset = pd.read_csv(csv_path)
            prepared = self._prepare_dataset(dataset)

            profile_series = self._extract_profile_series(profile_data)
            self._validate_profile(profile_series)

            matches = self._find_similar_households(prepared, profile_series)
            summary = self._build_summary(matches, profile_series)
            print("----------------",summary)
            updates['comparison_summary'] = summary
            updates['workflow_stage'] = 'Complete'
            messages.append('[SUCCESS] Similar household comparison completed.')
        except Exception as e:
            errors.append(str(e))
            messages.append(f'[ERROR] {e}')
            updates['workflow_stage'] = 'Error'

        updates['messages'] = messages
        updates['errors'] = errors
        return Command(update=updates, goto=self.route(updates))

    def _prepare_dataset(self, dataset: pd.DataFrame) -> pd.DataFrame:
        comparison_columns = self.comparison_columns + [
            'daily_energy_consumption_kWh', 'monthly_energy_consumption_kWh'
        ]
        missing_cols = [col for col in comparison_columns if col not in dataset.columns]
        if missing_cols:
            raise ValueError(f"Dataset is missing expected columns: {missing_cols}")

        subset = dataset[comparison_columns].copy()
        for col in self.numeric_features:
            if col in subset.columns:
                subset[col] = pd.to_numeric(subset[col], errors='coerce').fillna(0)

        for cat_col in self.categorical_filters:
            if cat_col in subset.columns:
                subset[cat_col] = subset[cat_col].astype(str).fillna('Unknown')

        return subset

    def _extract_profile_series(self, profile_data: Dict[str, Any]) -> Any:
        profile = {col: profile_data.get(col, None) for col in self.comparison_columns}
        if profile.get('ac_star_rating') is None and profile_data.get('ac_star_rating') is not None:
            profile['ac_star_rating'] = profile_data.get('ac_star_rating')

        numeric_values = {col: float(profile.get(col, 0) or 0) for col in self.numeric_features}
        categorical_values = {col: str(profile.get(col)).strip() for col in self.categorical_filters if profile.get(col) is not None}
        if 'daily_energy_consumption_kWh' in profile_data:
            numeric_values['daily_energy_consumption_kWh'] = float(profile_data.get('daily_energy_consumption_kWh') or 0)
        if 'monthly_energy_consumption_kWh' in profile_data:
            numeric_values['monthly_energy_consumption_kWh'] = float(profile_data.get('monthly_energy_consumption_kWh') or 0)
        return pd.Series({**numeric_values, **categorical_values})

    def _validate_profile(self, profile_series: Any) -> None:
        required = ['house_type', 'climate_zone', 'city_tier']
        missing = [name for name in required if not profile_series.get(name)]
        if missing:
            raise ValueError(f"Profile must include values for {', '.join(missing)} to compare similar households.")

    def _find_similar_households(self, dataset: Any, profile_series: Any) -> Any:
        candidates = dataset.copy()
        for cat_col in self.categorical_filters:
            if cat_col in profile_series and profile_series[cat_col] and profile_series[cat_col] != 'None':
                candidates = candidates[candidates[cat_col].str.lower() == str(profile_series[cat_col]).lower()]

        if candidates.empty and 'house_type' in dataset.columns and 'climate_zone' in dataset.columns and 'city_tier' in dataset.columns:
            candidates = dataset[(dataset['house_type'].str.lower() == str(profile_series['house_type']).lower()) &
                                 (dataset['climate_zone'].str.lower() == str(profile_series['climate_zone']).lower()) &
                                 (dataset['city_tier'].str.lower() == str(profile_series['city_tier']).lower())]

        if candidates.empty:
            candidates = dataset.copy()

        distance = pd.Series(0.0, index=candidates.index)
        for feature in self.numeric_features:
            if feature in candidates.columns:
                target_value = float(profile_series.get(feature, 0) or 0)
                distance += (candidates[feature].astype(float).fillna(0) - target_value).abs()

        candidates = candidates.assign(similarity_distance=distance)
        candidates = candidates.sort_values(by='similarity_distance', ascending=True)
        return candidates.head(5)

    def _build_summary(self, matches: Any, profile_series: Any) -> Dict[str, Any]:
        top_matches = []
        for _, row in matches.reset_index(drop=True).iterrows():
            top_matches.append({
                'house_type': row['house_type'],
                'num_bedrooms': int(row['num_bedrooms']),
                'floor_area_sqft': float(row['floor_area_sqft']),
                'num_occupants': int(row['num_occupants']),
                'climate_zone': row['climate_zone'],
                'city_tier': row['city_tier'],
                'daily_energy_consumption_kWh': float(row['daily_energy_consumption_kWh']),
                'monthly_energy_consumption_kWh': float(row['monthly_energy_consumption_kWh']),
                'similarity_distance': float(row['similarity_distance'])
            })

        average_daily = float(matches['daily_energy_consumption_kWh'].mean()) if not matches.empty else 0.0
        average_monthly = float(matches['monthly_energy_consumption_kWh'].mean()) if not matches.empty else 0.0
        current_daily = profile_series.get('daily_energy_consumption_kWh')
        current_monthly = profile_series.get('monthly_energy_consumption_kWh')

        return {
            'comparison_columns': self.comparison_columns,
            'similar_households_found': len(matches),
            'top_matches': top_matches,
            'peer_average_daily_kWh': average_daily,
            'peer_average_monthly_kWh': average_monthly,
            'target_daily_kWh': float(current_daily) if current_daily is not None else None,
            'target_monthly_kWh': float(current_monthly) if current_monthly is not None else None,
            'notes': (
                "The comparison uses occupancy, appliance, building envelope, and renewable asset "
                "features from the profile to rank households with similar energy use patterns."
            )
        }

    def route(self, state: HouseholdProfileState):
        if state.get('errors'):
            return END
        return END

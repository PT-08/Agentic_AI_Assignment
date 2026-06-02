"""
Utility functions for household energy data handling.
Simplified for incremental development.
"""

import pandas as pd
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path


# Valid values for normalization
VALID_HOUSE_TYPES = [
    "Apartment", "Villa", "Bungalow", "Townhouse", "Penthouse"
]

VALID_CLIMATE_ZONES = [
    "Hot & Dry",
    "Hot & Humid",
    "Composite",
    "Temperate",
    "Cold"
]

VALID_CITY_TIERS = [
    "Tier 1",
    "Tier 2",
    "Tier 3"
]


def load_household_data(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Load household energy requirement dataset."""
    if csv_path is None:
        base_dir = Path(__file__).parent.parent
        csv_path = os.path.join(base_dir, "household_energy_requirement.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")
    
    return pd.read_csv(csv_path)


def normalize_input(value: str, valid_values: List[str]) -> Optional[str]:
    """
    Normalize user input to match dataset values.
    Examples: "apt" -> "Apartment", "hot dry" -> "Hot & Dry"
    """
    if not value:
        return None
    
    value_lower = str(value).lower().strip()
    
    for valid in valid_values:
        if valid.lower() == value_lower or valid.lower().replace(" ", "") == value_lower.replace(" ", ""):
            return valid
    
    return None



"""
NEXUS GRID — Carbon Intensity Profiles
Real-world hourly carbon intensity (kgCO2/kWh) for different grid regions.

Sources / basis:
  - UK: National Grid ESO 2023 data (avg winter)
  - US East: EIA 2023 PJM hourly average
  - India West: CEA 2023 Maharashtra grid data (coal-heavy, solar midday dip)
  - India South: CEA 2023 TNEB (higher solar penetration)
  - Custom: flat 0.4 placeholder, overridden by user upload
"""

from typing import Dict, List

# Each profile = 24 hourly values (index 0 = midnight, index 12 = noon)
CARBON_PROFILES: Dict[str, List[float]] = {

    "uk_national_grid": [
        0.22, 0.21, 0.20, 0.19, 0.19, 0.20,   # 00-05  (low demand, wind)
        0.24, 0.28, 0.30, 0.29, 0.27, 0.24,   # 06-11  (morning ramp up)
        0.21, 0.19, 0.18, 0.19, 0.22, 0.26,   # 12-17  (solar peak, then evening)
        0.30, 0.32, 0.30, 0.28, 0.26, 0.23,   # 18-23  (evening peak)
    ],

    "us_eastern_pjm": [
        0.38, 0.36, 0.35, 0.34, 0.34, 0.35,   # 00-05
        0.38, 0.43, 0.47, 0.45, 0.42, 0.39,   # 06-11
        0.36, 0.33, 0.31, 0.32, 0.36, 0.41,   # 12-17
        0.46, 0.49, 0.47, 0.44, 0.42, 0.40,   # 18-23
    ],

    "india_west_maharashtra": [
        0.72, 0.70, 0.68, 0.67, 0.67, 0.68,   # 00-05  (coal-heavy overnight)
        0.74, 0.80, 0.84, 0.79, 0.72, 0.65,   # 06-11  (morning peak, then solar)
        0.58, 0.54, 0.52, 0.55, 0.62, 0.70,   # 12-17  (solar midday dip)
        0.78, 0.83, 0.81, 0.78, 0.76, 0.74,   # 18-23  (evening coal peak)
    ],

    "india_south_tneb": [
        0.58, 0.56, 0.54, 0.53, 0.53, 0.54,   # 00-05
        0.58, 0.63, 0.66, 0.62, 0.56, 0.49,   # 06-11  (higher solar penetration)
        0.43, 0.40, 0.38, 0.40, 0.46, 0.54,   # 12-17
        0.62, 0.66, 0.63, 0.60, 0.58, 0.56,   # 18-23
    ],

    "custom": [
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,   # flat placeholder
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,
    ],
}

# Human-readable labels for the frontend dropdown
PROFILE_LABELS: Dict[str, str] = {
    "uk_national_grid":       "🇬🇧 UK National Grid",
    "us_eastern_pjm":         "🇺🇸 US Eastern (PJM)",
    "india_west_maharashtra":  "🇮🇳 India West (Maharashtra)",
    "india_south_tneb":        "🇮🇳 India South (TNEB)",
    "custom":                  "⚙️ Custom (upload your own)",
}


def get_profile(name: str) -> List[float]:
    """Return the 24-hour carbon profile. Falls back to 'custom' if unknown."""
    return CARBON_PROFILES.get(name, CARBON_PROFILES["custom"])


def list_profiles() -> Dict[str, str]:
    """Return all available profile keys + human labels."""
    return PROFILE_LABELS

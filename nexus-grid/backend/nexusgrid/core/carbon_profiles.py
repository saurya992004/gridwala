"""
NEXUS GRID - Carbon intensity profiles.
Real-world inspired hourly carbon intensity (kgCO2/kWh) for different regions.
"""

from typing import Dict, List


CARBON_PROFILES: Dict[str, List[float]] = {
    "uk_national_grid": [
        0.22, 0.21, 0.20, 0.19, 0.19, 0.20,
        0.24, 0.28, 0.30, 0.29, 0.27, 0.24,
        0.21, 0.19, 0.18, 0.19, 0.22, 0.26,
        0.30, 0.32, 0.30, 0.28, 0.26, 0.23,
    ],
    "us_eastern_pjm": [
        0.38, 0.36, 0.35, 0.34, 0.34, 0.35,
        0.38, 0.43, 0.47, 0.45, 0.42, 0.39,
        0.36, 0.33, 0.31, 0.32, 0.36, 0.41,
        0.46, 0.49, 0.47, 0.44, 0.42, 0.40,
    ],
    "india_west_maharashtra": [
        0.72, 0.70, 0.68, 0.67, 0.67, 0.68,
        0.74, 0.80, 0.84, 0.79, 0.72, 0.65,
        0.58, 0.54, 0.52, 0.55, 0.62, 0.70,
        0.78, 0.83, 0.81, 0.78, 0.76, 0.74,
    ],
    "india_south_tneb": [
        0.58, 0.56, 0.54, 0.53, 0.53, 0.54,
        0.58, 0.63, 0.66, 0.62, 0.56, 0.49,
        0.43, 0.40, 0.38, 0.40, 0.46, 0.54,
        0.62, 0.66, 0.63, 0.60, 0.58, 0.56,
    ],
    "custom": [
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,
        0.40, 0.40, 0.40, 0.40, 0.40, 0.40,
    ],
}


PROFILE_LABELS: Dict[str, str] = {
    "uk_national_grid": "UK National Grid",
    "us_eastern_pjm": "US Eastern (PJM)",
    "india_west_maharashtra": "India West (Maharashtra)",
    "india_south_tneb": "India South (TNEB)",
    "custom": "Custom (upload your own)",
}


def get_profile(name: str) -> List[float]:
    return CARBON_PROFILES.get(name, CARBON_PROFILES["custom"])


def list_profiles() -> Dict[str, str]:
    return PROFILE_LABELS

"""Curated fallback catalog for offline and demo-friendly geo resolution."""

from __future__ import annotations

import re
from typing import Dict, List


CATALOG_LOCATIONS: List[Dict[str, object]] = [
    {
        "display_name": "London, England, United Kingdom",
        "latitude": 51.5072,
        "longitude": -0.1276,
        "country": "United Kingdom",
        "country_code": "gb",
        "state": "England",
        "city": "London",
        "locality": "London",
        "category": "place",
        "type": "city",
        "importance": 0.99,
    },
    {
        "display_name": "Manchester, England, United Kingdom",
        "latitude": 53.4808,
        "longitude": -2.2426,
        "country": "United Kingdom",
        "country_code": "gb",
        "state": "England",
        "city": "Manchester",
        "locality": "Manchester",
        "category": "place",
        "type": "city",
        "importance": 0.91,
    },
    {
        "display_name": "New York City, New York, United States",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "country": "United States",
        "country_code": "us",
        "state": "New York",
        "city": "New York City",
        "locality": "New York City",
        "category": "place",
        "type": "city",
        "importance": 0.99,
    },
    {
        "display_name": "Boston, Massachusetts, United States",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "country": "United States",
        "country_code": "us",
        "state": "Massachusetts",
        "city": "Boston",
        "locality": "Boston",
        "category": "place",
        "type": "city",
        "importance": 0.9,
    },
    {
        "display_name": "San Francisco, California, United States",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "country": "United States",
        "country_code": "us",
        "state": "California",
        "city": "San Francisco",
        "locality": "San Francisco",
        "category": "place",
        "type": "city",
        "importance": 0.92,
    },
    {
        "display_name": "Austin, Texas, United States",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "country": "United States",
        "country_code": "us",
        "state": "Texas",
        "city": "Austin",
        "locality": "Austin",
        "category": "place",
        "type": "city",
        "importance": 0.84,
    },
    {
        "display_name": "Mumbai, Maharashtra, India",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "country": "India",
        "country_code": "in",
        "state": "Maharashtra",
        "city": "Mumbai",
        "locality": "Mumbai",
        "category": "place",
        "type": "city",
        "importance": 0.97,
    },
    {
        "display_name": "Bengaluru, Karnataka, India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "country": "India",
        "country_code": "in",
        "state": "Karnataka",
        "city": "Bengaluru",
        "locality": "Bengaluru",
        "category": "place",
        "type": "city",
        "importance": 0.94,
    },
    {
        "display_name": "Chennai, Tamil Nadu, India",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "country": "India",
        "country_code": "in",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "locality": "Chennai",
        "category": "place",
        "type": "city",
        "importance": 0.93,
    },
    {
        "display_name": "Singapore",
        "latitude": 1.3521,
        "longitude": 103.8198,
        "country": "Singapore",
        "country_code": "sg",
        "state": "Singapore",
        "city": "Singapore",
        "locality": "Singapore",
        "category": "place",
        "type": "city-state",
        "importance": 0.95,
    },
    {
        "display_name": "Nairobi, Nairobi County, Kenya",
        "latitude": -1.2921,
        "longitude": 36.8219,
        "country": "Kenya",
        "country_code": "ke",
        "state": "Nairobi County",
        "city": "Nairobi",
        "locality": "Nairobi",
        "category": "place",
        "type": "city",
        "importance": 0.88,
    },
    {
        "display_name": "Sao Paulo, Sao Paulo, Brazil",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "country": "Brazil",
        "country_code": "br",
        "state": "Sao Paulo",
        "city": "Sao Paulo",
        "locality": "Sao Paulo",
        "category": "place",
        "type": "city",
        "importance": 0.94,
    },
]


def featured_catalog_locations(limit: int = 8) -> List[Dict[str, object]]:
    """Return a curated list of catalog locations for the atlas launcher."""
    safe_limit = max(1, min(limit, len(CATALOG_LOCATIONS)))
    return [dict(item) for item in CATALOG_LOCATIONS[:safe_limit]]


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def search_catalog(query: str, limit: int = 5) -> List[Dict[str, object]]:
    """Return the best catalog matches for a free-form location query."""
    q = _normalize(query)
    if not q:
        return []

    terms = [term for term in q.split() if term]
    scored: List[tuple[float, Dict[str, object]]] = []

    for item in CATALOG_LOCATIONS:
        haystack = _normalize(
            " ".join(
                str(item.get(field, ""))
                for field in ("display_name", "locality", "city", "state", "country")
            )
        )
        if not haystack:
            continue

        score = 0.0
        matched = False
        if haystack == q:
            score += 10.0
            matched = True
        if q in haystack:
            score += 5.0
            matched = True

        term_hits = sum(1.0 for term in terms if term in haystack)
        if term_hits:
            score += term_hits
            matched = True

        if matched:
            score += float(item.get("importance", 0.0))

        if matched:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [dict(item) for _, item in scored[: max(1, min(limit, 10))]]

"""Fixtures compartidas para los tests."""

import pytest


def _make_forecast(n_days: int = 3, **overrides) -> dict:
    """Construye un forecast dict minimo y valido, sobreescribible por clave."""
    base = {
        "dates": [f"2026-01-0{i + 1}" for i in range(n_days)],
        "temp_max": [25.0] * n_days,
        "temp_min": [10.0] * n_days,
        "precipitation": [0.0] * n_days,
        "precip_probability": [0.0] * n_days,
        "wind_speed": [10.0] * n_days,
        "wind_gusts": [15.0] * n_days,
        "wind_direction": [180.0] * n_days,
        "et0": [3.0] * n_days,
        "radiation": [20.0] * n_days,
        "sunrise": ["2026-01-01T07:00"] * n_days,
        "sunset": ["2026-01-01T20:00"] * n_days,
        "humidity_max": [60.0] * n_days,
        "humidity_min": [30.0] * n_days,
        "humidity_mean": [35.0] * n_days,
        "soil_moisture": [0.30] * n_days,
        "n_days": n_days,
    }
    base.update(overrides)
    return base


@pytest.fixture
def make_forecast():
    return _make_forecast

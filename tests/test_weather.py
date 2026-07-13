import pytest

from agro_alertas.weather import (
    _process,
    consecutive_dry_days,
    format_wind_direction,
    water_balance,
)


def _raw_response(n_days: int = 2) -> dict:
    dates = [f"2026-01-0{i + 1}" for i in range(n_days)]
    return {
        "daily": {
            "time": dates,
            "temperature_2m_max": [25.0] * n_days,
            "temperature_2m_min": [10.0] * n_days,
            "precipitation_sum": [0.0] * n_days,
            "precipitation_probability_max": [0.0] * n_days,
            "wind_speed_10m_max": [10.0] * n_days,
            "wind_gusts_10m_max": [15.0] * n_days,
            "wind_direction_10m_dominant": [180.0] * n_days,
            "et0_fao_evapotranspiration": [3.0] * n_days,
            "shortwave_radiation_sum": [20.0] * n_days,
            "sunrise": ["2026-01-01T07:00"] * n_days,
            "sunset": ["2026-01-01T20:00"] * n_days,
        },
        "hourly": {
            "time": [f"{d}T{h:02d}:00" for d in dates for h in range(24)],
            "relative_humidity_2m": [50.0 + h % 10 for _ in dates for h in range(24)],
            "soil_moisture_0_to_1cm": [0.2 for _ in dates for _ in range(24)],
            "soil_moisture_1_to_3cm": [0.25 for _ in dates for _ in range(24)],
            "soil_moisture_3_to_9cm": [0.3 for _ in dates for _ in range(24)],
        },
    }


def test_process_aggregates_hourly_humidity_into_daily_stats():
    result = _process(_raw_response())

    assert result["n_days"] == 2
    assert len(result["humidity_max"]) == 2
    assert result["humidity_max"][0] == 59.0
    assert result["humidity_min"][0] == 50.0


def test_process_averages_soil_moisture_layers():
    result = _process(_raw_response())
    assert result["soil_moisture"][0] == pytest.approx((0.2 + 0.25 + 0.3) / 3)


def test_format_wind_direction_handles_none_and_cardinal_points():
    assert format_wind_direction(None) == "—"
    assert format_wind_direction(0) == "N"
    assert format_wind_direction(180) == "S"


def test_water_balance_skips_missing_values():
    forecast = {"et0": [5.0, None], "precipitation": [2.0, 3.0]}
    assert water_balance(forecast) == [3.0, None]


def test_consecutive_dry_days_resets_on_rain():
    forecast = {"precipitation": [0.0, 0.5, 5.0, 0.0, 0.0]}
    assert consecutive_dry_days(forecast) == [1, 2, 0, 1, 2]

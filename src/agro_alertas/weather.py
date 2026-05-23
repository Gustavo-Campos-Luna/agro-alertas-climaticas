import requests
from datetime import datetime, date
import numpy as np
from agro_alertas.config import LOCATION, FORECAST_DAYS


def fetch_forecast() -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LOCATION["latitude"],
        "longitude": LOCATION["longitude"],
        "timezone": LOCATION["timezone"],
        "forecast_days": FORECAST_DAYS,
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
            "et0_fao_evapotranspiration",
            "shortwave_radiation_sum",
            "sunrise",
            "sunset",
        ]),
        "hourly": ",".join([
            "relative_humidity_2m",
            "soil_moisture_0_to_1cm",
            "soil_moisture_1_to_3cm",
            "soil_moisture_3_to_9cm",
        ]),
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    raw = response.json()

    return _process(raw)


def _process(raw: dict) -> dict:
    daily = raw["daily"]
    hourly = raw["hourly"]

    dates = daily["time"]
    n = len(dates)

    humidity_max, humidity_min, humidity_mean = [], [], []
    soil_moisture = []

    hourly_dates = [t[:10] for t in hourly["time"]]
    rh = hourly["relative_humidity_2m"]
    sm_0_1 = hourly.get("soil_moisture_0_to_1cm", [None] * len(rh))
    sm_1_3 = hourly.get("soil_moisture_1_to_3cm", [None] * len(rh))
    sm_3_9 = hourly.get("soil_moisture_3_to_9cm", [None] * len(rh))

    for d in dates:
        idxs = [i for i, hd in enumerate(hourly_dates) if hd == d]
        day_rh = [rh[i] for i in idxs if rh[i] is not None]
        humidity_max.append(max(day_rh) if day_rh else None)
        humidity_min.append(min(day_rh) if day_rh else None)
        humidity_mean.append(float(np.mean(day_rh)) if day_rh else None)

        sms = []
        for sm in [sm_0_1, sm_1_3, sm_3_9]:
            vals = [sm[i] for i in idxs if i < len(sm) and sm[i] is not None]
            sms.extend(vals)
        soil_moisture.append(float(np.mean(sms)) if sms else None)

    return {
        "dates": dates,
        "temp_max": daily["temperature_2m_max"],
        "temp_min": daily["temperature_2m_min"],
        "precipitation": daily["precipitation_sum"],
        "precip_probability": daily["precipitation_probability_max"],
        "wind_speed": daily["wind_speed_10m_max"],
        "wind_gusts": daily["wind_gusts_10m_max"],
        "wind_direction": daily["wind_direction_10m_dominant"],
        "et0": daily["et0_fao_evapotranspiration"],
        "radiation": daily["shortwave_radiation_sum"],
        "sunrise": daily["sunrise"],
        "sunset": daily["sunset"],
        "humidity_max": humidity_max,
        "humidity_min": humidity_min,
        "humidity_mean": humidity_mean,
        "soil_moisture": soil_moisture,
        "n_days": n,
    }


def format_wind_direction(degrees: float) -> str:
    if degrees is None:
        return "—"
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    idx = round(degrees / 45) % 8
    return dirs[idx]


def water_balance(forecast: dict) -> list[float]:
    return [
        (et - p) if et is not None and p is not None else None
        for et, p in zip(forecast["et0"], forecast["precipitation"])
    ]


def consecutive_dry_days(forecast: dict, threshold_mm: float = 1.0) -> list[int]:
    result = []
    count = 0
    for p in forecast["precipitation"]:
        if p is not None and p < threshold_mm:
            count += 1
        else:
            count = 0
        result.append(count)
    return result

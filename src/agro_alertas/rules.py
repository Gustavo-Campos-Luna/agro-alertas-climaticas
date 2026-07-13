from dataclasses import dataclass
from datetime import datetime

from agro_alertas.config import MONITORED_CROPS
from agro_alertas.crops_db import CROP_INFO, get_alert_rules

SEVERITY_ORDER = {"crítica": 0, "alta": 1, "media": 2, "baja": 3}


@dataclass
class Alert:
    crop: str
    crop_label: str
    crop_emoji: str
    day_index: int
    date_str: str
    alert_id: str
    label: str
    severity: str
    message: str


def evaluate(forecast: dict) -> list[Alert]:
    alerts = []

    for day_i, date_str in enumerate(forecast["dates"]):
        forecast_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        day_data = {
            "temp_max": forecast["temp_max"][day_i],
            "temp_min": forecast["temp_min"][day_i],
            "precipitation": forecast["precipitation"][day_i],
            "precip_probability": forecast["precip_probability"][day_i],
            "wind_speed": forecast["wind_speed"][day_i],
            "wind_gusts": forecast["wind_gusts"][day_i],
            "humidity_max": forecast["humidity_max"][day_i],
            "humidity_min": forecast["humidity_min"][day_i],
            "humidity_mean": forecast["humidity_mean"][day_i],
            "et0": forecast["et0"][day_i],
            "soil_moisture": forecast["soil_moisture"][day_i],
        }

        for crop in MONITORED_CROPS:
            rules = get_alert_rules(crop, forecast_date)
            info = CROP_INFO[crop]

            for rule in rules:
                try:
                    if rule["check"](day_data):
                        alerts.append(Alert(
                            crop=crop,
                            crop_label=info["label"],
                            crop_emoji=info["emoji"],
                            day_index=day_i,
                            date_str=date_str,
                            alert_id=rule["id"],
                            label=rule["label"],
                            severity=rule["severity"],
                            message=rule["message"](day_data),
                        ))
                except (TypeError, KeyError):
                    continue

    alerts.sort(key=lambda a: (SEVERITY_ORDER.get(a.severity, 99), a.day_index))
    return alerts


def alerts_by_crop(alerts: list[Alert]) -> dict[str, list[Alert]]:
    result: dict[str, list[Alert]] = {crop: [] for crop in MONITORED_CROPS}
    for alert in alerts:
        result[alert.crop].append(alert)
    return result


def overall_severity(alerts: list[Alert]) -> str:
    if not alerts:
        return "sin_alertas"
    top = min(alerts, key=lambda a: SEVERITY_ORDER.get(a.severity, 99))
    return top.severity


def format_date_es(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    months = ["ene", "feb", "mar", "abr", "may", "jun",
               "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{days[dt.weekday()]} {dt.day} {months[dt.month - 1]}"

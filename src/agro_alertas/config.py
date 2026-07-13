import os
from typing import TypedDict


class Location(TypedDict):
    name: str
    latitude: float
    longitude: float
    timezone: str
    altitude_m: int
    region: str


LOCATION: Location = {
    "name": os.getenv("LOCATION_NAME", "Chimbarongo, Colchagua"),
    "latitude": float(os.getenv("LOCATION_LATITUDE", "-34.7125")),
    "longitude": float(os.getenv("LOCATION_LONGITUDE", "-71.0434")),
    "timezone": os.getenv("LOCATION_TIMEZONE", "America/Santiago"),
    "altitude_m": int(os.getenv("LOCATION_ALTITUDE_M", "305")),
    "region": os.getenv(
        "LOCATION_REGION", "Región del Libertador General Bernardo O'Higgins"
    ),
}

MONITORED_CROPS = ["viña", "cerezos", "maíz", "trigo", "porotos"]

FORECAST_DAYS = 7

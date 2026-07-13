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
    "name": os.getenv("LOCATION_NAME", "Santiago"),
    "latitude": float(os.getenv("LOCATION_LATITUDE", "-33.4489")),
    "longitude": float(os.getenv("LOCATION_LONGITUDE", "-70.6693")),
    "timezone": os.getenv("LOCATION_TIMEZONE", "America/Santiago"),
    "altitude_m": int(os.getenv("LOCATION_ALTITUDE_M", "570")),
    "region": os.getenv("LOCATION_REGION", "Región Metropolitana de Santiago"),
}

MONITORED_CROPS = ["viña", "cerezos", "maíz", "trigo", "porotos"]

FORECAST_DAYS = 7

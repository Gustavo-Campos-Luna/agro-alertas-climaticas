import importlib
import os


def test_location_defaults_when_no_env(monkeypatch):
    for var in (
        "LOCATION_NAME",
        "LOCATION_LATITUDE",
        "LOCATION_LONGITUDE",
        "LOCATION_TIMEZONE",
        "LOCATION_ALTITUDE_M",
        "LOCATION_REGION",
    ):
        monkeypatch.delenv(var, raising=False)

    from agro_alertas import config

    importlib.reload(config)

    assert config.LOCATION["name"] == "Santiago"
    assert config.LOCATION["latitude"] == -33.4489
    assert config.LOCATION["timezone"] == "America/Santiago"


def test_location_overridden_by_env(monkeypatch):
    monkeypatch.setenv("LOCATION_NAME", "Predio de prueba")
    monkeypatch.setenv("LOCATION_LATITUDE", "-33.45")
    monkeypatch.setenv("LOCATION_LONGITUDE", "-70.66")

    from agro_alertas import config

    importlib.reload(config)

    assert config.LOCATION["name"] == "Predio de prueba"
    assert config.LOCATION["latitude"] == -33.45
    assert config.LOCATION["longitude"] == -70.66

    # Restaura el modulo a su estado por defecto para no afectar otros tests.
    for var in ("LOCATION_NAME", "LOCATION_LATITUDE", "LOCATION_LONGITUDE"):
        monkeypatch.delenv(var, raising=False)
    importlib.reload(config)
    os.environ.pop("LOCATION_NAME", None)

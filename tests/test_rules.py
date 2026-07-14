from agro_alertas.rules import (
    alerts_by_crop,
    evaluate,
    format_date_es,
    overall_severity,
)


def test_no_alerts_on_favorable_forecast(make_forecast):
    forecast = make_forecast()
    alerts = evaluate(forecast)
    assert alerts == []
    assert overall_severity(alerts) == "sin_alertas"


def test_critical_frost_alert_for_vina_and_cerezos(make_forecast):
    forecast = make_forecast(temp_min=[-1.0, -1.0, -1.0])
    alerts = evaluate(forecast)

    assert any(a.crop == "viña" and a.alert_id == "helada_critica" for a in alerts)
    assert overall_severity(alerts) == "crítica"


def test_alerts_are_sorted_by_severity_then_day(make_forecast):
    forecast = make_forecast(
        n_days=2,
        temp_min=[5.0, -1.0],  # dia 0: sin riesgo de helada, dia 1: helada critica
    )
    alerts = evaluate(forecast)

    assert alerts[0].severity == "crítica"
    assert alerts[0].day_index == 1


def test_alerts_by_crop_includes_every_monitored_crop(make_forecast):
    forecast = make_forecast()
    grouped = alerts_by_crop(evaluate(forecast))

    assert set(grouped.keys()) == {"viña", "cerezos", "maíz", "trigo", "porotos"}
    assert all(isinstance(v, list) for v in grouped.values())


def test_botrytis_alert_requires_both_humidity_and_rain(make_forecast):
    only_humid = make_forecast(humidity_max=[90.0], precipitation=[0.0], n_days=1)
    only_rain = make_forecast(humidity_max=[50.0], precipitation=[5.0], n_days=1)
    both = make_forecast(humidity_max=[90.0], precipitation=[5.0], n_days=1)

    assert not any(a.alert_id == "botrytis" for a in evaluate(only_humid))
    assert not any(a.alert_id == "botrytis" for a in evaluate(only_rain))
    assert any(a.alert_id == "botrytis" for a in evaluate(both))


def test_format_date_es_returns_spanish_abbreviation():
    assert format_date_es("2026-01-01") == "Jue 1 ene"

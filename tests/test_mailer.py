import pytest

from agro_alertas.mailer import _md_to_html, build_html, send_email
from agro_alertas.rules import evaluate


def test_md_to_html_converts_headings_and_bold():
    html = _md_to_html("## Titulo\n**importante** y *cursiva*")
    assert "font-weight:700" in html
    assert "<strong>importante</strong>" in html
    assert "<em>cursiva</em>" in html


def test_build_html_smoke_test_with_and_without_alerts(make_forecast):
    forecast = make_forecast()
    html_no_alerts = build_html(forecast, [], "Sin novedad.", "")
    assert "<!DOCTYPE html>" in html_no_alerts
    assert "SIN ALERTAS" in html_no_alerts

    forecast_frost = make_forecast(temp_min=[-1.0] * len(forecast["dates"]))
    alerts = evaluate(forecast_frost)
    html_with_alerts = build_html(forecast_frost, alerts, "Riesgo de helada.", "")
    assert "ALERTA CRÍTICA" in html_with_alerts


def test_send_email_raises_without_credentials(monkeypatch, make_forecast):
    for var in ("EMAIL_SENDER", "EMAIL_PASSWORD", "EMAIL_RECIPIENTS"):
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValueError, match="Faltan variables"):
        send_email(make_forecast(), [], "", "")

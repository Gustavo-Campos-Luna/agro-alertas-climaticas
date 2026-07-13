from agro_alertas.ai_analysis import _fallback_analysis, generate_analysis
from agro_alertas.rules import evaluate


def test_fallback_analysis_without_alerts():
    assert "Sin alertas críticas" in _fallback_analysis([])


def test_fallback_analysis_mentions_critical_count(make_forecast):
    forecast = make_forecast(n_days=2, temp_min=[-1.0, -1.0])
    alerts = evaluate(forecast)
    text = _fallback_analysis(alerts)
    assert "críticas" in text


def test_generate_analysis_falls_back_without_api_key(monkeypatch, make_forecast):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    forecast = make_forecast()
    result = generate_analysis(forecast, [])
    assert "Sin alertas críticas" in result

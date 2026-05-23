import os
from groq import Groq
from agro_alertas.rules import Alert, format_date_es
from agro_alertas.config import LOCATION, MONITORED_CROPS
from agro_alertas.crops_db import CROP_INFO


def build_weather_summary(forecast: dict) -> str:
    lines = ["Pronóstico 7 días — " + LOCATION["name"]]
    lines.append(f"{'Fecha':<12} {'TMax':>6} {'TMin':>6} {'Lluvia':>8} {'Prob%':>6} {'Viento':>8} {'Ráfaga':>8} {'Hum%':>6} {'ET₀':>5} {'HumSuelo':>9}")
    lines.append("-" * 90)
    for i, d in enumerate(forecast["dates"]):
        date_label = format_date_es(d)
        tm = f"{forecast['temp_max'][i]:.1f}°C" if forecast['temp_max'][i] is not None else "—"
        tn = f"{forecast['temp_min'][i]:.1f}°C" if forecast['temp_min'][i] is not None else "—"
        pp = f"{forecast['precipitation'][i]:.1f}mm" if forecast['precipitation'][i] is not None else "—"
        pr = f"{forecast['precip_probability'][i]:.0f}%" if forecast['precip_probability'][i] is not None else "—"
        ws = f"{forecast['wind_speed'][i]:.0f}km/h" if forecast['wind_speed'][i] is not None else "—"
        wg = f"{forecast['wind_gusts'][i]:.0f}km/h" if forecast['wind_gusts'][i] is not None else "—"
        hm = f"{forecast['humidity_max'][i]:.0f}%" if forecast['humidity_max'][i] is not None else "—"
        et = f"{forecast['et0'][i]:.1f}" if forecast['et0'][i] is not None else "—"
        sm = f"{forecast['soil_moisture'][i]:.2f}" if forecast['soil_moisture'][i] is not None else "—"
        lines.append(f"{date_label:<12} {tm:>6} {tn:>6} {pp:>8} {pr:>6} {ws:>8} {wg:>8} {hm:>6} {et:>5} {sm:>9}")
    return "\n".join(lines)


def build_alerts_summary(alerts: list[Alert]) -> str:
    if not alerts:
        return "No se detectaron alertas para los próximos 7 días."
    lines = []
    current_crop = None
    for a in sorted(alerts, key=lambda x: (x.crop, x.day_index)):
        if a.crop != current_crop:
            current_crop = a.crop
            info = CROP_INFO[a.crop]
            lines.append(f"\n{info['emoji']} {info['label'].upper()}:")
        lines.append(f"  [{a.severity.upper()}] {format_date_es(a.date_str)} — {a.label}: {a.message}")
    return "\n".join(lines)


def generate_analysis(forecast: dict, alerts: list[Alert]) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback_analysis(alerts)

    weather_summary = build_weather_summary(forecast)
    alerts_summary = build_alerts_summary(alerts)
    crops_list = ", ".join(CROP_INFO[c]["label"] for c in MONITORED_CROPS)

    prompt = f"""Eres un ingeniero agrónomo experto en la zona de la Región Metropolitana, Chile.
Analiza el pronóstico climático y las alertas detectadas para los cultivos del predio ubicado en {LOCATION['name']}.

CULTIVOS MONITOREADOS: {crops_list}

PRONÓSTICO CLIMÁTICO (7 días):
{weather_summary}

ALERTAS DETECTADAS POR SISTEMA DE REGLAS:
{alerts_summary}

INSTRUCCIONES:
1. Escribe un análisis agronómico conciso y práctico en español.
2. Prioriza las alertas más críticas primero.
3. Da recomendaciones concretas y accionables para cada problema detectado.
4. Menciona el contexto de la zona (zona mediterránea semiárida).
5. Si hay condiciones favorables, menciónalas brevemente.
6. Máximo 350 palabras. Tono profesional pero directo.
7. Organiza por cultivo o por tema según lo más útil.
8. NO repitas exactamente los mensajes de alerta — añade contexto y profundidad agronómica.
"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=600,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return _fallback_analysis(alerts)


def _fallback_analysis(alerts: list[Alert]) -> str:
    if not alerts:
        return "Sin alertas críticas para los próximos 7 días. Condiciones climáticas dentro de rangos normales para los cultivos monitoreados."
    critical = [a for a in alerts if a.severity == "crítica"]
    high = [a for a in alerts if a.severity == "alta"]
    msg = f"Se detectaron {len(alerts)} alertas en total"
    if critical:
        msg += f", incluyendo {len(critical)} críticas"
    if high:
        msg += f" y {len(high)} de alta severidad"
    msg += ". Revisa las alertas por cultivo para más detalle. (Análisis IA no disponible — verifica tu API key de Groq)"
    return msg

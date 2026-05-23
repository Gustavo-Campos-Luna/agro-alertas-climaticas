"""
main.py — Orquestador principal del Sistema Agro Alertas Climáticas.

Flujo de ejecución:
  1. Carga variables de entorno (.env)
  2. Obtiene pronóstico de Open-Meteo para Santiago (7 días)
  3. Evalúa reglas de alerta para cada cultivo monitoreado
  4. Genera gráficos agroclimáticos con Matplotlib
  5. Solicita análisis agronómico a Groq (Llama 3.3-70b, gratis)
  6. Construye y envía email HTML con todo lo anterior via Gmail SMTP

Uso:
  python main.py              → Ejecuta y envía email
  python main.py --preview    → Guarda el email como HTML en local (sin enviar)
  python main.py --test       → Muestra resumen en consola (sin email ni IA)
"""

import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

# UTF-8 en consola Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Carga las variables de entorno desde .env antes de cualquier import que las use
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

from agro_alertas.weather import fetch_forecast
from agro_alertas.rules import evaluate, alerts_by_crop, overall_severity, format_date_es
from agro_alertas.charts import generate_charts
from agro_alertas.ai_analysis import generate_analysis
from agro_alertas.mailer import send_email, build_html
from agro_alertas.config import LOCATION, MONITORED_CROPS
from agro_alertas.crops_db import CROP_INFO


# ─── Utilidades de consola ──────────────────────────────────────────────────

SEVERITY_ICONS = {
    "crítica": "🔴",
    "alta": "🟡",
    "media": "🟠",
    "baja": "🟢",
    "sin_alertas": "✅",
}

def _header():
    print("\n" + "═" * 60)
    print("  🌱 Sistema Agro Alertas Climáticas")
    print(f"  📍 {LOCATION['name']}")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("═" * 60)

def _print_summary(forecast: dict, alerts: list):
    severity = overall_severity(alerts)
    icon = SEVERITY_ICONS.get(severity, "❓")
    print(f"\n  Nivel de alerta: {icon} {severity.upper()}")
    print(f"  Total alertas: {len(alerts)}")

    by_crop = alerts_by_crop(alerts)
    for crop in MONITORED_CROPS:
        crop_alerts = by_crop[crop]
        info = CROP_INFO[crop]
        count = len(crop_alerts)
        status = f"{count} alerta{'s' if count != 1 else ''}" if count > 0 else "sin alertas"
        print(f"    {info['emoji']} {info['label']:<20} → {status}")

    print(f"\n  Pronóstico disponible: {forecast['n_days']} días")
    print(f"  Temperaturas: {min(t for t in forecast['temp_min'] if t is not None):.1f}°C mín "
          f"/ {max(t for t in forecast['temp_max'] if t is not None):.1f}°C máx")

    rain_total = sum(p for p in forecast["precipitation"] if p is not None)
    print(f"  Lluvia acumulada 7 días: {rain_total:.1f} mm")


# ─── Modo preview (HTML a disco) ────────────────────────────────────────────

def _save_preview(forecast: dict, alerts: list, ai_text: str, chart_b64: str):
    output_path = PROJECT_ROOT / "outputs" / "preview_email.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = build_html(forecast, alerts, ai_text, chart_b64)
    output_path.write_text(html, encoding="utf-8")
    print(f"\n  ✓ Preview guardado en: {output_path}")
    print("    Abre el archivo en tu navegador para ver el email.")


# ─── Modo test (sin email ni IA) ────────────────────────────────────────────

def _run_test(forecast: dict, alerts: list):
    _print_summary(forecast, alerts)
    if alerts:
        print("\n  Detalle de alertas:")
        for a in alerts[:10]:
            icon = SEVERITY_ICONS.get(a.severity, "?")
            print(f"    {icon} [{a.crop_emoji} {a.crop_label}] {format_date_es(a.date_str)} — {a.label}")
        if len(alerts) > 10:
            print(f"    ... y {len(alerts) - 10} alertas más.")
    print()


# ─── Flujo principal ────────────────────────────────────────────────────────

def run(mode: str = "email"):
    """
    Ejecuta el sistema completo.

    Args:
        mode: "email"   → envía el email completo
              "preview" → guarda HTML localmente
              "test"    → solo muestra resumen en consola
    """
    _header()

    # PASO 1: Pronóstico climático
    print("\n  [1/5] Obteniendo pronóstico de Open-Meteo...", end=" ", flush=True)
    try:
        forecast = fetch_forecast()
        print(f"OK ({forecast['n_days']} días, {LOCATION['name']})")
    except Exception as e:
        print(f"ERROR\n  ✗ No se pudo obtener el pronóstico: {e}")
        sys.exit(1)

    # PASO 2: Evaluación de alertas
    print("  [2/5] Evaluando alertas por cultivo...", end=" ", flush=True)
    alerts = evaluate(forecast)
    severity = overall_severity(alerts)
    icon = SEVERITY_ICONS.get(severity, "?")
    print(f"OK ({len(alerts)} alertas — {icon} {severity})")

    if mode == "test":
        _run_test(forecast, alerts)
        return

    # PASO 3: Gráficos
    print("  [3/5] Generando gráficos climáticos...", end=" ", flush=True)
    try:
        chart_b64 = generate_charts(forecast)
        print("OK (5 paneles generados)")
    except Exception as e:
        print(f"ERROR — {e}\n  Continuando sin gráficos.")
        chart_b64 = ""

    # PASO 4: Análisis IA (Groq)
    if len(alerts) > 0:
        print("  [4/5] Solicitando análisis agronómico a Groq (Llama 3.3)...", end=" ", flush=True)
        try:
            ai_text = generate_analysis(forecast, alerts)
            print("OK")
        except Exception as e:
            print(f"WARN — {e}\n  Usando análisis de respaldo.")
            ai_text = "No fue posible obtener análisis IA. Revisa tu API key de Groq en el archivo .env"
    else:
        print("  [4/5] Sin alertas — análisis IA omitido.")
        ai_text = "No se detectaron condiciones de riesgo para los próximos 7 días. Condiciones climáticas favorables para todos los cultivos monitoreados."

    # PASO 5: Envío / preview
    if mode == "preview":
        print("  [5/5] Guardando preview HTML...", end=" ", flush=True)
        _save_preview(forecast, alerts, ai_text, chart_b64)
        _print_summary(forecast, alerts)
    else:
        print("  [5/5] Enviando email via Gmail SMTP...", end=" ", flush=True)
        try:
            send_email(forecast, alerts, ai_text, chart_b64)
        except ValueError as e:
            print(f"\n\n  ✗ Error de configuración: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n  ✗ Error al enviar email: {e}")
            print("\n  Tip: Asegúrate de usar un Gmail App Password (no tu contraseña normal).")
            print("  Guía: Google Account → Seguridad → Contraseñas de aplicación")
            sys.exit(1)

        _print_summary(forecast, alerts)

    print("\n" + "═" * 60)
    print("  ✓ Sistema completado exitosamente")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    mode = "email"
    if "--preview" in sys.argv:
        mode = "preview"
    elif "--test" in sys.argv:
        mode = "test"

    run(mode)

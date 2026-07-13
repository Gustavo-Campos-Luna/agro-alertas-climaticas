# Agro Alertas Climáticas

[![CI](https://github.com/Gustavo-Campos-Luna/agro-alertas-climaticas/actions/workflows/ci.yml/badge.svg)](https://github.com/Gustavo-Campos-Luna/agro-alertas-climaticas/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

Sistema en Python que genera un reporte agroclimático semanal para un predio agrícola y lo envía por correo. Obtiene el pronóstico desde Open-Meteo, evalúa reglas de alerta por cultivo (heladas, enfermedades fúngicas, estrés hídrico, viento), genera gráficos y agrega un análisis agronómico con IA (Groq / Llama 3.3).

Configurado por defecto para Chimbarongo, Colchagua (Chile), pero la ubicación y los cultivos monitoreados son configurables.

## Estructura

```text
src/agro_alertas/
  config.py         Ubicación del predio y cultivos monitoreados (via variables de entorno)
  weather.py        Cliente de Open-Meteo y procesamiento del pronóstico
  crops_db.py       Base de conocimiento agronómico: reglas de alerta por cultivo
  rules.py          Evaluación de reglas contra el pronóstico y utilidades de severidad
  charts.py         Generación de gráficos (Matplotlib) embebidos en el email
  ai_analysis.py    Análisis agronómico generado con Groq (Llama 3.3), con respaldo sin IA
  mailer.py         Construcción del email HTML y envío via Gmail SMTP
  main.py           Orquestador del flujo completo (CLI)
tests/              Suite de tests (pytest)
scripts/            Scripts de instalación y tarea programada (Windows)
outputs/            Archivos generados localmente, como preview_email.html
.github/workflows/  CI (lint + tests) y el envío diario programado
```

## Instalación

```bash
git clone https://github.com/Gustavo-Campos-Luna/agro-alertas-climaticas.git
cd agro-alertas-climaticas
pip install -r requirements.txt
cp .env.example .env
```

Completa `.env` con tus credenciales:

```env
EMAIL_SENDER=
EMAIL_PASSWORD=      # Gmail App Password, no tu contraseña de cuenta
EMAIL_RECIPIENTS=    # separados por coma
GROQ_API_KEY=        # opcional: sin ella se usa un análisis de respaldo sin IA
```

Opcionalmente, sobreescribe la ubicación del predio (por defecto Chimbarongo, Colchagua):

```env
LOCATION_NAME=
LOCATION_LATITUDE=
LOCATION_LONGITUDE=
LOCATION_TIMEZONE=
LOCATION_ALTITUDE_M=
LOCATION_REGION=
```

## Uso

```bash
export PYTHONPATH=src   # PowerShell: $env:PYTHONPATH = "src"

python -m agro_alertas.main --test      # resumen en consola, sin email ni IA
python -m agro_alertas.main --preview   # genera outputs/preview_email.html sin enviar
python -m agro_alertas.main             # ejecuta el flujo completo y envía el email
```

## Desarrollo

```bash
pip install -e ".[dev]"

ruff check .                  # lint
mypy src/agro_alertas/         # chequeo de tipos
pytest                        # tests
```

## Automatización (GitHub Actions)

`.github/workflows/daily_alert.yml` ejecuta el envío diario mediante un cron de GitHub Actions, usando `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENTS` y `GROQ_API_KEY` como [Secrets del repositorio](../../settings/secrets/actions) (nunca hardcodeados).

Para pausar el envío diario sin tocar el código: pestaña **Actions** → workflow **"Alerta Agroclimática Diaria"** → **Disable workflow**.

`.github/workflows/ci.yml` corre lint, chequeo de tipos y tests en cada push y pull request a `main`.

## Scripts Windows

```powershell
scripts\setup.bat
scripts\configurar_tarea.bat
```

## Descargo de responsabilidad

Este reporte es de carácter orientativo. Los umbrales agronómicos están calibrados con fuentes públicas (SAG Chile, INIA, USDA-ARS, entre otras) pero siempre deben validarse con observación directa del cultivo y criterio agronómico local antes de tomar decisiones de manejo.

## Licencia

[MIT](LICENSE)

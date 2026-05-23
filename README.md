# Agro Alertas Climaticas

Sistema Python para generar un reporte agroclimatico semanal de Chimbarongo, Colchagua.

El flujo principal obtiene pronostico desde Open-Meteo, evalua reglas por cultivo, genera graficos, agrega analisis agronomico con Groq cuando corresponde y arma un email HTML.

## Estructura

```text
src/agro_alertas/   Codigo fuente de la aplicacion
scripts/            Scripts de instalacion y tarea programada
outputs/            Archivos generados, como preview_email.html
requirements.txt    Dependencias para instalacion simple
.env.example        Variables requeridas
```

## Configuracion

1. Instala dependencias:

```powershell
pip install -r requirements.txt
```

2. Copia `.env.example` a `.env` y completa credenciales:

```env
EMAIL_SENDER=
EMAIL_PASSWORD=
EMAIL_RECIPIENTS=
GROQ_API_KEY=
```

## Uso

Desde la raiz del proyecto:

```powershell
$env:PYTHONPATH = "src"
python -m agro_alertas.main --test
python -m agro_alertas.main --preview
python -m agro_alertas.main
```

El preview HTML se genera en:

```text
outputs/preview_email.html
```

## Scripts Windows

```powershell
scripts\setup.bat
scripts\configurar_tarea.bat
```


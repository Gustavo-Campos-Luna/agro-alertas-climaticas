# Contribuir

Gracias por tu interés en mejorar este proyecto.

## Configuracion del entorno de desarrollo

```bash
git clone https://github.com/<tu-usuario>/agro-alertas-climaticas.git
cd agro-alertas-climaticas
pip install -r requirements.txt
pip install -e ".[dev]"
cp .env.example .env  # completa tus credenciales locales
```

## Antes de enviar un cambio

Ejecuta lint, chequeo de tipos y tests:

```bash
ruff check .
mypy src/agro_alertas/
pytest
```

## Estilo de codigo

- Formateo y orden de imports gestionados por [ruff](https://docs.astral.sh/ruff/).
- Tipado gradual con `mypy`; añade anotaciones de tipo en el codigo nuevo.
- Los umbrales agronomicos en `crops_db.py` deben citar la fuente (SAG, INIA, USDA-ARS, etc.) en un comentario o en el docstring del modulo.

## Pull requests

1. Crea una rama descriptiva (`feature/...`, `fix/...`).
2. Asegura que CI (lint + tests) pase en verde.
3. Describe el cambio y su motivacion en la descripcion del PR.

"""
crops_db.py — Base de conocimiento de cultivos y reglas de alerta.

Enfermedades y umbrales calibrados para la Región de O'Higgins / Colchagua, Chile.
Fuentes validadas: SAG Chile (fichas técnicas de plagas/enfermedades), INIA Rayentué,
SmartCherry.cl, FIA, USDA-ARS, SINAVIMO Argentina, INIA Uruguay, y literatura fitopatológica nacional.
Fungicidas verificados en plaguicidas.sag.gob.cl (planilla actualizada 01-10-2025).

Umbrales verificados contra fuentes chilenas y latam oficiales (revisión 2025):
  - Monilinia fructicola (cerezo): T 14-25°C (SAG + SmartCherry), antes 15-28°C
  - Botrytis cinerea (viña): umbral alerta HR >85%, esporulación óptima HR >90-95%
  - Roya amarilla (trigo): HR >85% (alerta temprana, infección plena a HR >92%)
  - Antracnosis (poroto): T 13-26°C añadida; HR alerta subida a >90% (óptimo 92-100%)
  - Mildiu viña: precip >6mm (alerta), T 10-30°C; regla original exige ≥10mm (INIA Chile/Auger 1997)
  - Golpe blanco trigo: temp_max >20°C (antes >15°C); óptimo 24-28°C (INIA Uruguay + El Mercurio/INIA)
  - Roya de la hoja trigo: T 15-30°C (antes 18-28°C); óptimo 16-22°C (USDA-ARS + SINAVIMO Argentina)
"""

from datetime import date

CROP_INFO = {
    "viña": {
        "label": "Viña / Vid",
        "emoji": "🍇",
        "description": "Vitis vinifera — Colchagua, zona de producción de vinos finos",
        "harvest_months": [3, 4],
        "flowering_months": [10, 11],
    },
    "cerezos": {
        "label": "Cerezos",
        "emoji": "🍒",
        "description": "Prunus avium — Muy sensible a lluvia en cosecha y heladas tardías",
        "harvest_months": [12, 1],
        "flowering_months": [9, 10],
    },
    "maíz": {
        "label": "Maíz",
        "emoji": "🌽",
        "description": "Zea mays — Sensible a heladas y calor extremo en floración",
        "harvest_months": [3, 4],
        "flowering_months": [12, 1],
    },
    "trigo": {
        "label": "Trigo",
        "emoji": "🌾",
        "description": "Triticum aestivum — Principal cereal de la zona centro-sur de Chile",
        "harvest_months": [12, 1],
        "flowering_months": [10, 11],
    },
    "porotos": {
        "label": "Porotos",
        "emoji": "🫘",
        "description": "Phaseolus vulgaris — Leguminosa muy sensible a heladas y anegamiento",
        "harvest_months": [2, 3],
        "flowering_months": [12, 1],
    },
}


def get_alert_rules(crop: str, forecast_date: date) -> list[dict]:
    month = forecast_date.month

    rules = {

        # ──────────────────────────────────────────────────────────────────
        # VIÑA / VID
        # ──────────────────────────────────────────────────────────────────
        "viña": [
            {
                "id": "helada_critica",
                "label": "Helada crítica",
                "check": lambda d: d["temp_min"] is not None and d["temp_min"] < 0,
                "severity": "crítica",
                "message": lambda d: f"Temperatura mínima de {d['temp_min']:.1f}°C — Daño severo en brotes, pámpanos y racimos. Activa sistemas antihelada de inmediato.",
            },
            {
                "id": "pre_helada",
                "label": "Pre-helada",
                "check": lambda d: d["temp_min"] is not None and 0 <= d["temp_min"] < 3,
                "severity": "alta",
                "message": lambda d: f"Temperatura mínima de {d['temp_min']:.1f}°C — Zona de riesgo. Prepara sistemas antihelada y monitorea la madrugada.",
            },
            {
                "id": "botrytis",
                "label": "Podredumbre gris — Botrytis cinerea",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 85 and
                    d["precipitation"] is not None and d["precipitation"] > 2
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}% + {d['precipitation']:.1f}mm — Condiciones de riesgo para Botrytis cinerea. Umbral alerta HR >85%; esporulación óptima >90% (T óptima 17-23°C). Resistencia a iprodiona documentada en Colchagua — rota grupos FRAC: iprodiona (FRAC 2, máx. 2 aplic./temporada) → fenhexamida/Teldor (FRAC 17) → ciprodinil+fludioxonil/Switch (FRAC 9+12). Todos registrados SAG Chile.",
            },
            {
                "id": "mildiu",
                "label": "Mildiu — Plasmopara viticola",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["temp_max"] is not None and 10 <= d["temp_max"] <= 30 and
                    d["precipitation"] is not None and d["precipitation"] > 6
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C + {d['precipitation']:.1f}mm — Condiciones de infección de Mildiu. La 'Regla de los 3 diez' requiere T>10°C + lluvia≥10mm + brotes≥10cm; umbral de alerta desde 6mm (INIA Chile / Auger & Esterio 1997). Esporulación secundaria activa con HR>80%. Aplica cobre preventivo o mancozeb.",
            },
            {
                "id": "oidio",
                "label": "Oídio — Erysiphe necator",
                "check": lambda d: (
                    d["humidity_mean"] is not None and 40 < d["humidity_mean"] < 72 and
                    d["temp_max"] is not None and 20 < d["temp_max"] < 33 and
                    (d["precipitation"] is None or d["precipitation"] < 1)
                ),
                "severity": "media",
                "message": lambda d: f"HR media {d['humidity_mean']:.0f}%, {d['temp_max']:.1f}°C sin lluvia — El oídio se favorece con tiempo seco y cálido, diferente a otros hongos. Aplica azufre preventivo o IBE (miclobutanil, tebuconazol).",
            },
            {
                "id": "viento_fuerte",
                "label": "Viento — daño en sarmientos y estructura",
                "check": lambda d: d["wind_gusts"] is not None and d["wind_gusts"] > 65,
                "severity": "alta",
                "message": lambda d: f"Ráfagas de {d['wind_gusts']:.0f} km/h — Riesgo de rotura de sarmientos y daño en espalderas. Revisa tensores y amarras.",
            },
            {
                "id": "calor_extremo",
                "label": "Estrés térmico — quemadura de racimos",
                "check": lambda d: d["temp_max"] is not None and d["temp_max"] > 38,
                "severity": "media",
                "message": lambda d: f"Temperatura de {d['temp_max']:.1f}°C — Riesgo de quemadura solar en racimos y detención de maduración. Riega en horario nocturno.",
            },
            *([{
                "id": "lluvia_cosecha",
                "label": "Lluvia en vendimia — dilución y podredumbre",
                "check": lambda d: d["precipitation"] is not None and d["precipitation"] > 8,
                "severity": "crítica",
                "message": lambda d: f"{d['precipitation']:.1f}mm durante vendimia — Dilución de azúcares, riesgo de Botrytis y Ácido Acético. Cosecha anticipada si grado está logrado.",
            }] if month in CROP_INFO["viña"]["harvest_months"] else []),
            {
                "id": "sequia_vina",
                "label": "Déficit hídrico — estrés en viña",
                "check": lambda d: (
                    d["et0"] is not None and d["et0"] > 5 and
                    d["precipitation"] is not None and d["precipitation"] < 1 and
                    d["soil_moisture"] is not None and d["soil_moisture"] < 0.20
                ),
                "severity": "media",
                "message": lambda d: f"Demanda hídrica {d['et0']:.1f}mm/día, suelo seco ({d['soil_moisture']:.2f} m³/m³) — Estrés hídrico activo. Revisa programación de riego por goteo.",
            },
        ],

        # ──────────────────────────────────────────────────────────────────
        # CEREZOS
        # ──────────────────────────────────────────────────────────────────
        "cerezos": [
            {
                "id": "helada_critica",
                "label": "Helada crítica en cerezos",
                "check": lambda d: d["temp_min"] is not None and d["temp_min"] < -2,
                "severity": "crítica",
                "message": lambda d: f"Temperatura de {d['temp_min']:.1f}°C — Daño irreversible en yemas y fruta cuajada. Activa sistemas antihelada con urgencia (aspersión, calefactores).",
            },
            {
                "id": "helada_moderada",
                "label": "Helada — daño en flores y fruta",
                "check": lambda d: d["temp_min"] is not None and -2 <= d["temp_min"] < 0,
                "severity": "alta",
                "message": lambda d: f"Temperatura de {d['temp_min']:.1f}°C — Riesgo de daño en flores y fruta en desarrollo.",
            },
            {
                "id": "pre_helada",
                "label": "Temperatura marginal — zona de riesgo",
                "check": lambda d: d["temp_min"] is not None and 0 <= d["temp_min"] < 2,
                "severity": "media",
                "message": lambda d: f"Mínima de {d['temp_min']:.1f}°C — Monitorea la madrugada con termómetro en zona de fruta.",
            },
            *([{
                "id": "lluvia_cosecha_cerezos",
                "label": "Lluvia en cosecha — rajado de fruta (cracking)",
                "check": lambda d: d["precipitation"] is not None and d["precipitation"] > 4,
                "severity": "crítica",
                "message": lambda d: f"{d['precipitation']:.1f}mm durante cosecha — El rajado por absorción de agua destruye la fruta. Coseche inmediatamente si hay madurez comercial. Considere cubierta plástica.",
            }] if month in CROP_INFO["cerezos"]["harvest_months"] else []),
            {
                "id": "monilia",
                "label": "Momificado / Pudrición parda — Monilinia fructicola",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 85 and
                    d["temp_max"] is not None and 14 <= d["temp_max"] <= 25
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C — Condiciones favorables para Monilinia fructicola (T óptima 20-25°C, rango 14-25°C; 5 h de humedad = inoculación; SAG Chile + SmartCherry). Alta presión en pre-cordillera de Colchagua. En cosecha de exportación prefiere ciprodinil+fludioxonil/Switch (FRAC 9+12, referencia ASOEX); iprodiona (FRAC 2) máx. 2 aplic./temporada. Ambos registrados SAG Chile.",
            },
            {
                "id": "viruela_cerezo",
                "label": "Viruela del cerezo — Coccomyces hiemalis",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["precipitation"] is not None and d["precipitation"] > 3 and
                    d["temp_max"] is not None and 10 < d["temp_max"] < 22
                ),
                "severity": "media",
                "message": lambda d: f"HR {d['humidity_max']:.0f}% + {d['precipitation']:.1f}mm + {d['temp_max']:.1f}°C — Condiciones para Viruela del cerezo (manchas foliares rojizas). Produce defoliación prematura. Aplica fungicida cúprico.",
            },
            {
                "id": "calor_extremo_cerezos",
                "label": "Calor extremo — doble carozo y quemadura",
                "check": lambda d: d["temp_max"] is not None and d["temp_max"] > 35,
                "severity": "alta",
                "message": lambda d: f"Temperatura de {d['temp_max']:.1f}°C — Riesgo de doble carozo en floración y quemadura solar en fruta. Riega en horas nocturnas.",
            },
            {
                "id": "viento_cerezos",
                "label": "Viento — daño mecánico y caída de fruta",
                "check": lambda d: d["wind_gusts"] is not None and d["wind_gusts"] > 50,
                "severity": "alta",
                "message": lambda d: f"Ráfagas de {d['wind_gusts']:.0f} km/h — Caída prematura de fruta y daño en ramas. Revisa estado de mallas antigranizo y antigolpe.",
            },
        ],

        # ──────────────────────────────────────────────────────────────────
        # MAÍZ
        # ──────────────────────────────────────────────────────────────────
        "maíz": [
            {
                "id": "helada_maiz",
                "label": "Helada crítica — daño total en maíz",
                "check": lambda d: d["temp_min"] is not None and d["temp_min"] < 2,
                "severity": "crítica",
                "message": lambda d: f"Temperatura de {d['temp_min']:.1f}°C — El maíz es extremadamente sensible a heladas en todas sus etapas. Pérdida total probable.",
            },
            {
                "id": "calor_extremo_maiz",
                "label": "Calor extremo — esterilidad del polen",
                "check": lambda d: d["temp_max"] is not None and d["temp_max"] > 38,
                "severity": "alta",
                "message": lambda d: f"Temperatura de {d['temp_max']:.1f}°C — Sobre 38°C el polen pierde viabilidad (esterilidad). Impacto directo en rendimiento si coincide con antesis (espigado).",
            },
            {
                "id": "tizon_norte",
                "label": "Tizón del norte — Exserohilum turcicum",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["temp_max"] is not None and 18 < d["temp_max"] < 27
                ),
                "severity": "media",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C — Condiciones favorables para Tizón del norte, enfermedad foliar prevalente en el centro de Chile. Monitorea hojas basales.",
            },
            {
                "id": "roya_maiz",
                "label": "Roya común del maíz — Puccinia sorghi",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["temp_max"] is not None and 16 < d["temp_max"] < 25 and
                    d["precipitation"] is not None and d["precipitation"] > 2
                ),
                "severity": "media",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C — Condiciones para Roya común. Inspecciona ambas caras del limbo foliar. Aplica triazol si superas 5% de área afectada.",
            },
            {
                "id": "pudricion_mazorca",
                "label": "Pudrición de mazorca — Fusarium/Gibberella",
                "check": lambda d: (
                    d["precipitation"] is not None and d["precipitation"] > 8 and
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["temp_max"] is not None and d["temp_max"] > 18
                ),
                "severity": "alta",
                "message": lambda d: f"{d['precipitation']:.1f}mm + HR {d['humidity_max']:.0f}% — Riesgo de pudrición por Fusarium/Gibberella con producción de micotoxinas (DON, fumonisinas). Crítico en floración y llenado de grano.",
            },
            {
                "id": "viento_acame",
                "label": "Viento — volcamiento (acame)",
                "check": lambda d: d["wind_speed"] is not None and d["wind_speed"] > 55,
                "severity": "alta",
                "message": lambda d: f"Viento de {d['wind_speed']:.0f} km/h — Riesgo de volcamiento de plantas. Más grave en espigado. Las plantas acamadas dificultan la cosecha mecánica.",
            },
            {
                "id": "sequia_maiz",
                "label": "Déficit hídrico crítico en maíz",
                "check": lambda d: (
                    d["et0"] is not None and d["et0"] > 4 and
                    d["precipitation"] is not None and d["precipitation"] < 1 and
                    d["soil_moisture"] is not None and d["soil_moisture"] < 0.18
                ),
                "severity": "alta",
                "message": lambda d: f"Demanda hídrica {d['et0']:.1f}mm/día, suelo seco ({d['soil_moisture']:.2f} m³/m³) — Estrés hídrico. El maíz sin agua en floración pierde rendimiento muy rápido. Riega de inmediato.",
            },
        ],

        # ──────────────────────────────────────────────────────────────────
        # TRIGO
        # ──────────────────────────────────────────────────────────────────
        "trigo": [
            {
                "id": "helada_trigo",
                "label": "Helada — daño en espiga de trigo",
                "check": lambda d: d["temp_min"] is not None and d["temp_min"] < 0,
                "severity": "alta",
                "message": lambda d: f"Temperatura de {d['temp_min']:.1f}°C — Daño posible en espigas si está en antesis o encañado. Evalúa el estado fenológico actual del cultivo.",
            },
            {
                "id": "roya_amarilla",
                "label": "Roya amarilla / Roya estriada — Puccinia striiformis",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 85 and
                    d["temp_max"] is not None and 10 <= d["temp_max"] <= 20
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C — Condiciones ideales para Roya amarilla (T óptima 10-15°C, se detiene sobre 22°C; HR >92% para infección). La enfermedad más destructiva del trigo en Chile, especialmente en O'Higgins y el Maule. Inspecciona urgente y aplica triazol (tebuconazol, propiconazol).",
            },
            {
                "id": "roya_hoja",
                "label": "Roya de la hoja — Puccinia triticina",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["temp_max"] is not None and 15 <= d["temp_max"] <= 30
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C — Condiciones para Roya de la hoja (T óptima 16-22°C, activa hasta 30°C; rocío nocturno ≥6-8 h = infección; USDA-ARS + SINAVIMO). Prefiere temperaturas más altas que la roya amarilla. Aplica estrobilurina o triazol preventivo.",
            },
            {
                "id": "golpe_blanco",
                "label": "Golpe blanco / Fusariosis — Fusarium graminearum",
                "check": lambda d: (
                    d["precipitation"] is not None and d["precipitation"] > 5 and
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["temp_max"] is not None and d["temp_max"] > 20
                ),
                "severity": "alta",
                "message": lambda d: f"{d['precipitation']:.1f}mm + HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C — Riesgo de Golpe blanco durante antesis (T>20°C + HR>80% + mojado>48 h = infección epidémica; T óptima 24-28°C; INIA Uruguay / El Mercurio Campo / INIA Chile). Produce micotoxinas DON. Aplica tebuconazol o metconazol.",
            },
            {
                "id": "mancha_amarilla",
                "label": "Mancha amarilla / Tan spot — Pyrenophora tritici-repentis",
                "check": lambda d: (
                    d["precipitation"] is not None and d["precipitation"] > 3 and
                    d["humidity_max"] is not None and d["humidity_max"] > 75 and
                    d["temp_max"] is not None and d["temp_max"] > 12
                ),
                "severity": "media",
                "message": lambda d: f"Lluvia {d['precipitation']:.1f}mm + HR {d['humidity_max']:.0f}% — Condiciones para Mancha amarilla, frecuente en suelos con rastrojos de trigo. Aplica fungicida si se detectan síntomas.",
            },
            {
                "id": "oidio_trigo",
                "label": "Oídio del trigo — Blumeria graminis",
                "check": lambda d: (
                    d["humidity_mean"] is not None and 50 < d["humidity_mean"] < 78 and
                    d["temp_max"] is not None and 15 < d["temp_max"] < 22 and
                    (d["precipitation"] is None or d["precipitation"] < 2)
                ),
                "severity": "media",
                "message": lambda d: f"HR {d['humidity_mean']:.0f}%, {d['temp_max']:.1f}°C sin lluvia — Condiciones para Oídio del trigo. Se desarrolla rápido con tiempo fresco y sin lluvia. Aplica azufre o IBE.",
            },
            *([{
                "id": "lluvia_cosecha_trigo",
                "label": "Lluvia en cosecha — germinación en espiga",
                "check": lambda d: d["precipitation"] is not None and d["precipitation"] > 8,
                "severity": "alta",
                "message": lambda d: f"{d['precipitation']:.1f}mm en cosecha — Riesgo de germinación en espiga (pre-harvest sprouting) con pérdida de gluten y caída del Número de Caída. Cosecha con urgencia si el grano está maduro.",
            }] if month in CROP_INFO["trigo"]["harvest_months"] else []),
            {
                "id": "sequia_trigo",
                "label": "Déficit hídrico en trigo",
                "check": lambda d: (
                    d["et0"] is not None and d["et0"] > 4 and
                    d["precipitation"] is not None and d["precipitation"] < 1 and
                    d["soil_moisture"] is not None and d["soil_moisture"] < 0.15
                ),
                "severity": "media",
                "message": lambda d: f"Demanda hídrica {d['et0']:.1f}mm/día, suelo seco — Estrés hídrico crítico en encañado y llenado de grano. El trigo bajo riego debe activar turno.",
            },
        ],

        # ──────────────────────────────────────────────────────────────────
        # POROTOS
        # ──────────────────────────────────────────────────────────────────
        "porotos": [
            {
                "id": "helada_porotos",
                "label": "Helada crítica — daño total en porotos",
                "check": lambda d: d["temp_min"] is not None and d["temp_min"] < 2,
                "severity": "crítica",
                "message": lambda d: f"Temperatura de {d['temp_min']:.1f}°C — Los porotos son extremadamente sensibles a heladas en cualquier etapa. Pérdida total del cultivo muy probable.",
            },
            {
                "id": "calor_porotos",
                "label": "Calor extremo — aborto de flores",
                "check": lambda d: d["temp_max"] is not None and d["temp_max"] > 35,
                "severity": "alta",
                "message": lambda d: f"Temperatura de {d['temp_max']:.1f}°C — Sobre 35°C se produce aborto de flores y falla en el cuaje de vainas. Impacto directo y severo en el rendimiento.",
            },
            {
                "id": "antracnosis",
                "label": "Antracnosis — Colletotrichum lindemuthianum",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 90 and
                    d["temp_max"] is not None and 13 <= d["temp_max"] <= 26 and
                    d["precipitation"] is not None and d["precipitation"] > 3
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C + {d['precipitation']:.1f}mm — Condiciones para Antracnosis (T óptima 13-26°C, HR 92-100%). Principal enfermedad del poroto en Chile. Manchas en vainas y hojas. Aplica preventivo: cobre/mancozeb (contacto) o azoxistrobina/Priori Xtra (sistémico, carencia 21 d). Todos registrados SAG Chile.",
            },
            {
                "id": "roya_porotos",
                "label": "Roya del poroto — Uromyces appendiculatus",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 80 and
                    d["temp_max"] is not None and 17 < d["temp_max"] < 27
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C — Condiciones favorables para Roya del poroto. Muy destructiva si no se controla. Aplica triazol o estrobilurina preventivo.",
            },
            {
                "id": "moho_blanco",
                "label": "Moho blanco / Pudrición del tallo — Sclerotinia sclerotiorum",
                "check": lambda d: (
                    d["humidity_max"] is not None and d["humidity_max"] > 85 and
                    d["temp_max"] is not None and 14 < d["temp_max"] < 24 and
                    d["soil_moisture"] is not None and d["soil_moisture"] > 0.25
                ),
                "severity": "alta",
                "message": lambda d: f"HR {d['humidity_max']:.0f}%, {d['temp_max']:.1f}°C, suelo saturado — Condiciones críticas para Sclerotinia (moho blanco). Una vez establecido es muy difícil de controlar. Mejora drenaje y ventilación.",
            },
            {
                "id": "anegamiento_porotos",
                "label": "Exceso hídrico — pudrición radicular",
                "check": lambda d: d["precipitation"] is not None and d["precipitation"] > 20,
                "severity": "alta",
                "message": lambda d: f"{d['precipitation']:.1f}mm — Alto riesgo de anegamiento y pudrición por Rhizoctonia solani y Phytophthora. Verifica drenaje superficial del potrero.",
            },
            {
                "id": "sequia_porotos",
                "label": "Déficit hídrico en porotos",
                "check": lambda d: (
                    d["soil_moisture"] is not None and d["soil_moisture"] < 0.15 and
                    d["et0"] is not None and d["et0"] > 3
                ),
                "severity": "alta",
                "message": lambda d: f"Suelo seco ({d['soil_moisture']:.2f} m³/m³), demanda hídrica {d['et0']:.1f}mm/día — Estrés hídrico severo. El déficit en floración y llenado de vaina reduce drásticamente el rendimiento.",
            },
        ],
    }

    return rules.get(crop, [])

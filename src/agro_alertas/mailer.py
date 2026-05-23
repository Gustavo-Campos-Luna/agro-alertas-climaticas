"""
mailer.py — Construcción y envío del email HTML agroclimático.

Diseño: "Diario de Campo" — estética editorial agrícola.
Tipografía: Playfair Display (encabezados) + IBM Plex Mono (datos).
Paleta: tinta oscura + vitela cálida + terracota de alerta + verde salvia.

El email incluye:
  - Header editorial con nivel de alerta y estadísticas clave
  - Gráficos embebidos como imagen base64 (sin servidor externo)
  - Alertas agrupadas por cultivo en formato lista compacta
  - Análisis agronómico generado por Groq
  - Tabla numérica del pronóstico 7 días
  - Footer minimalista con fuentes de datos
"""

import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from agro_alertas.rules import Alert, format_date_es, overall_severity, alerts_by_crop
from agro_alertas.config import LOCATION, MONITORED_CROPS
from agro_alertas.crops_db import CROP_INFO


def _md_to_html(text: str) -> str:
    """Convierte markdown básico (Groq output) a HTML limpio para email."""
    lines = text.split("\n")
    out = []
    for line in lines:
        # Encabezados ### ## #
        line = re.sub(r"^###\s+(.+)", r'<p style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:#1C1917;margin:12px 0 4px 0;">\1</p>', line)
        line = re.sub(r"^##\s+(.+)",  r'<p style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:#1C1917;margin:14px 0 4px 0;">\1</p>', line)
        line = re.sub(r"^#\s+(.+)",   r'<p style="font-family:Georgia,serif;font-size:15px;font-weight:700;color:#1C1917;margin:14px 0 6px 0;">\1</p>', line)
        # Negrita e itálica
        line = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", line)
        line = re.sub(r"\*\*(.+?)\*\*",     r"<strong>\1</strong>", line)
        line = re.sub(r"\*(.+?)\*",          r"<em>\1</em>", line)
        # Ítems de lista
        if re.match(r"^[-•]\s+", line):
            line = re.sub(r"^[-•]\s+(.+)", r'<p style="margin:4px 0 4px 16px;font-family:Georgia,serif;font-size:13px;color:#1C1917;line-height:1.65;text-align:justify;">— \1</p>', line)
        elif re.match(r"^\d+\.\s+", line):
            line = re.sub(r"^\d+\.\s+(.+)", r'<p style="margin:4px 0 4px 16px;font-family:Georgia,serif;font-size:13px;color:#1C1917;line-height:1.65;text-align:justify;">\1</p>', line)
        elif line.strip() == "":
            line = '<div style="height:6px;"></div>'
        elif not line.startswith("<p"):
            line = f'<p style="margin:5px 0;font-family:Georgia,serif;font-size:13px;color:#1C1917;line-height:1.7;text-align:justify;">{line}</p>'
        out.append(line)
    return "\n".join(out)


# ─── Tokens de diseño ───────────────────────────────────────────────────────

C = {
    "ink":        "#1C1917",
    "ink_soft":   "#44403C",
    "vellum":     "#F8F5EF",
    "vellum_mid": "#EDE8DF",
    "vellum_dk":  "#DDD8CF",
    "terracotta": "#B5451B",
    "terra_lt":   "#E8D5CC",
    "sage":       "#4A7059",
    "sage_lt":    "#C8DDD0",
    "amber":      "#92400E",
    "amber_lt":   "#FDE68A",
    "critical":   "#991B1B",
    "critical_lt":"#FEE2E2",
    "high":       "#92400E",
    "high_lt":    "#FEF3C7",
    "medium":     "#713F12",
    "medium_lt":  "#FEF9C3",
    "ok":         "#14532D",
    "ok_lt":      "#DCFCE7",
    "rule":       "#D6D0C8",
    "white":      "#FDFCFA",
}

NUM_FONT = "Arial, Helvetica, 'Segoe UI', sans-serif"

# Colores de borde izquierdo y punto por severidad
SEV = {
    "crítica":    {"dot": C["critical"],  "bar": C["critical"],  "bg": C["critical_lt"], "label": "CRÍTICA"},
    "alta":       {"dot": C["terracotta"],"bar": C["terracotta"],"bg": C["terra_lt"],    "label": "ALTA"},
    "media":      {"dot": C["amber"],     "bar": C["amber"],     "bg": C["amber_lt"],    "label": "MEDIA"},
    "baja":       {"dot": C["sage"],      "bar": C["sage"],      "bg": C["sage_lt"],     "label": "BAJA"},
    "sin_alertas":{"dot": C["sage"],      "bar": C["sage"],      "bg": C["ok_lt"],       "label": "OK"},
}


# ─── Componentes HTML ────────────────────────────────────────────────────────

def _severity_stripe(severity: str) -> str:
    """Barra horizontal de color según severidad (reemplaza al badge genérico)."""
    s = SEV.get(severity, SEV["media"])
    labels = {
        "crítica":    "ALERTA CRÍTICA — Acción inmediata requerida",
        "alta":       "ALERTA ALTA — Revisa los cultivos afectados",
        "media":      "ALERTA MEDIA — Monitoreo recomendado",
        "baja":       "ALERTA BAJA — Vigilancia rutinaria",
        "sin_alertas":"SIN ALERTAS — Condiciones favorables esta semana",
    }
    return f"""
    <div style="background:{s['bar']};padding:10px 32px;">
      <span style="font-family:'IBM Plex Mono',Courier,monospace;font-size:11px;
                   font-weight:500;letter-spacing:2px;color:{C['white']};text-transform:uppercase;">
        {labels.get(severity, severity.upper())}
      </span>
    </div>"""


def _stat_block(value: str, label: str, accent: str = C["vellum"]) -> str:
    return f"""
    <td style="padding:20px 24px;border-right:1px solid rgba(248,245,239,0.24);text-align:center;vertical-align:middle;">
      <div style="font-family:{NUM_FONT};font-size:31px;
                  font-weight:700;color:{accent};line-height:1;letter-spacing:0;
                  font-variant-numeric:tabular-nums;">{value}</div>
      <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                  letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.55);
                  margin-top:5px;">{label}</div>
    </td>"""


def _crop_row(crop: str, crop_alerts: list) -> str:
    info = CROP_INFO[crop]
    has = len(crop_alerts) > 0

    if not has:
        return f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid {C['vellum_dk']};">
            <span style="font-family:'IBM Plex Mono',Courier,monospace;font-size:10px;
                         color:{C['sage']};margin-right:10px;">✓</span>
            <span style="font-family:Georgia,'Playfair Display',serif;font-size:13px;
                         color:{C['ink_soft']};font-style:italic;">{info['label']}</span>
            <span style="font-family:'IBM Plex Mono',Courier,monospace;font-size:10px;
                         color:{C['sage']};float:right;">sin alertas</span>
          </td>
        </tr>"""

    # Determina la severidad más alta del cultivo
    order = {"crítica": 0, "alta": 1, "media": 2, "baja": 3}
    top_sev = min(crop_alerts, key=lambda a: order.get(a.severity, 9)).severity
    s = SEV.get(top_sev, SEV["media"])

    alert_rows = []
    seen = set()
    for a in crop_alerts:
        key = (a.alert_id, a.date_str)
        if key in seen:
            continue
        seen.add(key)
        sv = SEV.get(a.severity, SEV["media"])
        alert_rows.append(f"""
        <div style="display:flex;gap:10px;align-items:flex-start;padding:5px 0;
                    border-bottom:1px dashed {C['vellum_dk']};">
          <div style="flex-shrink:0;margin-top:3px;">
            <span style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                         font-weight:700;letter-spacing:1px;color:{sv['dot']};
                         background:{sv['bg']};padding:1px 5px;">{sv['label']}</span>
          </div>
          <div style="flex:1;">
            <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:10px;
                        color:{C['ink_soft']};margin-bottom:2px;">{format_date_es(a.date_str)}</div>
            <div style="font-family:Georgia,'Times New Roman',serif;font-size:12px;
                        color:{C['ink']};line-height:1.5;">{a.message}</div>
          </div>
        </div>""")

    return f"""
    <tr>
      <td style="padding:0;border-bottom:1px solid {C['rule']};">
        <div style="border-left:3px solid {s['bar']};padding:12px 16px;margin:8px 0;">
          <div style="font-family:Georgia,'Playfair Display',serif;font-size:14px;
                      font-weight:700;color:{C['ink']};margin-bottom:8px;">
            {info['emoji']} {info['label']}
            <span style="font-family:'IBM Plex Mono',Courier,monospace;font-size:10px;
                         color:{s['dot']};font-weight:400;float:right;margin-top:2px;">
              {len(crop_alerts)} alerta{'s' if len(crop_alerts)>1 else ''}
            </span>
          </div>
          {''.join(alert_rows)}
        </div>
      </td>
    </tr>"""


def _forecast_table(forecast: dict) -> str:
    header_cells = ["", "T.Máx", "T.Mín", "Lluvia", "Prob.", "Viento", "Ráfaga", "HR%", "Dem.Hídrica*"]
    header_html = "".join(
        f'<th style="padding:6px 8px;text-align:right;font-family:\'IBM Plex Mono\',Courier,monospace;'
        f'font-size:9px;letter-spacing:1px;color:{C["white"]};border-right:1px solid rgba(255,255,255,0.15);">'
        f'{h}</th>'
        for h in header_cells
    )

    rows_html = ""
    for i, d in enumerate(forecast["dates"]):
        date_lbl = format_date_es(d)
        tm  = f"{forecast['temp_max'][i]:.0f}°" if forecast['temp_max'][i] is not None else "—"
        tn  = f"{forecast['temp_min'][i]:.0f}°" if forecast['temp_min'][i] is not None else "—"
        pp  = f"{forecast['precipitation'][i]:.1f}" if forecast['precipitation'][i] is not None else "—"
        pr  = f"{forecast['precip_probability'][i]:.0f}%" if forecast['precip_probability'][i] is not None else "—"
        ws  = f"{forecast['wind_speed'][i]:.0f}" if forecast['wind_speed'][i] is not None else "—"
        wg  = f"{forecast['wind_gusts'][i]:.0f}" if forecast['wind_gusts'][i] is not None else "—"
        hm  = f"{forecast['humidity_max'][i]:.0f}%" if forecast['humidity_max'][i] is not None else "—"
        et  = f"{forecast['et0'][i]:.1f}" if forecast['et0'][i] is not None else "—"

        tn_raw = forecast['temp_min'][i]
        row_bg = C["critical_lt"] if (tn_raw is not None and tn_raw < 0) else \
                 C["terra_lt"] if (tn_raw is not None and tn_raw < 2) else \
                 (C["vellum"] if i % 2 == 0 else C["vellum_mid"])

        tn_color = C["critical"] if (tn_raw is not None and tn_raw < 0) else \
                   C["terracotta"] if (tn_raw is not None and tn_raw < 2) else C["ink"]

        mono = f"font-family:{NUM_FONT};font-size:12px;font-variant-numeric:tabular-nums;letter-spacing:0"
        td = f"padding:7px 8px;text-align:right;border-right:1px solid {C['vellum_dk']}"

        rows_html += f"""
        <tr style="background:{row_bg};">
          <td style="{td};font-weight:600;color:{C['ink']};{mono};text-align:left;">{date_lbl}</td>
          <td style="{td};color:{C['terracotta']};font-weight:600;{mono};">{tm}</td>
          <td style="{td};color:{tn_color};font-weight:600;{mono};">{tn}</td>
          <td style="{td};color:{C['ink']};{mono};">{pp}</td>
          <td style="{td};color:{C['ink']};{mono};">{pr}</td>
          <td style="{td};color:{C['ink']};{mono};">{ws}</td>
          <td style="{td};color:{C['terracotta']};{mono};">{wg}</td>
          <td style="{td};color:{C['sage']};{mono};">{hm}</td>
          <td style="{td};color:{C['amber']};{mono};">{et}</td>
        </tr>"""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;border:1px solid {C['rule']};border-radius:4px;overflow:hidden;">
      <thead>
        <tr style="background:{C['ink']};">{header_html}</tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;margin-top:8px;background:{C['vellum']};border:1px solid {C['rule']};">
      <tr>
        <td style="padding:7px 9px;border-right:1px solid {C['rule']};vertical-align:top;">
          <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:8px;letter-spacing:1px;
                      text-transform:uppercase;color:{C['ink_soft']};margin-bottom:2px;">Lluvia</div>
          <div style="font-family:Georgia,serif;font-size:11px;color:{C['ink']};">milímetros acumulados del día</div>
        </td>
        <td style="padding:7px 9px;border-right:1px solid {C['rule']};vertical-align:top;">
          <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:8px;letter-spacing:1px;
                      text-transform:uppercase;color:{C['ink_soft']};margin-bottom:2px;">Viento / Ráfaga</div>
          <div style="font-family:Georgia,serif;font-size:11px;color:{C['ink']};">velocidad máxima en km/h</div>
        </td>
        <td style="padding:7px 9px;vertical-align:top;">
          <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:8px;letter-spacing:1px;
                      text-transform:uppercase;color:{C['ink_soft']};margin-bottom:2px;">HR%</div>
          <div style="font-family:Georgia,serif;font-size:11px;color:{C['ink']};">humedad relativa máxima</div>
        </td>
      </tr>
      <tr>
        <td colspan="3" style="padding:8px 9px;border-top:1px solid {C['rule']};vertical-align:top;">
          <span style="font-family:'IBM Plex Mono',Courier,monospace;font-size:8px;letter-spacing:1px;
                       text-transform:uppercase;color:{C['amber']};">Demanda hídrica ET₀</span>
          <span style="font-family:Georgia,serif;font-size:11px;color:{C['ink_soft']};line-height:1.45;">
            mm/día estimados por calor, viento y radiación. Si supera la lluvia disponible, conviene revisar riego.
          </span>
        </td>
      </tr>
    </table>"""


def build_html(forecast: dict, alerts: list, ai_text: str, chart_b64: str) -> str:
    """Construye el cuerpo completo del email en HTML — diseño Diario de Campo."""

    months_es = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    d = date.today()
    today_str = f"{d.day} de {months_es[d.month-1]} de {d.year}"

    severity   = overall_severity(alerts)
    by_crop    = alerts_by_crop(alerts)
    n_total    = len(alerts)
    n_critical = sum(1 for a in alerts if a.severity == "crítica")
    n_high     = sum(1 for a in alerts if a.severity == "alta")

    temp_vals = [t for t in forecast["temp_min"] if t is not None]
    temp_min_str = f"{min(temp_vals):.1f}°C" if temp_vals else "—"
    temp_max_str = f"{max(t for t in forecast['temp_max'] if t is not None):.1f}°C" if forecast["temp_max"] else "—"
    rain_total = sum(p for p in forecast["precipitation"] if p is not None)

    crops_html = "".join(
        f'<table width="100%" cellpadding="0" cellspacing="0"><tbody>{_crop_row(c, by_crop[c])}</tbody></table>'
        for c in MONITORED_CROPS
    )

    chart_section = f"""
    <img src="data:image/png;base64,{chart_b64}"
         alt="Pronóstico agroclimático 7 días"
         width="620"
         style="display:block;width:100%;max-width:620px;border-radius:3px;
                border:1px solid {C['vellum_dk']};margin:0 auto;">""" if chart_b64 else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Diario de Campo — {LOCATION['name']}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    body {{ margin:0; padding:0; background:{C['vellum_mid']}; }}
    .wrap {{ max-width:660px; margin:24px auto; background:{C['white']}; }}
    h2.section {{
      font-family:'Playfair Display',Georgia,serif;
      font-size:13px; font-weight:700; letter-spacing:2px; text-transform:uppercase;
      color:{C['ink']}; margin:0 0 14px 0; padding-bottom:8px;
      border-bottom:2px solid {C['ink']}; display:block;
    }}
  </style>
</head>
<body>
<div class="wrap">

  <!-- ══ CABECERA ═════════════════════════════════════════════════════════ -->
  <div style="background:{C['ink']};padding:28px 32px 0 32px;">

    <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.55);
                margin-bottom:14px;">
      Chimbarongo · Colchagua · {today_str}
    </div>

    <h1 style="font-family:'Playfair Display',Georgia,serif;font-size:34px;
               font-weight:700;color:{C['white']};margin:0 0 6px 0;line-height:1.1;">
      Diario de Campo
    </h1>
    <p style="font-family:'Playfair Display',Georgia,serif;font-style:italic;
              font-size:14px;color:rgba(255,255,255,0.60);margin:0 0 24px 0;">
      Informe agroclimático semanal — {LOCATION['name']}
    </p>

    <!-- Estadísticas en fila -->
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-top:1px solid rgba(248,245,239,0.24);margin-top:4px;">
      <tr>
        {_stat_block(str(n_total), "alertas", C["terracotta"] if n_total > 0 else C["vellum"])}
        {_stat_block(str(n_critical), "críticas", C["critical"] if n_critical > 0 else C["vellum"])}
        {_stat_block(f"{temp_min_str}", "mín 7 días", C["vellum"])}
        <td style="padding:20px 24px;text-align:center;vertical-align:middle;border-right:none;">
          <div style="font-family:{NUM_FONT};font-size:25px;
                      font-weight:700;color:{C['vellum']};line-height:1;letter-spacing:0;
                      font-variant-numeric:tabular-nums;">{rain_total:.0f} mm</div>
          <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                      letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.55);
                      margin-top:5px;">lluvia total</div>
        </td>
      </tr>
    </table>
  </div>

  <!-- Franja de nivel de alerta -->
  {_severity_stripe(severity)}

  <!-- ══ CUERPO ════════════════════════════════════════════════════════ -->
  <div style="padding:28px 32px;">

    <!-- TABLA DE DATOS -->
    <h2 class="section">Pronóstico · 7 Días</h2>
    {_forecast_table(forecast)}

    <!-- ANÁLISIS IA -->
    <h2 class="section" style="margin-top:28px;">Análisis Agronómico</h2>
    <div style="border-left:3px solid {C['terracotta']};padding:14px 20px;
                background:{C['vellum']};border-radius:0 4px 4px 0;">
      <div style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                  letter-spacing:2px;text-transform:uppercase;color:{C['terracotta']};
                  margin-bottom:10px;">Llama 3.3-70b · Groq · Contexto agronómico regional</div>
      {_md_to_html(ai_text)}
    </div>

    <!-- GRÁFICO -->
    <h2 class="section" style="margin-top:28px;">Visualización · 7 Días</h2>
    {chart_section}

    <!-- ALERTAS -->
    <h2 class="section" style="margin-top:28px;">Alertas por Cultivo</h2>
    {crops_html}

  </div>

  <!-- ══ PIE ════════════════════════════════════════════════════════════ -->
  <div style="background:{C['ink']};padding:20px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="vertical-align:top;">
          <p style="font-family:Georgia,'Playfair Display',serif;font-size:13px;
                    font-weight:700;color:{C['vellum']};margin:0 0 3px 0;letter-spacing:0.3px;">
            Reporte Agroclimático
          </p>
          <p style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                    letter-spacing:1.5px;text-transform:uppercase;
                    color:{C['vellum_dk']};margin:0;">
            {LOCATION['name']} · {LOCATION['region']}
          </p>
        </td>
        <td style="text-align:right;vertical-align:top;">
          <p style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                    letter-spacing:1px;text-transform:uppercase;
                    color:rgba(248,245,239,0.58);margin:0 0 3px 0;">
            Datos meteorológicos
          </p>
          <p style="font-family:'IBM Plex Mono',Courier,monospace;font-size:9px;
                    letter-spacing:1px;color:rgba(248,245,239,0.42);margin:0;">
            open-meteo.com · generado automáticamente
          </p>
        </td>
      </tr>
    </table>
    <div style="border-top:1px solid rgba(255,255,255,0.08);margin-top:14px;padding-top:12px;">
      <p style="font-family:Georgia,serif;font-style:italic;font-size:10px;
                color:rgba(248,245,239,0.52);margin:0;text-align:center;">
        Este reporte es de carácter orientativo. Valida siempre con observación directa del cultivo y criterio agronómico local.
      </p>
    </div>
  </div>

</div>
</body>
</html>"""


def send_email(forecast: dict, alerts: list, ai_text: str, chart_b64: str) -> None:
    """Envía el email via Gmail SMTP usando SSL (puerto 465)."""
    sender     = os.getenv("EMAIL_SENDER")
    password   = os.getenv("EMAIL_PASSWORD")
    recipients = [r.strip() for r in os.getenv("EMAIL_RECIPIENTS", "").split(",") if r.strip()]

    if not all([sender, password, recipients]):
        raise ValueError(
            "Faltan variables en .env: EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS.\n"
            "Nota: usa Gmail App Password (no tu contraseña de cuenta)."
        )

    severity   = overall_severity(alerts)
    n_critical = sum(1 for a in alerts if a.severity == "crítica")
    n_total    = len(alerts)

    if n_critical > 0:
        prefix = f"CRÍTICO ({n_critical})"
    elif n_total > 0:
        prefix = f"{n_total} alertas"
    else:
        prefix = "Sin alertas"

    months_es = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
    d = date.today()
    date_short = f"{d.day} {months_es[d.month-1]} {d.year}"
    subject = f"[AgroCampo] {prefix} — {LOCATION['name']} · {date_short}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Diario de Campo <{sender}>"
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(build_html(forecast, alerts, ai_text, chart_b64), "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())

    print(f"  Email enviado a: {', '.join(recipients)}")
    print(f"  Asunto: {subject}")

"""
charts.py — Generación de gráficos agroclimáticos.

Diseño: paleta "Diario de Campo" — fondo vitela, colores terracota/salvia/ámbar.
Layout: 4 paneles (temperatura ancho completo + 3 paneles inferiores).
Retorna imagen PNG embebida como string base64.
"""

import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
import numpy as np
from agro_alertas.rules import format_date_es

# ─── Paleta editorial (espeja tokens del email) ─────────────────────────────

P = {
    "fig_bg":    "#F8F5EF",
    "panel_bg":  "#FDFCFA",
    "ink":       "#1C1917",
    "ink_soft":  "#78716C",
    "rule":      "#E5E0D8",
    "terra":     "#B5451B",
    "terra_lt":  "#F4C4B4",
    "sage":      "#4A7059",
    "sage_lt":   "#C8DDD0",
    "amber":     "#92400E",
    "amber_lt":  "#FDE68A",
    "frost":     "#BFDBFE",
    "frost_line":"#3B82F6",
    "pre_frost": "#FDE68A",
    "rain":      "#4A7059",
    "prob":      "#B5451B",
    "hum":       "#92400E",
    "wind":      "#44403C",
    "gusts":     "#B5451B",
    "et0":       "#92400E",
    "balance_pos":"#B5451B",
    "balance_neg":"#4A7059",
}

def _apply_style(ax):
    ax.set_facecolor(P["panel_bg"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(P["rule"])
    ax.spines["bottom"].set_color(P["rule"])
    ax.tick_params(colors=P["ink_soft"], labelsize=10, length=3)
    ax.yaxis.label.set_color(P["ink_soft"])
    ax.grid(axis="y", color=P["rule"], linewidth=0.7, linestyle="-", zorder=0)
    ax.set_axisbelow(True)

def _title(ax, text):
    ax.set_title(text, fontsize=12, fontweight="bold", color=P["ink"],
                 pad=10, loc="left", fontfamily="serif")

def _labels(dates):
    return [format_date_es(d) for d in dates]

def _safe(vals, default=0.0):
    return [v if v is not None else default for v in vals]

def _nan(vals):
    return [v if v is not None else np.nan for v in vals]


# ─── Panel 1: Temperatura ───────────────────────────────────────────────────

def _plot_temperature(ax, x, labels, f):
    tmax = _nan(f["temp_max"])
    tmin = _nan(f["temp_min"])

    all_vals = [v for v in tmin + tmax if not np.isnan(v)]
    if all_vals:
        ymin = min(min(all_vals) - 3, -1)
        ymax = max(max(all_vals) + 3, 8)
    else:
        ymin, ymax = -3, 30
    ax.set_ylim(ymin, ymax)

    ax.axhspan(ymin, 0, alpha=0.20, color=P["frost"], zorder=1, linewidth=0)
    ax.axhspan(0, 2, alpha=0.16, color=P["pre_frost"], zorder=1, linewidth=0)

    ax.fill_between(x, tmin, tmax, alpha=0.11, color=P["terra"], zorder=2)
    ax.plot(x, tmax, "o-", color=P["terra"], lw=2.1, ms=5, zorder=4, label="T. máxima")
    ax.plot(x, tmin, "o-", color=P["sage"],  lw=2.1, ms=5, zorder=4, label="T. mínima")

    ax.axhline(0, color=P["frost_line"], lw=1.1, ls="--", alpha=0.85, zorder=3)
    ax.axhline(2, color=P["frost_line"], lw=0.9, ls=":", alpha=0.65, zorder=3)
    ax.text(
        0.99,
        0 + (ymax - ymin) * 0.015,
        "Helada 0°C",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=9,
        color=P["frost_line"],
        fontweight="bold",
    )
    ax.text(
        0.99,
        2 + (ymax - ymin) * 0.015,
        "Pre-helada 2°C",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=9,
        color=P["frost_line"],
    )

    for i, (mx, mn) in enumerate(zip(tmax, tmin)):
        if not np.isnan(mx):
            ax.annotate(f"{mx:.0f}°", (x[i], mx), xytext=(0, 6),
                        textcoords="offset points", ha="center",
                        fontsize=10, color=P["terra"], fontweight="bold")
        if not np.isnan(mn):
            color_mn = P["frost_line"] if mn < 2 else P["sage"]
            weight = "bold" if mn < 2 else "normal"
            ax.annotate(f"{mn:.0f}°", (x[i], mn), xytext=(0, -11),
                        textcoords="offset points", ha="center",
                        fontsize=10, color=color_mn, fontweight=weight)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("°C", fontsize=8)
    ax.legend(
        fontsize=10,
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0, 1.02),
        labelcolor=P["ink_soft"],
        ncol=2,
        borderaxespad=0,
    )
    _title(ax, "Temperatura y Riesgo de Helada")


# ─── Panel 2: Precipitación ─────────────────────────────────────────────────

def _plot_precipitation(ax, x, labels, f):
    rain = _safe(f["precipitation"])
    prob = _safe(f["precip_probability"])
    max_rain = max(rain) if rain else 0
    significant_rain = max_rain >= 1.0

    if max_rain <= 0:
        rain_ylim = 1.0
    elif max_rain < 1.0:
        rain_ylim = 1.0
    elif max_rain < 5.0:
        rain_ylim = max(5.0, max_rain * 1.35)
    else:
        rain_ylim = max_rain * 1.25
    ax.set_ylim(0, rain_ylim)

    bar_colors = [P["sage"] if r > 0 else P["rule"] for r in rain]
    bars = ax.bar(x, rain, color=bar_colors, width=0.55, zorder=3, alpha=0.9)

    for bar, val in zip(bars, rain):
        if val <= 0:
            continue
        label = f"{val:.1f}" if val < 10 else f"{val:.0f}"
        ax.text(
            bar.get_x() + bar.get_width()/2,
            max(val, rain_ylim * 0.035) + rain_ylim * 0.025,
            label,
            ha="center",
            va="bottom",
            fontsize=10,
            color=P["sage"],
            fontweight="bold",
            clip_on=False,
        )

    ax2 = ax.twinx()
    ax2.plot(x, prob, "o--", color=P["prob"], lw=1.4, ms=4, zorder=5, alpha=0.80, label="Prob.")
    ax2.fill_between(x, 0, prob, alpha=0.05, color=P["prob"])
    ax2.set_ylim(0, 115)
    ax2.set_ylabel("Prob. %", fontsize=10, color=P["prob"])
    ax2.tick_params(axis="y", colors=P["prob"], labelsize=7.5, length=3)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color(P["rule"])

    for i, p in enumerate(prob):
        if p >= 50 or (not significant_rain and p > 0 and i in {int(np.argmax(prob))}):
            ax2.annotate(
                f"{p:.0f}%",
                (x[i], p),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=P["prob"],
                fontweight="bold",
            )

    if not significant_rain:
        ax.text(
            0.02,
            0.92,
            "Sin lluvia significativa",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=11,
            color=P["ink_soft"],
            fontstyle="italic",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, rotation=20, ha="right")
    ax.set_ylabel("mm", fontsize=8)
    _title(ax, "Precipitación y Probabilidad")


# ─── Panel 3: Humedad relativa ──────────────────────────────────────────────

def _plot_humidity(ax, x, labels, f):
    hmax  = _nan(f["humidity_max"])
    hmean = _nan(f["humidity_mean"])
    threshold = 85

    vals = [v for v in hmax + hmean if not np.isnan(v)]
    if vals and max(vals) >= 75:
        ymin = max(45, min(vals) - 12)
        ymin = min(ymin, 60)
        ymax = 105
    else:
        ymin, ymax = 0, 100

    ax.set_ylim(ymin, ymax)
    ax.axhspan(threshold, ymax, alpha=0.14, color=P["terra"], zorder=1, linewidth=0)

    ax.fill_between(x, hmean, hmax, alpha=0.10, color=P["hum"], zorder=2)
    ax.plot(x, hmax,  "o--", color=P["hum"],  lw=1.3, ms=4, alpha=0.45, zorder=3, label="HR máxima")
    ax.plot(x, hmean, "o-",  color=P["terra"], lw=2.2, ms=5, alpha=0.95, zorder=4, label="HR media")

    ax.axhline(threshold, color=P["terra"], lw=1.2, ls="--", alpha=0.75, zorder=3, label="Umbral riesgo 85%")
    ax.axhline(80, color=P["amber"], lw=0.9, ls=":",  alpha=0.5, zorder=3)

    notable = {}
    if vals:
        mean_vals = [(i, v) for i, v in enumerate(hmean) if not np.isnan(v)]
        if mean_vals:
            notable[max(mean_vals, key=lambda item: item[1])[0]] = "max"
            notable[min(mean_vals, key=lambda item: item[1])[0]] = "min"

    for i, v in enumerate(hmean):
        if not np.isnan(v):
            if v < threshold and i not in notable:
                continue
            color = P["terra"] if v >= threshold else P["hum"]
            is_min = notable.get(i) == "min"
            y_offset = -12 if is_min else 6
            va = "top" if is_min else "bottom"
            ax.annotate(f"{v:.0f}%", (x[i], v), xytext=(0, y_offset),
                        textcoords="offset points", ha="center", va=va,
                        fontsize=10, color=color, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, rotation=20, ha="right")
    ax.set_ylabel("HR %", fontsize=8)
    ax.legend(fontsize=9, frameon=False, loc="upper right", labelcolor=P["ink_soft"])
    _title(ax, "Humedad Relativa y Riesgo Fúngico")


# ─── Panel 4: Viento ────────────────────────────────────────────────────────

def _plot_wind(ax, x, labels, f):
    wspeed = _safe(f["wind_speed"])
    wgusts = _safe(f["wind_gusts"])
    threshold = 50
    max_wind = max(wspeed + wgusts) if (wspeed or wgusts) else 0
    ymax = max(threshold + 8, max_wind * 1.25, 25)
    ax.set_ylim(0, ymax)

    w = 0.32
    ax.bar(x - w/2, wspeed, w, color=P["wind"],  alpha=0.75, zorder=3, label="Velocidad máx.")
    ax.bar(x + w/2, wgusts, w, color=P["gusts"], alpha=0.72, zorder=3, label="Ráfagas")

    if ymax > threshold:
        ax.axhspan(threshold, ymax, alpha=0.08, color=P["terra"], zorder=1, linewidth=0)
        ax.axhline(threshold, color=P["terra"], lw=1.0, ls="--", alpha=0.65, zorder=3)
        ax.text(
            0.99,
            threshold + ymax * 0.015,
            "Umbral daño 50 km/h",
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="bottom",
            fontsize=9,
            color=P["terra"],
            fontweight="bold",
        )

    for i, (ws, wg) in enumerate(zip(wspeed, wgusts)):
        if ws > 0 and (max_wind >= 20 or ws >= 8):
            ax.text(x[i]-w/2, ws+0.5, f"{ws:.0f}", ha="center",
                    fontsize=9, color=P["wind"], fontweight="bold")
        if wg > 0:
            ax.text(x[i]+w/2, wg+0.5, f"{wg:.0f}", ha="center",
                    fontsize=9, color=P["gusts"], fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, rotation=20, ha="right")
    ax.set_ylabel("km/h", fontsize=8)
    ax.legend(
        fontsize=9,
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0, 1.02),
        ncol=2,
        labelcolor=P["ink_soft"],
        borderaxespad=0,
    )
    _title(ax, "Viento y Ráfagas")


# ─── Figura completa ─────────────────────────────────────────────────────────

def generate_charts(forecast: dict) -> str:
    """
    Genera la figura combinada de 4 paneles y retorna como base64 PNG.

    Layout:
      [ Temperatura — ancho completo ]
      [ Precipitación ] [ Humedad ] [ Viento ]
    """
    labels = _labels(forecast["dates"])
    x = np.arange(len(labels))

    rcParams["font.family"]    = "serif"
    rcParams["font.serif"]     = ["Georgia", "Times New Roman", "DejaVu Serif"]
    rcParams["axes.linewidth"] = 0.8

    fig = plt.figure(figsize=(14, 8.5), facecolor=P["fig_bg"])

    gs = gridspec.GridSpec(
        2, 3,
        figure=fig,
        height_ratios=[1.4, 1],
        hspace=0.52,
        wspace=0.38,
        left=0.06, right=0.97,
        top=0.93,  bottom=0.08,
    )

    ax_temp = fig.add_subplot(gs[0, :])
    ax_rain = fig.add_subplot(gs[1, 0])
    ax_hum  = fig.add_subplot(gs[1, 1])
    ax_wind = fig.add_subplot(gs[1, 2])

    for ax in [ax_temp, ax_rain, ax_hum, ax_wind]:
        _apply_style(ax)

    _plot_temperature(ax_temp, x, labels, forecast)
    _plot_precipitation(ax_rain, x, labels, forecast)
    _plot_humidity(ax_hum,  x, labels, forecast)
    _plot_wind(ax_wind, x, labels, forecast)

    fig.text(
        0.5, 0.97,
        f"Pronóstico Agroclimático — Chimbarongo, Colchagua",
        ha="center", fontsize=11.5, fontweight="bold",
        color=P["ink"], fontfamily="serif",
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight",
                facecolor=P["fig_bg"], edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

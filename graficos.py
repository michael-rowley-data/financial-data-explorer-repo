"""Figuras Plotly del Explorador de Datos Financieros.

Funciones que construyen figuras a partir de series ya calculadas. No acceden
a Streamlit directamente (solo reciben datos y devuelven ``go.Figure``), lo que
permite testearlas de forma aislada.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from calculos import (
    media_movil,
    rentabilidad_acumulada,
    serie_drawdown,
    volatilidad_movil,
)
from config import (
    ACENTO,
    ACENTO_SECUNDARIO,
    BORDE,
    ESCALAS_FECHA,
    FONDO,
    FUENTE,
    NEGATIVO,
    REJILLA,
    SUPERFICIE,
    TEXTO,
    TEXTO_SECUNDARIO,
)


def figura_base(titulo: str, titulo_y: str, altura: int = 380) -> go.Figure:
    """Lienzo común: misma tipografía, rejilla, fondo y formato de fechas."""
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15, color=TEXTO), x=0, xanchor="left"),
        height=altura,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor=SUPERFICIE,
        plot_bgcolor=SUPERFICIE,
        font=dict(family=FUENTE, size=12, color=TEXTO_SECUNDARIO),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=FONDO, bordercolor=BORDE, font=dict(color=TEXTO)),
        showlegend=False,
        separators=",.",
    )
    fig.update_xaxes(
        gridcolor=REJILLA,
        zeroline=False,
        tickformatstops=ESCALAS_FECHA,
        showspikes=True,
        spikecolor=BORDE,
    )
    fig.update_yaxes(title_text=titulo_y, gridcolor=REJILLA, zeroline=False)
    return fig


def grafico_precio(
    precios: pd.Series,
    ticker: str,
    divisa: str,
    nombre: str,
    ventana_mm: int | None = None,
) -> go.Figure:
    """Gráfico de línea del precio de cierre diario, con media móvil opcional."""
    titulo = f"Precio de cierre diario · {nombre} ({ticker})"
    fig = figura_base(titulo, f"Precio de cierre ({divisa})", altura=430)
    fig.add_trace(go.Scatter(
        x=precios.index, y=precios.values, mode="lines", name="Cierre",
        line=dict(color=ACENTO, width=2),
        hovertemplate=f"%{{x|%d/%m/%Y}}<br>Cierre: %{{y:,.2f}} {divisa}<extra></extra>",
    ))
    if ventana_mm:
        mm = media_movil(precios, ventana_mm)
        if not mm.empty:
            fig.add_trace(go.Scatter(
                x=mm.index, y=mm.values, mode="lines", name=f"Media móvil {ventana_mm}d",
                line=dict(color=ACENTO_SECUNDARIO, width=1.6, dash="dot"),
                hovertemplate=f"%{{x|%d/%m/%Y}}<br>Media móvil {ventana_mm}d: %{{y:,.2f}} {divisa}<extra></extra>",
            ))
            fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


def grafico_rentabilidad_acumulada(precios: pd.Series, ticker: str) -> go.Figure:
    """Gráfico de la rentabilidad acumulada normalizada a 100."""
    serie = rentabilidad_acumulada(precios)
    fig = figura_base(
        "Rentabilidad acumulada · base 100 al inicio del periodo",
        "Valor de la inversión (base 100)",
    )
    fig.add_hline(y=100, line_dash="dot", line_color=BORDE)
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines", name=ticker,
        line=dict(color=ACENTO, width=2),
        hovertemplate="%{x|%d/%m/%Y}<br>Valor base 100: %{y:,.2f}<extra></extra>",
    ))
    return fig


def grafico_volatilidad(precios: pd.Series, ventana: int) -> go.Figure:
    """Gráfico de la volatilidad anualizada móvil con su media del periodo."""
    serie = volatilidad_movil(precios, ventana)
    fig = figura_base(
        f"Volatilidad anualizada móvil · ventana de {ventana} sesiones",
        "Volatilidad anualizada",
    )
    fig.update_yaxes(tickformat=".1%")
    if serie.empty:
        return fig
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines", name="Volatilidad móvil",
        line=dict(color=ACENTO_SECUNDARIO, width=2),
        hovertemplate="%{x|%d/%m/%Y}<br>Volatilidad anualizada: %{y:.1%}<extra></extra>",
    ))
    media = float(serie.mean())
    fig.add_hline(
        y=media,
        line_dash="dot",
        line_color=TEXTO_SECUNDARIO,
        annotation_text=f"Media del periodo: {media:.1%}",
        annotation_position="top left",
        annotation_font=dict(color=TEXTO_SECUNDARIO, size=11),
    )
    return fig


def grafico_drawdown(precios: pd.Series) -> go.Figure:
    """Gráfico de la caída desde los máximos del periodo."""
    serie = serie_drawdown(precios)
    fig = figura_base(
        "Caída desde máximos del periodo",
        "Caída respecto al máximo",
    )
    fig.update_yaxes(tickformat=".1%")
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines", name="Caída",
        line=dict(color=NEGATIVO, width=1.6),
        fill="tozeroy", fillcolor="rgba(229, 83, 75, 0.18)",
        hovertemplate="%{x|%d/%m/%Y}<br>Caída desde máximos: %{y:.1%}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=BORDE)
    return fig


def grafico_comparacion(
    serie_principal: pd.Series,
    serie_comparada: pd.Series,
    ticker_principal: str,
    ticker_comparado: str,
) -> go.Figure:
    """Comparación de rentabilidad acumulada normalizada a 100."""
    fig = figura_base(
        "Comparación de rentabilidad acumulada · base 100 en la primera sesión común",
        "Valor de la inversión (base 100)",
        altura=430,
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(color=TEXTO_SECUNDARIO)),
    )
    fig.add_hline(y=100, line_dash="dot", line_color=BORDE)
    for serie, ticker, color in (
        (serie_principal, ticker_principal, ACENTO),
        (serie_comparada, ticker_comparado, ACENTO_SECUNDARIO),
    ):
        fig.add_trace(go.Scatter(
            x=serie.index, y=serie.values, mode="lines", name=ticker,
            line=dict(color=color, width=2),
            hovertemplate=f"%{{x|%d/%m/%Y}}<br>{ticker} (base 100): %{{y:,.2f}}<extra></extra>",
        ))
    return fig
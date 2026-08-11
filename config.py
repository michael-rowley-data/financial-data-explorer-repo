"""Configuración central del Explorador de Datos Financieros.

Concentra constantes de negocio, identidad visual y catálogos para que el
resto de módulos no repitan valores mágicos. Separar la configuración del
código facilita el mantenimiento y permite documentar cada decisión.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------
SESIONES_POR_AÑO = 252          # sesiones bursátiles aprox. de un año (EE. UU.)
VENTANA_VOLATILIDAD_DEFECTO = 21
TTL_DATOS_SEGUNDOS = 3600       # 1 hora: los precios de cierre cambian 1 vez/día

# ---------------------------------------------------------------------------
# Catálogo de activos habituales (evita consultas lentas a Yahoo para los más usados)
# ---------------------------------------------------------------------------
ACTIVOS_HABITUALES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "JPM": "JPMorgan Chase",
    "KO": "Coca-Cola",
    "XOM": "ExxonMobil",
    "SPY": "ETF sobre el S&P 500",
    "QQQ": "ETF sobre el Nasdaq 100",
}
OPCION_MANUAL = "Otro (escribir el ticker)"

PERIODOS = {
    "YTD": "ytd",
    "1Y": "1y",
    "5Y": "5y",
    "Máx": "max",
}

VENTANAS_VOLATILIDAD = {
    10: "10 sesiones (2 semanas)",
    21: "21 sesiones (1 mes)",
    42: "42 sesiones (2 meses)",
    63: "63 sesiones (1 trimestre)",
    126: "126 sesiones (medio año)",
}

# ---------------------------------------------------------------------------
# Identidad visual (paleta única reutilizada en interfaz y gráficos)
# ---------------------------------------------------------------------------
FONDO = "#0D1117"
SUPERFICIE = "#151B23"
BORDE = "#232C38"
TEXTO = "#E6EDF3"
TEXTO_SECUNDARIO = "#A8B3BF"    # contraste mejorado sobre SUPERFICIE (accesibilidad)
ACENTO = "#E0A458"              # activo principal
ACENTO_SECUNDARIO = "#5FB0A5"   # activo comparativo / volatilidad
POSITIVO = "#35C77C"
NEGATIVO = "#E5534B"
REJILLA = "#1E2632"

FUENTE = "Segoe UI, Inter, Helvetica, Arial, sans-serif"

CONFIG_PLOTLY = {"displayModeBar": False}

# Formatos de fecha numéricos: se evitan los nombres de mes en inglés.
ESCALAS_FECHA = [
    dict(dtickrange=[None, 604800000], value="%d/%m"),
    dict(dtickrange=[604800000, "M1"], value="%d/%m"),
    dict(dtickrange=["M1", "M12"], value="%m/%Y"),
    dict(dtickrange=["M12", None], value="%Y"),
]
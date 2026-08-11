"""Validación de entradas y series para el Explorador de Datos Financieros.

Funciones puras (sin dependencia de Streamlit) para poder testearlas con
pytest de forma determinista.
"""

from __future__ import annotations

import re

import pandas as pd

# Tickers de Yahoo Finance: letras, números, punto (BRK.B), guion (BTC-USD),
# circunflejo (^GSPC) e igual (EURUSD=X). Longitud razonable 1-10.
_PATRON_TICKER = re.compile(r"^[A-Z0-9.\-^=]{1,10}$")


def validar_ticker(ticker: str) -> str | None:
    """Normaliza y valida un ticker.

    Devuelve el ticker normalizado (mayúsculas, sin espacios) si es válido,
    o ``None`` si no lo es.
    """
    if not isinstance(ticker, str):
        return None
    limpio = ticker.strip().upper()
    if not limpio:
        return None
    if not _PATRON_TICKER.match(limpio):
        return None
    return limpio


def validar_serie_precios(precios: pd.Series, minimo_observaciones: int = 2) -> str | None:
    """Valida una serie de precios y devuelve el motivo de rechazo o ``None``.

    Comprueba, en orden:
    1. que sea una ``pd.Series`` no vacía;
    2. que el índice sea de fechas;
    3. que no haya fechas duplicadas;
    4. que no haya valores no finitos;
    5. que tenga al menos ``minimo_observaciones`` observaciones.
    """
    if not isinstance(precios, pd.Series) or precios.empty:
        return "La serie de precios está vacía."
    if not isinstance(precios.index, pd.DatetimeIndex):
        return "El índice de la serie no es de fechas."
    if precios.index.has_duplicates:
        return "La serie contiene fechas duplicadas."
    if not pd.api.types.is_numeric_dtype(precios):
        return "La serie contiene valores no numéricos."
    if not bool(precios.notna().all()):
        return "La serie contiene valores nulos o no finitos."
    if len(precios) < minimo_observaciones:
        return (
            f"La serie tiene {len(precios)} observaciones; "
            f"se necesitan al menos {minimo_observaciones}."
        )
    return None


def validar_ventana(ventana: int, n_observaciones: int) -> str | None:
    """Valida que una ventana móvil sea posible para el número de observaciones.

    Devuelve ``None`` si es válida o un mensaje de error en caso contrario.
    """
    if ventana < 2:
        return "La ventana debe ser de al menos 2 sesiones."
    if n_observaciones <= ventana:
        return (
            f"El periodo tiene {n_observaciones} sesiones, menos que la ventana "
            f"de {ventana} sesiones seleccionada."
        )
    return None
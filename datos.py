"""Carga y limpieza de datos desde Yahoo Finance.

Cada función decorada con ``@st.cache_data`` reduce el trabajo al evitar
descargas repetidas: los precios de cierre solo cambian una vez al día, por lo
que cachear una hora evita saturar Yahoo y acelera los reruns de la app.
"""

from __future__ import annotations

import time

import pandas as pd
import streamlit as st
import yfinance as yf

from config import ACTIVOS_HABITUALES, TTL_DATOS_SEGUNDOS
from validacion import validar_ticker

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

# Nº de reintentos y espera base (segundos) ante errores transitorios/rate limit.
MAX_REINTENTOS = 3
ESPERA_BASE_SEGUNDOS = 1.0


@st.cache_data(show_spinner=False, ttl=TTL_DATOS_SEGUNDOS)
def descargar_cieres(ticker: str, periodo: str) -> pd.Series | None:
    """Descarga la serie diaria de cierre de un ticker desde Yahoo Finance.

    Usa ``auto_adjust=True`` para que la rentabilidad del periodo refleje
    dividendos y splits. Aplica reintentos con backoff ante errores transitorios.
    Devuelve ``None`` si el ticker no existe o no hay datos suficientes.
    """
    ticker = validar_ticker(ticker)
    if ticker is None:
        return None
    cierres = _descargar_con_reintentos(ticker, periodo)
    if cierres is None:
        return None
    return _limpiar_cieres(cierres, ticker)


def _descargar_con_reintentos(ticker: str, periodo: str) -> pd.DataFrame | None:
    """Descarga con reintentos; devuelve el DataFrame raw o ``None`` si falla."""
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            datos = yf.download(
                ticker,
                period=periodo,
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            if datos is not None and not datos.empty:
                return datos
        except Exception:
            # Fallo transitorio (red, rate limit): reintentar con backoff.
            pass
        if intento < MAX_REINTENTOS:
            time.sleep(ESPERA_BASE_SEGUNDOS * intento)
    return None


def _limpiar_cieres(datos: pd.DataFrame, ticker: str) -> pd.Series | None:
    """Extrae la columna de cierre del ticker pedido y la normaliza."""
    if datos is None or datos.empty or "Close" not in datos.columns:
        return None
    cierres = datos["Close"]

    # yfinance puede devolver columnas con MultiIndex (un nivel por ticker).
    if isinstance(cierres, pd.DataFrame):
        if ticker in cierres.columns:
            cierres = cierres[ticker]
        else:
            cierres = cierres.iloc[:, 0]

    cierres = cierres.dropna()
    cierres.index = pd.to_datetime(cierres.index)
    # Se elimina la zona horaria para comparar series de forma consistente.
    if getattr(cierres.index, "tz", None) is not None:
        cierres.index = cierres.index.tz_localize(None)
    cierres = cierres.sort_index()
    # Yahoo Finance puede devolver filas duplicadas para una misma fecha; se
    # conserva la última para evitar retornos diarios distorsionados.
    if cierres.index.has_duplicates:
        cierres = cierres[~cierres.index.duplicated(keep="last")]
    cierres.name = ticker
    return cierres if len(cierres) >= 2 else None


@st.cache_data(show_spinner=False, ttl=TTL_DATOS_SEGUNDOS)
def obtener_divisa(ticker: str) -> str:
    """Divisa de cotización del activo; USD si Yahoo Finance no la informa."""
    try:
        divisa = yf.Ticker(ticker).fast_info.get("currency")
    except Exception:
        divisa = None
    return divisa if isinstance(divisa, str) and divisa else "USD"


@st.cache_data(show_spinner=False, ttl=TTL_DATOS_SEGUNDOS)
def obtener_nombre(ticker: str) -> str:
    """Nombre de la empresa; usa el catálogo habitual o consulta Yahoo Finance."""
    conocido = ACTIVOS_HABITUALES.get(ticker)
    if conocido:
        return conocido
    try:
        info = yf.Ticker(ticker).info
        nombre = info.get("shortName") or info.get("longName")
        if isinstance(nombre, str) and nombre:
            return nombre
    except Exception:
        pass
    return "Activo consultado"


def alinear_series(serie_a: pd.Series, serie_b: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Recorta ambas series a sus fechas comunes para comparar sin sesgos."""
    fechas_comunes = serie_a.index.intersection(serie_b.index)
    return serie_a.loc[fechas_comunes], serie_b.loc[fechas_comunes]
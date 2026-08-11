"""Tests deterministas de la capa de datos (sin red, sin Yahoo Finance).

Se ejercita ``_limpiar_cieres`` directamente con DataFrames sintéticos que
reproducen estructuras problemáticas reales: vacío, MultiIndex, fechas
duplicadas, ticker ausente en columnas y serie constante.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from datos import _limpiar_cieres


def _df_close(valores, fechas=None, nombre="T"):
    if fechas is None:
        fechas = pd.bdate_range("2023-01-02", periods=len(valores))
    return pd.DataFrame({"Close": valores}, index=fechas)


def test_limpiar_df_vacio():
    assert _limpiar_cieres(pd.DataFrame(), "T") is None


def test_limpiar_sin_columna_close():
    df = pd.DataFrame({"Open": [1, 2, 3]})
    assert _limpiar_cieres(df, "T") is None


def test_limpiar_serie_valida():
    df = _df_close([100.0, 101.0, 102.0])
    serie = _limpiar_cieres(df, "T")
    assert serie is not None
    assert len(serie) == 3
    assert serie.name == "T"


def test_limpiar_menor_dos_obs():
    df = _df_close([100.0])
    assert _limpiar_cieres(df, "T") is None


def test_limpiar_nan_se_eliminan():
    df = _df_close([100.0, np.nan, 102.0, 103.0])
    serie = _limpiar_cieres(df, "T")
    assert serie is not None
    assert len(serie) == 3  # el NaN desaparece
    assert 100.0 in serie.values and 102.0 in serie.values


def test_limpiar_fechas_duplicadas_se_conserva_ultima():
    fechas = pd.to_datetime(["2023-01-02", "2023-01-02", "2023-01-03"])
    df = _df_close([100.0, 999.0, 102.0], fechas=fechas)
    serie = _limpiar_cieres(df, "T")
    assert serie is not None
    # La fecha duplicada queda con el último valor (999.0), no el primero.
    assert serie.loc["2023-01-02"] == pytest.approx(999.0)
    assert len(serie) == 2


def test_limpiar_serie_constante_mantiene_dos_obs():
    # Serie constante de 5 puntos: válida (>=2), volatilidad 0 la gestiona calculos.
    df = _df_close([100.0] * 5)
    serie = _limpiar_cieres(df, "T")
    assert serie is not None
    assert len(serie) == 5


def test_limpiar_multiindex_ticker_en_columnas():
    fechas = pd.bdate_range("2023-01-02", periods=3)
    df = pd.DataFrame(
        {("Close", "AAPL"): [100.0, 101.0, 102.0], ("Close", "MSFT"): [50.0, 51.0, 52.0]},
        index=fechas,
    )
    serie = _limpiar_cieres(df, "AAPL")
    assert serie is not None
    assert list(serie.values) == [100.0, 101.0, 102.0]


def test_limpiar_multiindex_ticker_ausente_usa_primera_columna():
    fechas = pd.bdate_range("2023-01-02", periods=3)
    df = pd.DataFrame(
        {("Close", "AAPL"): [100.0, 101.0, 102.0]},
        index=fechas,
    )
    # Se pide "ZZZ" que no está en columnas -> usa la primera por robustez.
    serie = _limpiar_cieres(df, "ZZZ")
    assert serie is not None
    assert list(serie.values) == [100.0, 101.0, 102.0]


def test_limpiar_timezone_se_elimina():
    fechas = pd.bdate_range("2023-01-02", periods=3, tz="UTC")
    df = _df_close([100.0, 101.0, 102.0], fechas=fechas)
    serie = _limpiar_cieres(df, "T")
    assert serie is not None
    assert getattr(serie.index, "tz", None) is None

"""Tests deterministas de validación y formato del Explorador."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ui import clase_signo, formato_numero, formato_porcentaje, simbolo_signo
from validacion import validar_serie_precios, validar_ticker, validar_ventana


# ---------------------------------------------------------------------------
# Validación de ticker
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "ticker,esperado",
    [
        ("AAPL", "AAPL"),
        ("aapl", "AAPL"),          # normaliza a mayúsculas
        ("  msft  ", "MSFT"),      # quita espacios
        ("BRK.B", "BRK.B"),        # punto permitido
        ("BTC-USD", "BTC-USD"),    # guion permitido
        ("^GSPC", "^GSPC"),        # circunflejo permitido
        ("EURUSD=X", "EURUSD=X"),  # igual permitido
        ("SAN.MC", "SAN.MC"),
    ],
)
def test_validar_ticker_valido(ticker, esperado):
    assert validar_ticker(ticker) == esperado


@pytest.mark.parametrize(
    "ticker",
    [
        "",            # vacío
        "   ",         # solo espacios
        "AAPL;;",      # caracteres no permitidos
        "AB CD",       # espacio interno
        "A" * 11,      # demasiado largo
        "12345678901", # demasiado largo numérico
        None,          # no es string
        123,           # no es string
    ],
)
def test_validar_ticker_invalido(ticker):
    assert validar_ticker(ticker) is None


# ---------------------------------------------------------------------------
# Validación de serie de precios
# ---------------------------------------------------------------------------
def test_validar_serie_precios_valida(serie_precios):
    assert validar_serie_precios(serie_precios) is None


def test_validar_serie_precios_vacia(serie_vacia):
    assert validar_serie_precios(serie_vacia) is not None


def test_validar_serie_precios_un_punto(serie_un_punto):
    # Por defecto se exigen 2 observaciones.
    assert validar_serie_precios(serie_un_punto) is not None
    # Con mínimo 1, es válida.
    assert validar_serie_precios(serie_un_punto, minimo_observaciones=1) is None


def test_validar_serie_precios_fechas_duplicadas():
    fechas = pd.DatetimeIndex(["2023-01-02", "2023-01-02", "2023-01-03"])
    serie = pd.Series([100.0, 101.0, 102.0], index=fechas)
    assert validar_serie_precios(serie) is not None


def test_validar_serie_precios_valores_nulos():
    fechas = pd.bdate_range("2023-01-02", periods=3)
    serie = pd.Series([100.0, np.nan, 102.0], index=fechas)
    assert validar_serie_precios(serie) is not None


def test_validar_serie_precios_no_es_serie():
    assert validar_serie_precios([1, 2, 3]) is not None


# ---------------------------------------------------------------------------
# Validación de ventana
# ---------------------------------------------------------------------------
def test_validar_ventana_valida():
    assert validar_ventana(21, 250) is None


def test_validar_ventana_imposible():
    assert validar_ventana(126, 100) is not None


def test_validar_ventana_menor_que_2():
    assert validar_ventana(1, 250) is not None


# ---------------------------------------------------------------------------
# Formato español
# ---------------------------------------------------------------------------
def test_formato_numero_decimal_espanol():
    assert formato_numero(1234.5) == "1.234,50"


def test_formato_numero_entero():
    assert formato_numero(1000, 0) == "1.000"


def test_formato_porcentaje():
    assert formato_porcentaje(0.0123) == "1,23 %"


def test_formato_porcentaje_con_signo():
    assert formato_porcentaje(0.05, con_signo=True) == "+5,00 %"
    assert formato_porcentaje(-0.05, con_signo=True) == "-5,00 %"


def test_formato_porcentaje_nan():
    assert formato_porcentaje(float("nan")) == "No disponible"


# ---------------------------------------------------------------------------
# Clases y símbolos de signo
# ---------------------------------------------------------------------------
def test_clase_signo():
    assert clase_signo(0.1) == "fx-positivo"
    assert clase_signo(0.0) == "fx-positivo"
    assert clase_signo(-0.1) == "fx-negativo"


def test_simbolo_signo():
    assert simbolo_signo(0.1) == "▲"
    assert simbolo_signo(0.0) == "▲"
    assert simbolo_signo(-0.1) == "▼"
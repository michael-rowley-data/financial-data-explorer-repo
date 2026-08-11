"""Tests deterministas de las métricas financieras del Explorador."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from calculos import (
    estadisticos_retornos,
    mejor_peor_sesion,
    proporcion_dias_positivos,
    ratio_rentabilidad_volatilidad,
    rentabilidad_acumulada,
    rentabilidad_anualizada,
    rentabilidad_periodo,
    rentabilidades_diarias,
    serie_drawdown,
    sharpe_ratio,
    sortino_ratio,
    volatilidad_anualizada,
    volatilidad_movil,
)


# ---------------------------------------------------------------------------
# Rentabilidad diaria
# ---------------------------------------------------------------------------
def test_rentabilidades_diarias_serie_subida(serie_precios_subida):
    retornos = rentabilidades_diarias(serie_precios_subida)
    # Con precios crecientes lineales, todos los retornos son positivos.
    assert (retornos > 0).all()
    # El primer retorno se descarta (no hay dato anterior).
    assert len(retornos) == len(serie_precios_subida) - 1


def test_rentabilidades_diarias_serie_bajada(serie_precios_bajada):
    retornos = rentabilidades_diarias(serie_precios_bajada)
    assert (retornos < 0).all()


def test_rentabilidades_diarias_serie_vacia(serie_vacia):
    retornos = rentabilidades_diarias(serie_vacia)
    assert retornos.empty


# ---------------------------------------------------------------------------
# Rentabilidad del periodo
# ---------------------------------------------------------------------------
def test_rentabilidad_periodo_subida(serie_precios_subida):
    # 100 → 200: rentabilidad = 1.0 (100 %)
    assert rentabilidad_periodo(serie_precios_subida) == pytest.approx(1.0)


def test_rentabilidad_periodo_bajada(serie_precios_bajada):
    # 200 → 100: rentabilidad = -0.5 (-50 %)
    assert rentabilidad_periodo(serie_precios_bajada) == pytest.approx(-0.5)


def test_rentabilidad_periodo_un_punto(serie_un_punto):
    assert np.isnan(rentabilidad_periodo(serie_un_punto))


# ---------------------------------------------------------------------------
# Rentabilidad anualizada (CAGR)
# ---------------------------------------------------------------------------
def test_rentabilidad_anualizada_subida(serie_precios_subida):
    # 100 → 200 en 50 sesiones: CAGR = 2^(252/50) - 1
    esperado = 2.0 ** (252 / 50) - 1.0
    assert rentabilidad_anualizada(serie_precios_subida) == pytest.approx(esperado)


def test_rentabilidad_anualizada_un_punto(serie_un_punto):
    assert np.isnan(rentabilidad_anualizada(serie_un_punto))


def test_rentabilidad_anualizada_serie_vacia(serie_vacia):
    assert np.isnan(rentabilidad_anualizada(serie_vacia))


# ---------------------------------------------------------------------------
# Volatilidad anualizada
# ---------------------------------------------------------------------------
def test_volatilidad_anualizada_serie_constante():
    # Sin variación, la volatilidad es 0.
    precios = pd.Series([100.0] * 10, index=pd.bdate_range("2023-01-02", periods=10))
    assert volatilidad_anualizada(precios) == pytest.approx(0.0)


def test_volatilidad_anualizada_un_punto(serie_un_punto):
    assert np.isnan(volatilidad_anualizada(serie_un_punto))


def test_volatilidad_anualizada_es_positiva(serie_precios):
    assert volatilidad_anualizada(serie_precios) > 0


# ---------------------------------------------------------------------------
# Volatilidad móvil
# ---------------------------------------------------------------------------
def test_volatilidad_movil_longitud(serie_precios):
    ventana = 21
    serie = volatilidad_movil(serie_precios, ventana)
    # Se pierden (ventana) observaciones por el rolling + 1 por pct_change.
    assert len(serie) == len(serie_precios) - ventana


def test_volatilidad_movil_ventana_imposible(serie_precios):
    # Ventana mayor que el número de observaciones → serie vacía.
    serie = volatilidad_movil(serie_precios, len(serie_precios) + 10)
    assert serie.empty


# ---------------------------------------------------------------------------
# Drawdown
# ---------------------------------------------------------------------------
def test_drawdown_serie_subida(serie_precios_subida):
    caidas = serie_drawdown(serie_precios_subida)
    # En una serie creciente, el drawdown es 0 en todo momento.
    assert (caidas <= 0).all()
    assert caidas.max() == pytest.approx(0.0)


def test_drawdown_serie_bajada(serie_precios_bajada):
    caidas = serie_drawdown(serie_precios_bajada)
    # El mínimo de la serie bajista es el peor drawdown.
    assert caidas.min() == pytest.approx(-0.5)


# ---------------------------------------------------------------------------
# Rentabilidad acumulada
# ---------------------------------------------------------------------------
def test_rentabilidad_acumulada_base_100(serie_precios_subida):
    acumulada = rentabilidad_acumulada(serie_precios_subida)
    # El primer valor es 100.
    assert acumulada.iloc[0] == pytest.approx(100.0)
    # El último valor = 100 * (1 + rentabilidad_total) = 200.
    assert acumulada.iloc[-1] == pytest.approx(200.0)


def test_rentabilidad_acumulada_serie_vacia(serie_vacia):
    assert rentabilidad_acumulada(serie_vacia).empty


# ---------------------------------------------------------------------------
# % de días positivos
# ---------------------------------------------------------------------------
def test_proporcion_dias_positivos_subida(serie_precios_subida):
    assert proporcion_dias_positivos(serie_precios_subida) == pytest.approx(1.0)


def test_proporcion_dias_positivos_bajada(serie_precios_bajada):
    assert proporcion_dias_positivos(serie_precios_bajada) == pytest.approx(0.0)


def test_proporcion_dias_positivos_vacia(serie_vacia):
    assert np.isnan(proporcion_dias_positivos(serie_vacia))


# ---------------------------------------------------------------------------
# Mejor / peor sesión
# ---------------------------------------------------------------------------
def test_mejor_peor_sesion_subida(serie_precios_subida):
    mejor_fecha, mejor_ret, peor_fecha, peor_ret = mejor_peor_sesion(serie_precios_subida)
    assert mejor_ret > 0
    assert peor_ret > 0  # en una serie creciente, incluso la peor es positiva
    assert mejor_ret >= peor_ret


def test_mejor_peor_sesion_vacia(serie_vacia):
    mejor_fecha, mejor_ret, peor_fecha, peor_ret = mejor_peor_sesion(serie_vacia)
    assert np.isnan(mejor_ret)
    assert np.isnan(peor_ret)


# ---------------------------------------------------------------------------
# Ratio rentabilidad / volatilidad
# ---------------------------------------------------------------------------
def test_ratio_rentabilidad_volatilidad_subida(serie_precios_subida):
    ratio = ratio_rentabilidad_volatilidad(serie_precios_subida)
    assert ratio > 0


def test_ratio_rentabilidad_volatilidad_serie_constante():
    precios = pd.Series([100.0] * 10, index=pd.bdate_range("2023-01-02", periods=10))
    assert np.isnan(ratio_rentabilidad_volatilidad(precios))


# ---------------------------------------------------------------------------
# Sharpe Ratio (histórico)
# ---------------------------------------------------------------------------
def test_sharpe_ratio_subida(serie_precios_subida):
    # Serie creciente lineal: rentabilidad y volatilidad positivas → ratio finito.
    valor = sharpe_ratio(serie_precios_subida)
    assert np.isfinite(valor)
    assert valor > 0


def test_sharpe_ratio_serie_con_ruido(serie_precios):
    valor = sharpe_ratio(serie_precios)
    assert np.isfinite(valor)
    # Debe coincidir con (CAGR - 0) / volatilidad anualizada.
    esperado = rentabilidad_anualizada(serie_precios) / volatilidad_anualizada(serie_precios)
    assert valor == pytest.approx(esperado)


def test_sharpe_ratio_tasa_libre_riesgo():
    # Con tasa libre de riesgo positiva, el numerador se reduce; sigue finito
    # mientras haya volatilidad (una serie lineal sí la tiene).
    precios = pd.Series(
        np.linspace(100.0, 120.0, 50), index=pd.bdate_range("2023-01-02", periods=50)
    )
    valor = sharpe_ratio(precios, tasa_libre_riesgo=0.02)
    esperado = (rentabilidad_anualizada(precios) - 0.02) / volatilidad_anualizada(precios)
    assert valor == pytest.approx(esperado)


def test_sharpe_ratio_serie_vacia(serie_vacia):
    assert np.isnan(sharpe_ratio(serie_vacia))


def test_sharpe_ratio_serie_constante():
    # Sin variación no hay volatilidad → el ratio no está definido.
    precios = pd.Series([100.0] * 10, index=pd.bdate_range("2023-01-02", periods=10))
    assert not np.isfinite(sharpe_ratio(precios))


# ---------------------------------------------------------------------------
# Sortino Ratio
# ---------------------------------------------------------------------------
def test_sortino_ratio_serie_con_ruido(serie_precios):
    valor = sortino_ratio(serie_precios)
    assert np.isfinite(valor)
    # Debe coincidir con (CAGR - 0) / downside deviation anualizada.
    retornos = rentabilidades_diarias(serie_precios)
    downside = np.minimum(retornos, 0.0)
    dd = float(np.sqrt(np.mean(downside**2)) * np.sqrt(252))
    esperado = rentabilidad_anualizada(serie_precios) / dd
    assert valor == pytest.approx(esperado)


def test_sortino_ratio_subida_sin_caida():
    # Serie siempre creciente: no hay retornos negativos → downside dev = 0 → nan.
    precios = pd.Series(
        np.linspace(100.0, 200.0, 50), index=pd.bdate_range("2023-01-02", periods=50)
    )
    assert not np.isfinite(sortino_ratio(precios))


def test_sortino_ratio_serie_vacia(serie_vacia):
    assert np.isnan(sortino_ratio(serie_vacia))


# ---------------------------------------------------------------------------
# Estadísticos de retornos
# ---------------------------------------------------------------------------
def test_estadisticos_retornos_serie_con_ruido(serie_precios):
    s = estadisticos_retornos(serie_precios)
    retornos = rentabilidades_diarias(serie_precios)
    assert s["media"] == pytest.approx(float(retornos.mean()))
    assert s["volatilidad"] == pytest.approx(float(retornos.std()))
    assert np.isfinite(s["skewness"])
    assert np.isfinite(s["kurtosis"])


def test_estadisticos_retornos_serie_constante():
    precios = pd.Series([100.0] * 10, index=pd.bdate_range("2023-01-02", periods=10))
    s = estadisticos_retornos(precios)
    assert np.isnan(s["media"])
    assert np.isnan(s["volatilidad"])
    assert np.isnan(s["skewness"])
    assert np.isnan(s["kurtosis"])


# ---------------------------------------------------------------------------
# Ratio retorno/riesgo: caso conocido
# ---------------------------------------------------------------------------
def test_ratio_rentabilidad_volatilidad_caso_conocido():
    # Serie con retorno total 0.10 y volatilidad anualizada conocida.
    rng = np.random.default_rng(0)
    ret = rng.normal(0.0004, 0.01, size=252)
    precios = pd.Series(100.0 * np.cumprod(1.0 + ret), index=pd.bdate_range("2023-01-02", periods=252))
    vol = volatilidad_anualizada(precios)
    esperado = rentabilidad_periodo(precios) / vol
    assert ratio_rentabilidad_volatilidad(precios) == pytest.approx(esperado)


# ---------------------------------------------------------------------------
# Drawdown: pico y caída intermedia
# ---------------------------------------------------------------------------
def test_drawdown_pico_y_caida_intermedia():
    precios = pd.Series([100.0, 110.0, 105.0, 95.0, 100.0], index=pd.bdate_range("2023-01-02", periods=5))
    caidas = serie_drawdown(precios)
    # Máximo acumulado: 100, 110, 110, 110, 110. Caída en el índice 3 = 95/110 - 1.
    assert caidas.iloc[3] == pytest.approx(95.0 / 110.0 - 1.0)
    assert caidas.min() == pytest.approx(95.0 / 110.0 - 1.0)


# ---------------------------------------------------------------------------
# Rentabilidad acumulada: retornos mixtos conocidos
# ---------------------------------------------------------------------------
def test_rentabilidad_acumulada_mixta():
    precios = pd.Series([100.0, 110.0, 99.0], index=pd.bdate_range("2023-01-02", periods=3))
    acum = rentabilidad_acumulada(precios)
    assert acum.iloc[0] == pytest.approx(100.0)
    # 100 * 1.10 * (99/110) = 99.0
    assert acum.iloc[-1] == pytest.approx(99.0)


"""Cálculos financieros puros del Explorador de Datos Financieros.

Funciones sin dependencia de Streamlit para poder testearlas con pytest de
forma determinista. No cambian la metodología financiera existente; solo se
añaden métricas descriptivas nuevas (CAGR, % días positivos, best/worst sesión,
ratio rentabilidad/volatilidad) que refuerzan el análisis histórico.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from config import SESIONES_POR_AÑO


def rentabilidades_diarias(precios: pd.Series) -> pd.Series:
    """Variación porcentual diaria del precio de cierre."""
    return precios.pct_change().dropna()


def rentabilidad_periodo(precios: pd.Series) -> float:
    """Rentabilidad total del periodo: (último cierre / primer cierre) - 1."""
    if len(precios) < 2:
        return float("nan")
    return float(precios.iloc[-1] / precios.iloc[0] - 1.0)


def rentabilidad_anualizada(precios: pd.Series) -> float:
    """Rentabilidad anualizada (CAGR) del periodo.

    ``(1 + rentabilidad_total) ** (252 / n_sesiones) - 1``. Devuelve ``nan``
    si la rentabilidad total es <= -1 (pérdida total) o hay pocos datos.
    """
    total = rentabilidad_periodo(precios)
    n = len(precios)
    if n < 2 or not np.isfinite(total) or total <= -1.0:
        return float("nan")
    return float((1.0 + total) ** (SESIONES_POR_AÑO / n) - 1.0)


def volatilidad_anualizada(precios: pd.Series) -> float:
    """Desviación estándar de las rentabilidades diarias × √252."""
    retornos = rentabilidades_diarias(precios)
    if len(retornos) < 2:
        return float("nan")
    return float(retornos.std() * np.sqrt(SESIONES_POR_AÑO))


def volatilidad_movil(precios: pd.Series, ventana: int) -> pd.Series:
    """Volatilidad anualizada calculada sobre una ventana móvil de sesiones."""
    retornos = rentabilidades_diarias(precios)
    return (retornos.rolling(window=ventana).std() * np.sqrt(SESIONES_POR_AÑO)).dropna()


def serie_drawdown(precios: pd.Series) -> pd.Series:
    """Caída relativa respecto al máximo acumulado hasta cada fecha."""
    return (precios / precios.expanding().max()) - 1.0


def media_movil(precios: pd.Series, ventana: int) -> pd.Series:
    """Media móvil simple del precio de cierre sobre ``ventana`` sesiones."""
    return precios.rolling(window=ventana, min_periods=ventana).mean().dropna()


def rentabilidad_acumulada(precios: pd.Series) -> pd.Series:
    """Evolución acumulada de la inversión con base 100 en la primera sesión.

    Se capitalizan las rentabilidades diarias y se antepone el valor inicial
    100 en la primera fecha real de la serie, sin crear fechas artificiales.
    """
    retornos = rentabilidades_diarias(precios)
    if retornos.empty:
        return pd.Series(dtype=float)
    acumulada = (1.0 + retornos).cumprod() * 100.0
    inicio = pd.Series([100.0], index=precios.index[:1])
    return pd.concat([inicio, acumulada])


def proporcion_dias_positivos(precios: pd.Series) -> float:
    """Proporción de sesiones con rentabilidad positiva (0-1)."""
    retornos = rentabilidades_diarias(precios)
    if retornos.empty:
        return float("nan")
    return float((retornos > 0).mean())


def mejor_peor_sesion(precios: pd.Series) -> tuple[pd.Timestamp, float, pd.Timestamp, float]:
    """Devuelve (fecha_mejor, rentabilidad_mejor, fecha_peor, rentabilidad_peor)."""
    retornos = rentabilidades_diarias(precios)
    if retornos.empty:
        return pd.NaT, float("nan"), pd.NaT, float("nan")
    mejor_fecha = retornos.idxmax()
    peor_fecha = retornos.idxmin()
    return (
        mejor_fecha,
        float(retornos.loc[mejor_fecha]),
        peor_fecha,
        float(retornos.loc[peor_fecha]),
    )


def ratio_rentabilidad_volatilidad(precios: pd.Series) -> float:
    """Rentabilidad total del periodo ÷ volatilidad anualizada.

    Es una medida descriptiva de retorno por unidad de riesgo (sin ajuste por
    tipo de interés libre de riesgo). Devuelve ``nan`` si la volatilidad es 0.
    """
    vol = volatilidad_anualizada(precios)
    if not np.isfinite(vol) or vol == 0:
        return float("nan")
    return float(rentabilidad_periodo(precios) / vol)


def sharpe_ratio(precios: pd.Series, tasa_libre_riesgo: float = 0.0) -> float:
    """Sharpe Ratio anualizado (histórico) del periodo.

    Mide cuánto rendimiento extra se obtuvo por cada unidad de volatilidad
    asumida: ``(rentabilidad_anualizada - tasa_libre_riesgo) / volatilidad_anualizada``.

    Supuestos explícitos:
    - La tasa libre de riesgo es ``0`` por defecto (los tipos reales se ignoran).
    - Se usan retornos diarios y 252 sesiones/año (aprox. mercado EE. UU.).
    - Es una métrica puramente descriptiva del pasado: no anticipa el futuro.

    Devuelve ``nan`` si no hay datos suficientes o la volatilidad es 0.
    """
    ret_anual = rentabilidad_anualizada(precios)
    vol = volatilidad_anualizada(precios)
    if not np.isfinite(ret_anual) or not np.isfinite(vol) or vol == 0:
        return float("nan")
    return float((ret_anual - tasa_libre_riesgo) / vol)


def sortino_ratio(precios: pd.Series, tasa_libre_riesgo: float = 0.0) -> float:
    """Sortino Ratio anualizado (histórico) del periodo.

    Similar al Sharpe pero solo penaliza la volatilidad a la baja
    (desviación estándar de los retornos por debajo de la tasa objetivo):
    ``(rentabilidad_anualizada - tasa_libre_riesgo) / downside_deviation_anual``.

    Supuestos explícitos:
    - Tasa libre de riesgo (objetivo diaria) = 0 por defecto.
    - La downside deviation usa retornos diarios negativos respecto a 0 y se
      anualiza con √252.
    - Métrica puramente descriptiva del pasado; no anticipa el futuro.

    Devuelve ``nan`` si no hay datos suficientes o la downside deviation es 0.
    """
    retornos = rentabilidades_diarias(precios)
    if len(retornos) < 2:
        return float("nan")
    ret_anual = rentabilidad_anualizada(precios)
    objetivo_diario = tasa_libre_riesgo / SESIONES_POR_AÑO
    downsides = np.minimum(retornos - objetivo_diario, 0.0)
    downside_dev = float(np.sqrt(np.mean(downsides**2)) * np.sqrt(SESIONES_POR_AÑO))
    if not np.isfinite(ret_anual) or not np.isfinite(downside_dev) or downside_dev == 0:
        return float("nan")
    return float((ret_anual - tasa_libre_riesgo) / downside_dev)


def estadisticos_retornos(precios: pd.Series) -> dict[str, float]:
    """Estadísticos descriptivos de los retornos diarios.

    Devuelve un diccionario con:
    - ``media``: media diaria de los retornos (no anualizada).
    - ``volatilidad``: desviación estándar diaria de los retornos (no anualizada).
    - ``skewness``: asimetría (Fisher, 0 = simétrica).
    - ``kurtosis``: exceso de curtosis (Fisher, 0 = normal).

    Todos sobre retornos diarios; la anualización de media/volatilidad se hace
    explícitamente en otras funciones. Devuelve ``nan`` por clave si faltan datos.
    """
    retornos = rentabilidades_diarias(precios)
    if len(retornos) < 2:
        return {
            "media": float("nan"),
            "volatilidad": float("nan"),
            "skewness": float("nan"),
            "kurtosis": float("nan"),
        }
    vol = float(retornos.std())
    if not np.isfinite(vol) or vol == 0:
        # Sin dispersión (serie constante) estos estadísticos no aportan.
        return {
            "media": float("nan"),
            "volatilidad": float("nan"),
            "skewness": float("nan"),
            "kurtosis": float("nan"),
        }
    media = float(retornos.mean())
    skew = float(stats.skew(retornos))
    kurt = float(stats.kurtosis(retornos))  # excess kurtosis (Fisher)
    return {
        "media": media,
        "volatilidad": vol,
        "skewness": skew,
        "kurtosis": kurt,
    }
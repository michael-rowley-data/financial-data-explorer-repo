"""Fixtures de datos deterministas para los tests del Explorador."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Permite importar los módulos del proyecto (config, calculos, etc.).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _serie_sintetica(n: int = 250, tendencia: float = 0.0005, ruido: float = 0.01, semilla: int = 42) -> pd.Series:
    """Genera una serie de precios de cierre sintética y determinista."""
    rng = np.random.default_rng(semilla)
    retornos = tendencia + rng.normal(0, ruido, size=n)
    precio = 100.0 * np.cumprod(1.0 + retornos)
    fechas = pd.bdate_range("2023-01-02", periods=n)
    return pd.Series(precio, index=fechas, name="PRUEBA")


@pytest.fixture
def serie_precios() -> pd.Series:
    """Serie de precios sintética (250 sesiones, determinista)."""
    return _serie_sintetica()


@pytest.fixture
def serie_precios_subida() -> pd.Series:
    """Serie con tendencia claramente alcista (100 → sube de forma monótona aprox.)."""
    precios = np.linspace(100.0, 200.0, 50)
    fechas = pd.bdate_range("2023-01-02", periods=50)
    return pd.Series(precios, index=fechas, name="SUBIDA")


@pytest.fixture
def serie_precios_bajada() -> pd.Series:
    """Serie con tendencia claramente bajista."""
    precios = np.linspace(200.0, 100.0, 50)
    fechas = pd.bdate_range("2023-01-02", periods=50)
    return pd.Series(precios, index=fechas, name="BAJADA")


@pytest.fixture
def serie_un_punto() -> pd.Series:
    """Serie con una sola observación (caso límite)."""
    return pd.Series([100.0], index=pd.DatetimeIndex(["2023-01-02"]), name="UNO")


@pytest.fixture
def serie_vacia() -> pd.Series:
    """Serie vacía (caso límite)."""
    return pd.Series(dtype=float, name="VACIA")
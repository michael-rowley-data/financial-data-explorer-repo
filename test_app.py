"""Smoke test de la aplicación Streamlit con AppTest.

Los tests inyectan datos sintéticos mediante ``monkeypatch`` sobre las funciones
de descarga de ``datos`` para que la app sea 100 % determinista y sin red.

Flujo de AppTest: ``run()`` puebla los widgets → se modifica el widget →
``run()`` re-ejecuta con el nuevo valor.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from conftest import _serie_sintetica

RUTA_APP = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture
def datos_sinteticos(monkeypatch):
    """Sustituye las funciones de red por datos sintéticos."""
    serie = _serie_sintetica()

    def fake_descargar(ticker: str, periodo: str) -> pd.Series | None:
        return serie

    def fake_divisa(ticker: str) -> str:
        return "USD"

    def fake_nombre(ticker: str) -> str:
        return f"Empresa de prueba ({ticker})"

    monkeypatch.setattr("datos.descargar_cieres", fake_descargar)
    monkeypatch.setattr("datos.obtener_divisa", fake_divisa)
    monkeypatch.setattr("datos.obtener_nombre", fake_nombre)


def test_app_renderiza_con_datos_sinteticos(datos_sinteticos):
    """Con ticker habitual, la app renderiza KPIs, gráficos y metodología."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()

    assert not at.exception

    # Se muestran las secciones esperadas.
    html = "".join(m.value for m in at.markdown)
    assert "Explorador de Datos Financieros" in html
    assert "Métricas del periodo" in html
    assert "Análisis complementario" in html

    # Existe la pestaña de rentabilidad acumulada.
    nombres_tabs = [tab.label for tab in at.tabs]
    assert "Rentabilidad acumulada" in nombres_tabs


def test_app_estado_vacio_sin_ticker(datos_sinteticos):
    """Con "Otro (escribir el ticker)" y ticker vacío, muestra el aviso."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()  # primera ejecución: puebla los widgets

    # Seleccionamos "Otro (escribir el ticker)" en el selectbox de activo.
    at.sidebar.selectbox[0].select("Otro (escribir el ticker)")
    at.run()

    assert not at.exception
    textos = [elemento.value for elemento in at.info]
    assert any("Escribe un ticker" in texto for texto in textos)


def test_app_ticker_invalido_muestra_error(datos_sinteticos):
    """Un ticker con caracteres no permitidos muestra un error temprano."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()

    at.sidebar.selectbox[0].select("Otro (escribir el ticker)")
    at.run()  # re-ejecuta para que aparezca el text_input
    at.text_input[0].set_value("AAPL;;")
    at.run()

    assert not at.exception
    errores = [elemento.value for elemento in at.error]
    assert any("no parece válido" in texto for texto in errores)


def test_app_ticker_manual_valido(datos_sinteticos):
    """Un ticker válido escrito a mano renderiza la app sin errores."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()

    at.sidebar.selectbox[0].select("Otro (escribir el ticker)")
    at.run()
    at.text_input[0].set_value("MSFT")
    at.run()

    assert not at.exception
    html = "".join(m.value for m in at.markdown)
    assert "Métricas del periodo" in html


def test_app_periodo_valido(datos_sinteticos):
    """Seleccionar un periodo distinto sigue renderizando correctamente."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()

    at.sidebar.selectbox[1].select("5Y")
    at.run()

    assert not at.exception
    html = "".join(m.value for m in at.markdown)
    assert "Métricas del periodo" in html


def test_app_ventana_volatilidad_valida(datos_sinteticos):
    """Una ventana de volatilidad válida (42) no muestra aviso de sesiones insuficientes."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()

    at.sidebar.select_slider[0].set_value(42)
    at.run()

    assert not at.exception
    html = "".join(m.value for m in at.markdown)
    assert "Análisis complementario" in html
    textos_info = [elemento.value for elemento in at.info]
    assert not any("menos que la ventana" in texto for texto in textos_info)


def test_app_ventana_superior_a_sesiones_muestra_info(monkeypatch):
    """Ventana mayor que sesiones disponibles muestra aviso, no error."""
    rng = np.random.default_rng(7)
    retornos = 0.0005 + rng.normal(0, 0.01, size=50)
    precio = 100.0 * np.cumprod(1.0 + retornos)
    fechas = pd.bdate_range("2023-01-02", periods=50)
    serie_corta = pd.Series(precio, index=fechas, name="CORTO")

    monkeypatch.setattr("datos.descargar_cieres", lambda t, p: serie_corta)
    monkeypatch.setattr("datos.obtener_divisa", lambda t: "USD")
    monkeypatch.setattr("datos.obtener_nombre", lambda t: f"Empresa ({t})")

    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()

    at.sidebar.select_slider[0].set_value(126)
    at.run()

    assert not at.exception
    textos = [elemento.value for elemento in at.info]
    assert any("sesiones" in texto for texto in textos)


def test_app_comparacion_renderiza_tab(datos_sinteticos):
    """Marcando 'Añadir un activo de referencia' se muestra la pestaña de comparación."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=10)
    at.run()

    at.sidebar.checkbox[0].check()
    at.run()

    assert not at.exception
    nombres_tabs = [tab.label for tab in at.tabs]
    assert "Comparación" in nombres_tabs

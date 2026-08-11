"""Explorador de Datos Financieros — aplicación Streamlit.

Orquestador que conecta los módulos del proyecto:
- ``datos``: carga y limpieza de datos desde Yahoo Finance (con caché).
- ``calculos``: métricas financieras puras.
- ``graficos``: figuras Plotly.
- ``ui``: formato español, estilos y tarjetas KPI.
- ``validacion``: validación de ticker, series y ventanas.

Ejecución:
    streamlit run app.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

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
)
from config import (
    ACTIVOS_HABITUALES,
    CONFIG_PLOTLY,
    OPCION_MANUAL,
    PERIODOS,
    SESIONES_POR_AÑO,
    VENTANAS_VOLATILIDAD,
    VENTANA_VOLATILIDAD_DEFECTO,
)
from datos import alinear_series, descargar_cieres, obtener_divisa, obtener_nombre
from graficos import (
    grafico_comparacion,
    grafico_drawdown,
    grafico_precio,
    grafico_rentabilidad_acumulada,
    grafico_volatilidad,
)
from ui import (
    ESTILOS,
    clase_signo,
    formato_fecha,
    formato_importe,
    formato_numero,
    formato_porcentaje,
    simbolo_signo,
)
from validacion import validar_ticker, validar_ventana


def _configurar_pagina() -> None:
    """Configuración de Streamlit (título, icono, layout)."""
    st.set_page_config(
        page_title="Explorador de Datos Financieros",
        page_icon="▲",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(ESTILOS, unsafe_allow_html=True)


def _tarjeta_kpi(etiqueta: str, valor: str, detalle: str, clase_detalle: str = "") -> str:
    """Devuelve el HTML de una tarjeta KPI."""
    return (
        '<div class="fx-kpi">'
        f'<div class="fx-kpi-etiqueta">{etiqueta}</div>'
        f'<div class="fx-kpi-valor">{valor}</div>'
        f'<div class="fx-kpi-detalle {clase_detalle}">{detalle}</div>'
        "</div>"
    )


def _render_barra_lateral() -> tuple[str, str, str, int, bool, str]:
    """Construye la barra lateral y devuelve la selección del usuario."""
    with st.sidebar:
        st.markdown("### Selección")

        opciones_activo = [
            f"{simbolo} · {nombre}" for simbolo, nombre in ACTIVOS_HABITUALES.items()
        ] + [OPCION_MANUAL]

        eleccion = st.selectbox(
            "Activo",
            options=opciones_activo,
            index=0,
            help="Elige un activo habitual o escribe cualquier ticker de Yahoo Finance.",
        )
        if eleccion == OPCION_MANUAL:
            ticker = st.text_input(
                "Ticker",
                value="",
                placeholder="Por ejemplo: NFLX, SAN.MC, BTC-USD",
            ).strip().upper()
        else:
            ticker = eleccion.split(" · ")[0]

        etiqueta_periodo = st.selectbox(
            "Periodo",
            options=list(PERIODOS.keys()),
            index=1,
            help="Histórico que se descarga desde Yahoo Finance.",
        )
        periodo = PERIODOS[etiqueta_periodo]

        with st.expander("Ajustes del análisis"):
            ventana_volatilidad = st.select_slider(
                "Ventana de volatilidad móvil",
                options=list(VENTANAS_VOLATILIDAD.keys()),
                value=VENTANA_VOLATILIDAD_DEFECTO,
                format_func=lambda v: VENTANAS_VOLATILIDAD[v],
                help="Sesiones utilizadas para estimar la volatilidad en cada fecha.",
            )
            ventana_mm = st.select_slider(
                "Media móvil del precio",
                options=[0, 20, 50, 100, 200],
                value=0,
                format_func=lambda v: "Sin media móvil" if v == 0 else f"{v} sesiones",
                help="Suaviza la serie de cierre para visualizar la tendencia. 0 la desactiva.",
            )
            comparar = st.checkbox("Añadir un activo de referencia", value=False)
            ticker_comparado = ""
            if comparar:
                ticker_comparado = st.text_input(
                    "Ticker de referencia",
                    value="SPY",
                    placeholder="Por ejemplo: SPY, QQQ",
                ).strip().upper()

        # Validación temprana del ticker manual (UX proactiva).
        if validar_ticker(ticker) is None and ticker:
            st.error(
                "El ticker no parece válido. Usa letras, números, punto (BRK.B), "
                "guion (BTC-USD) o ^GSPC, sin espacios."
            )

        st.caption("Datos: Yahoo Finance (yfinance). Precios de cierre diarios.")

    return ticker, etiqueta_periodo, periodo, ventana_volatilidad, ventana_mm, comparar, ticker_comparado


def _render_cabecera() -> None:
    """Cabecera de la aplicación."""
    st.markdown(
        '<div class="fx-cabecera">'
        '<div class="fx-marca">Análisis histórico de mercados</div>'
        '<div class="fx-titulo">Explorador de Datos Financieros</div>'
        '<p class="fx-subtitulo">Consulta el histórico real de un activo, revisa sus '
        'métricas de rentabilidad y riesgo, y compáralo con una referencia del mercado.</p>'
        "</div>",
        unsafe_allow_html=True,
    )


def _render_contexto(ticker: str, nombre: str, etiqueta_periodo: str, precios: pd.Series, divisa: str) -> None:
    """Chips de contexto del análisis."""
    st.markdown(
        '<div class="fx-contexto">'
        f'<div class="fx-chip fx-chip-activo"><strong>{ticker}</strong> · {nombre}</div>'
        f'<div class="fx-chip">Periodo: <strong>{etiqueta_periodo}</strong></div>'
        f'<div class="fx-chip">Del <strong>{formato_fecha(precios.index[0])}</strong> '
        f'al <strong>{formato_fecha(precios.index[-1])}</strong></div>'
        f'<div class="fx-chip">Sesiones: <strong>{formato_numero(len(precios), 0)}</strong></div>'
        f'<div class="fx-chip">Divisa: <strong>{divisa}</strong></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def _render_metricas_principales(precios: pd.Series, divisa: str) -> None:
    """KPIs principales, incluida la rentabilidad anualizada (CAGR)."""
    ultimo_precio = float(precios.iloc[-1])
    variacion_sesion = float(precios.iloc[-1] / precios.iloc[-2] - 1.0)
    rentabilidad_total = float(rentabilidad_periodo(precios))
    rent_anual = rentabilidad_anualizada(precios)
    volatilidad = volatilidad_anualizada(precios)
    caidas = serie_drawdown(precios)
    caida_maxima = float(caidas.min())
    fecha_caida_maxima = caidas.idxmin()

    st.markdown('<div class="fx-seccion">Métricas del periodo</div>', unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        st.markdown(
            _tarjeta_kpi(
                "Último precio de cierre",
                formato_importe(ultimo_precio, divisa),
                f"{simbolo_signo(variacion_sesion)} Última sesión: "
                f"{formato_porcentaje(variacion_sesion, 2, con_signo=True)}",
                clase_signo(variacion_sesion),
            ),
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            _tarjeta_kpi(
                "Rentabilidad del periodo",
                formato_porcentaje(rentabilidad_total, 2, con_signo=True),
                f"{simbolo_signo(rentabilidad_total)} Desde el {formato_fecha(precios.index[0])}",
                clase_signo(rentabilidad_total),
            ),
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            _tarjeta_kpi(
                "Rentabilidad anualizada",
                formato_porcentaje(rent_anual, 2, con_signo=True),
                "CAGR del periodo (tasa anual equivalente)",
                clase_signo(rent_anual),
            ),
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            _tarjeta_kpi(
                "Volatilidad anualizada",
                formato_porcentaje(volatilidad, 2),
                "Variabilidad diaria del precio, en términos anuales",
            ),
            unsafe_allow_html=True,
        )

    with kpi5:
        st.markdown(
            _tarjeta_kpi(
                "Máxima caída del periodo",
                formato_porcentaje(caida_maxima, 2),
                f"Mínimo alcanzado el {formato_fecha(fecha_caida_maxima)}",
                "fx-negativo",
            ),
            unsafe_allow_html=True,
        )


def _render_analisis_adicional(
    precios: pd.Series, ticker: str, ventana: int, comparar: bool, ticker_comparado: str, periodo: str
) -> None:
    """Pestañas de análisis complementario y comparación."""
    st.markdown('<div class="fx-seccion">Análisis complementario</div>', unsafe_allow_html=True)

    nombres_pestañas = ["Rentabilidad acumulada", "Volatilidad móvil", "Caídas desde máximos"]
    if comparar:
        nombres_pestañas.append("Comparación")
    pestañas = st.tabs(nombres_pestañas)

    with pestañas[0]:
        st.plotly_chart(
            grafico_rentabilidad_acumulada(precios, ticker),
            width="stretch",
            config=CONFIG_PLOTLY,
        )
        st.caption(
            "Valor de una inversión de 100 unidades realizada en la primera sesión "
            "del periodo, capitalizando las rentabilidades diarias."
        )

    with pestañas[1]:
        # Validación de ventana: si es imposible, se avisa y no se dibuja.
        error_ventana = validar_ventana(ventana, len(precios))
        if error_ventana:
            st.info(error_ventana)
        else:
            st.plotly_chart(
                grafico_volatilidad(precios, ventana),
                width="stretch",
                config=CONFIG_PLOTLY,
            )
            st.caption(
                f"Cada punto resume la variabilidad de las {ventana} sesiones "
                "anteriores, expresada en términos anuales."
            )

    with pestañas[2]:
        st.plotly_chart(grafico_drawdown(precios), width="stretch", config=CONFIG_PLOTLY)
        st.caption(
            "Distancia porcentual entre el precio de cierre y el máximo alcanzado "
            "hasta esa fecha. El valor 0 % indica que el activo está en máximos."
        )

    if comparar:
        with pestañas[3]:
            _render_comparacion(precios, ticker, ticker_comparado, periodo)


def _render_comparacion(precios: pd.Series, ticker: str, ticker_comparado: str, periodo: str) -> None:
    """Descarga la referencia, alinea y muestra la comparación + KPIs."""
    if not ticker_comparado:
        st.info("Indica el ticker de referencia en la barra lateral.")
        return
    if validar_ticker(ticker_comparado) is None:
        st.error("El ticker de referencia no parece válido.")
        return
    if ticker_comparado == ticker:
        st.info("El activo de referencia debe ser distinto del activo analizado.")
        return

    with st.spinner(f"Descargando el histórico de {ticker_comparado}…"):
        precios_comparados = descargar_cieres(ticker_comparado, periodo)

    if precios_comparados is None:
        st.warning(
            f"No se han encontrado datos para «{ticker_comparado}». "
            "La comparación no está disponible."
        )
        return

    # Aviso de divisa distinta (evita comparar sin contexto).
    divisa_principal = obtener_divisa(ticker)
    divisa_referencia = obtener_divisa(ticker_comparado)
    if divisa_principal != divisa_referencia:
        st.warning(
            f"Los tickers cotizan en divisas distintas ({divisa_principal} vs "
            f"{divisa_referencia}). La comparación es orientativa y no ajusta por tipo de cambio."
        )

    base, referencia = alinear_series(precios, precios_comparados)
    if len(base) < 2:
        st.warning(
            "Los dos activos no comparten suficientes sesiones en este "
            "periodo para poder compararlos."
        )
        return

    # Aviso de datos asimétricos (honestidad analítica).
    if len(referencia) < len(precios) * 0.5:
        st.info(
            f"«{ticker_comparado}» tiene bastantes menos sesiones que «{ticker}» "
            "en este periodo; la comparación cubre solo las fechas comunes."
        )

    st.plotly_chart(
        grafico_comparacion(
            rentabilidad_acumulada(base),
            rentabilidad_acumulada(referencia),
            ticker,
            ticker_comparado,
        ),
        width="stretch",
        config=CONFIG_PLOTLY,
    )
    rent_base = float(rentabilidad_periodo(base))
    rent_referencia = float(rentabilidad_periodo(referencia))
    dif_vol = volatilidad_anualizada(base) - volatilidad_anualizada(referencia)
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.markdown(
            _tarjeta_kpi(
                f"Rentabilidad de {ticker}",
                formato_porcentaje(rent_base, 2, con_signo=True),
                "Sesiones comunes a ambos activos",
                clase_signo(rent_base),
            ),
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            _tarjeta_kpi(
                f"Rentabilidad de {ticker_comparado}",
                formato_porcentaje(rent_referencia, 2, con_signo=True),
                "Sesiones comunes a ambos activos",
                clase_signo(rent_referencia),
            ),
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            _tarjeta_kpi(
                f"Volatilidad de {ticker}",
                formato_porcentaje(volatilidad_anualizada(base), 2),
                "Riesgo anualizado (sesiones comunes)",
            ),
            unsafe_allow_html=True,
        )
    with col_d:
        st.markdown(
            _tarjeta_kpi(
                f"Volatilidad de {ticker_comparado}",
                formato_porcentaje(volatilidad_anualizada(referencia), 2),
                "Riesgo anualizado (sesiones comunes)",
            ),
            unsafe_allow_html=True,
        )
    st.caption(
        f"Diferencia de rentabilidad del periodo: {formato_porcentaje(rent_base - rent_referencia, 2, con_signo=True)}. "
        f"Diferencia de volatilidad anualizada: {formato_porcentaje(dif_vol, 2, con_signo=True)}. "
        "Ambas series se reescalan a 100 en la primera sesión que "
        "comparten, de modo que la comparación no depende del precio."
    )


def _render_metricas_adicionales(precios: pd.Series) -> None:
    """Fila de métricas descriptivas adicionales (análisis histórico)."""
    st.markdown('<div class="fx-seccion">Análisis histórico</div>', unsafe_allow_html=True)

    proporcion_positivos = proporcion_dias_positivos(precios)
    mejor_fecha, mejor_ret, peor_fecha, peor_ret = mejor_peor_sesion(precios)
    ratio = ratio_rentabilidad_volatilidad(precios)
    sharpe = sharpe_ratio(precios)
    sortino = sortino_ratio(precios)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(
            _tarjeta_kpi(
                "Días positivos",
                formato_porcentaje(proporcion_positivos, 1),
                "Sesiones con rentabilidad positiva sobre el total",
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            _tarjeta_kpi(
                "Mejor sesión",
                formato_porcentaje(mejor_ret, 2, con_signo=True),
                f"El {formato_fecha(mejor_fecha)}" if mejor_fecha is not pd.NaT else "No disponible",
                clase_signo(mejor_ret),
            ),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            _tarjeta_kpi(
                "Peor sesión",
                formato_porcentaje(peor_ret, 2, con_signo=True),
                f"El {formato_fecha(peor_fecha)}" if peor_fecha is not pd.NaT else "No disponible",
                clase_signo(peor_ret),
            ),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            _tarjeta_kpi(
                "Retorno por unidad de riesgo",
                formato_numero(ratio, 2),
                "Rentabilidad del periodo ÷ volatilidad anualizada",
            ),
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            _tarjeta_kpi(
                "Sharpe Ratio (histórico)",
                formato_numero(sharpe, 2),
                "Rentabilidad anual − 0 ÷ volatilidad anual; tasa libre de riesgo = 0",
            ),
            unsafe_allow_html=True,
        )
    with col6:
        st.markdown(
            _tarjeta_kpi(
                "Sortino Ratio (histórico)",
                formato_numero(sortino, 2),
                "Como el Sharpe, pero solo penaliza las caídas; tasa libre de riesgo = 0",
            ),
            unsafe_allow_html=True,
        )

    _render_estadisticos_retornos(precios)


def _render_estadisticos_retornos(precios: pd.Series) -> None:
    """Fila de estadísticos descriptivos de los retornos diarios."""
    st.markdown('<div class="fx-seccion">Estadísticos de los retornos diarios</div>', unsafe_allow_html=True)
    stats = estadisticos_retornos(precios)
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        st.markdown(
            _tarjeta_kpi(
                "Media diaria",
                formato_porcentaje(stats["media"] * 100, 3),
                "Retorno medio por sesión (no anualizado)",
            ),
            unsafe_allow_html=True,
        )
    with e2:
        st.markdown(
            _tarjeta_kpi(
                "Volatilidad diaria",
                formato_porcentaje(stats["volatilidad"] * 100, 3),
                "Desviación típica del retorno diario (no anualizada)",
            ),
            unsafe_allow_html=True,
        )
    with e3:
        st.markdown(
            _tarjeta_kpi(
                "Asimetría (skew)",
                formato_numero(stats["skewness"], 2),
                "0 = simétrica; >0 colas con subidas extremas",
            ),
            unsafe_allow_html=True,
        )
    with e4:
        st.markdown(
            _tarjeta_kpi(
                "Curtosis (exceso)",
                formato_numero(stats["kurtosis"], 2),
                "0 = como la normal; >0 colas más gruesas (eventos extremos)",
            ),
            unsafe_allow_html=True,
        )


def _render_exportar_csv(precios: pd.Series, ticker: str, divisa: str) -> None:
    """Botón para descargar los datos analizados en CSV."""
    retornos = rentabilidades_diarias(precios)
    df = pd.DataFrame({"cierre": precios, "retorno_diario": retornos})
    df.index.name = "fecha"
    df = df.reset_index()
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
    csv = df.to_csv(index=False, decimal=".", sep=",")
    st.download_button(
        "Descargar datos en CSV",
        data=csv,
        file_name=f"{ticker}_cierres_retornos.csv",
        mime="text/csv",
        help=f"Serie de cierres diarios y retornos diarios en {divisa}.",
    )


def _render_insights(precios: pd.Series, ticker: str, nombre: str) -> None:
    """Bloque breve de insights descriptivos basados en los datos calculados.

    Solo describe resultados observados en el periodo; no recomienda inversiones.
    """
    st.markdown('<div class="fx-seccion">Insights del periodo</div>', unsafe_allow_html=True)

    total = rentabilidad_periodo(precios)
    anual = rentabilidad_anualizada(precios)
    vol = volatilidad_anualizada(precios)
    caida = float(serie_drawdown(precios).min())
    positivos = proporcion_dias_positivos(precios)
    mejor_fecha, mejor_ret, peor_fecha, peor_ret = mejor_peor_sesion(precios)
    stats = estadisticos_retornos(precios)

    lineas = []
    lineas.append(
        f"En el periodo analizado, **{nombre} ({ticker})** cerró con una "
        f"rentabilidad del **{formato_porcentaje(total, 2, con_signo=True)}** "
        f"(anualizada: {formato_porcentaje(anual, 2, con_signo=True)})."
    )
    lineas.append(
        f"Su volatilidad anualizada fue del **{formato_porcentaje(vol, 2)}** y la "
        f"caída máxima desde máximos alcanzó el **{formato_porcentaje(caida, 2)}**."
    )
    lineas.append(
        f"El **{formato_porcentaje(positivos, 1)}** de las sesiones cerraron en "
        f"positivo; la mejor fue el {formato_fecha(mejor_fecha)} "
        f"({formato_porcentaje(mejor_ret, 2, con_signo=True)}) y la peor el "
        f"{formato_fecha(peor_fecha)} ({formato_porcentaje(peor_ret, 2, con_signo=True)})."
    )
    if np.isfinite(stats["skewness"]):
        sesgo = "hacia subidas extremas" if stats["skewness"] > 0 else "hacia caídas extremas"
        if abs(stats["skewness"]) < 0.1:
            sesgo = "prácticamente simétrica"
        lineas.append(
            f"La distribución de retornos es {sesgo} (asimetría "
            f"{formato_numero(stats['skewness'], 2)}); su exceso de curtosis es "
            f"{formato_numero(stats['kurtosis'], 2)}, lo que indica "
            f"{'colas más gruesas (eventos extremos más frecuentes)' if stats['kurtosis'] > 0 else 'colas más finas que la normal'}."
        )
    lineas.append(
        "Estos datos describen el comportamiento pasado y no anticipan el futuro."
    )
    for texto in lineas:
        st.markdown(f"- {texto}")


def _render_metodologia(ventana: int) -> None:
    """Bloque de metodología y limitaciones."""
    st.markdown('<div class="fx-seccion">Metodología y limitaciones</div>', unsafe_allow_html=True)
    with st.expander("Cómo se obtienen los datos y cómo se calcula cada métrica"):
        st.markdown(
            f"""
**Origen de los datos.** Precios diarios de cierre descargados de Yahoo Finance
con la biblioteca `yfinance`, con ajuste por dividendos y splits
(`auto_adjust=True`). Se ordenan por fecha y se descartan las sesiones sin
cotización. Los datos se guardan en caché durante una hora para evitar
descargas repetidas.

**Rentabilidad diaria.** Variación porcentual del precio de cierre entre
sesiones consecutivas.

**Rentabilidad del periodo.** Cociente entre el último y el primer cierre
disponibles, menos uno.

**Rentabilidad anualizada (CAGR).** Rentabilidad del periodo expresada en
términos anuales equivalentes: `(1 + rentabilidad_total)^(252/n_sesiones) - 1`.

**Volatilidad anualizada.** Desviación estándar de las rentabilidades diarias
multiplicada por la raíz de {SESIONES_POR_AÑO}, el número aproximado de sesiones
bursátiles de un año. La versión móvil repite ese cálculo sobre una ventana
deslizante de {ventana} sesiones.

**Máxima caída.** Diferencia porcentual entre el precio de cierre y el máximo
acumulado hasta esa fecha; se muestra el valor más negativo del periodo.

**Rentabilidad acumulada.** Capitalización de las rentabilidades diarias
partiendo de una base 100 en la primera sesión del periodo.

**Sharpe Ratio (histórico).** Mide cuánta rentabilidad extra se obtuvo por
cada unidad de volatilidad asumida: `(rentabilidad anual − tasa libre de riesgo)
÷ volatilidad anual`. Aquí la tasa libre de riesgo es 0, se usan 252 sesiones
por año y solo describe el pasado. Valores más altos indican mejor relación
retorno/riesgo, pero no predicen el futuro.

**Sortino Ratio (histórico).** Igual que el Sharpe, pero solo penaliza la
volatilidad a la baja (caídas): `(rentabilidad anual − tasa libre de riesgo)
÷ desviación a la baja anual`. Al ignorar las subidas, suele ser mayor que el
Sharpe cuando el activo cae poco. También usa tasa libre de riesgo = 0 y 252
sesiones/año, y solo describe el pasado.

**Estadísticos de retornos diarios.** Media y volatilidad diarias (sin
anualizar), asimetría (*skewness*, 0 = simétrica) y exceso de curtosis
(*kurtosis*, 0 = igual que una distribución normal). La curtosis positiva
indica colas más gruesas: eventos extremos más frecuentes de lo normal.

**Análisis histórico.** % de días positivos, mejor/peor sesión, retorno por
unidad de riesgo, Sharpe y Sortino son métricas descriptivas del pasado; no
anticipan el futuro.

**Limitaciones.**
- La cobertura y la calidad de los datos dependen íntegramente de Yahoo Finance.
- Las métricas describen el pasado y no anticipan el comportamiento futuro.
- La comparación entre activos es descriptiva: no mide causalidad ni ajusta
  por riesgo o divisa.
- Esta herramienta tiene una finalidad analítica y divulgativa; no constituye
  asesoramiento financiero ni una recomendación de inversión.
"""
        )


def main() -> None:
    """Punto de entrada de la aplicación."""
    _configurar_pagina()

    ticker, etiqueta_periodo, periodo, ventana_volatilidad, ventana_mm, comparar, ticker_comparado = (
        _render_barra_lateral()
    )
    _render_cabecera()

    if not ticker:
        st.info("Escribe un ticker en la barra lateral para comenzar el análisis.")
        st.stop()

    if validar_ticker(ticker) is None:
        st.error(
            "El ticker no parece válido. Revisa que exista en Yahoo Finance "
            "(por ejemplo, AAPL o SAN.MC)."
        )
        st.stop()

    with st.spinner(f"Descargando el histórico de {ticker}…"):
        precios = descargar_cieres(ticker, periodo)

    if precios is None:
        st.error(
            f"No se han encontrado datos para «{ticker}» en el periodo seleccionado. "
            "Revisa que el ticker exista en Yahoo Finance (por ejemplo, AAPL o SAN.MC)."
        )
        st.stop()

    divisa = obtener_divisa(ticker)
    nombre_activo = obtener_nombre(ticker)

    _render_contexto(ticker, nombre_activo, etiqueta_periodo, precios, divisa)
    _render_exportar_csv(precios, ticker, divisa)
    _render_metricas_principales(precios, divisa)
    _render_metricas_adicionales(precios)

    st.markdown('<div class="fx-seccion">Evolución del precio</div>', unsafe_allow_html=True)
    st.caption(
        "Serie de cierres diarios ajustados por dividendos y splits. "
        "Pasa el cursor por encima para ver el valor exacto de cada sesión."
    )
    st.plotly_chart(
        grafico_precio(precios, ticker, divisa, nombre_activo, ventana_mm or None),
        width="stretch",
        config=CONFIG_PLOTLY,
    )

    _render_analisis_adicional(
        precios, ticker, ventana_volatilidad, comparar, ticker_comparado, periodo
    )
    _render_insights(precios, ticker, nombre_activo)
    _render_metodologia(ventana_volatilidad)

    st.markdown(
        '<div class="fx-pie">Explorador de Datos Financieros · Datos de Yahoo Finance '
        "obtenidos con yfinance · Herramienta de análisis histórico sin fines de "
        "asesoramiento.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
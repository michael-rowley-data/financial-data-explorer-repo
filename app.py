"""Explorador de Datos Financieros — aplicación Streamlit.

Herramienta independiente para explorar el comportamiento histórico de un
activo financiero a partir de datos reales de Yahoo Finance: descarga,
transformación, métricas de rentabilidad y riesgo, y visualización interactiva.

Ejecución:
    streamlit run app.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Explorador de Datos Financieros",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Identidad visual (paleta única reutilizada en interfaz y gráficos)
# ---------------------------------------------------------------------------
FONDO = "#0D1117"
SUPERFICIE = "#151B23"
BORDE = "#232C38"
TEXTO = "#E6EDF3"
TEXTO_SECUNDARIO = "#93A1B1"
ACENTO = "#E0A458"          # activo principal
ACENTO_SECUNDARIO = "#5FB0A5"  # activo comparativo / volatilidad
POSITIVO = "#35C77C"
NEGATIVO = "#E5534B"
REJILLA = "#1E2632"

FUENTE = "Segoe UI, Inter, Helvetica, Arial, sans-serif"

CONFIG_PLOTLY = {"displayModeBar": False}

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------
SESIONES_POR_AÑO = 252
VENTANA_VOLATILIDAD_DEFECTO = 21

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
    "6 meses": "6mo",
    "1 año": "1y",
    "2 años": "2y",
    "3 años": "3y",
    "5 años": "5y",
    "Máximo histórico": "max",
}

VENTANAS_VOLATILIDAD = {
    10: "10 sesiones (2 semanas)",
    21: "21 sesiones (1 mes)",
    42: "42 sesiones (2 meses)",
    63: "63 sesiones (1 trimestre)",
    126: "126 sesiones (medio año)",
}

# Formatos de fecha numéricos: se evitan los nombres de mes en inglés.
ESCALAS_FECHA = [
    dict(dtickrange=[None, 604800000], value="%d/%m"),
    dict(dtickrange=[604800000, "M1"], value="%d/%m"),
    dict(dtickrange=["M1", "M12"], value="%m/%Y"),
    dict(dtickrange=["M12", None], value="%Y"),
]

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
ESTILOS = f"""
<style>
.stApp {{ background-color: {FONDO}; }}
.block-container {{ max-width: 1240px; padding-top: 2.2rem; padding-bottom: 3rem; }}

[data-testid="stSidebar"] {{
    background-color: #10161E;
    border-right: 1px solid {BORDE};
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.6rem; }}

h1, h2, h3, h4 {{ color: {TEXTO}; font-family: {FUENTE}; letter-spacing: -0.01em; }}
p, li, label, span {{ font-family: {FUENTE}; }}

.fx-cabecera {{ border-bottom: 1px solid {BORDE}; padding-bottom: 1.1rem; margin-bottom: 1.4rem; }}
.fx-marca {{
    font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: {ACENTO}; font-weight: 600; margin-bottom: 0.35rem;
}}
.fx-titulo {{ font-size: 2.05rem; font-weight: 650; color: {TEXTO}; margin: 0 0 0.35rem 0; }}
.fx-subtitulo {{ font-size: 0.97rem; color: {TEXTO_SECUNDARIO}; margin: 0; max-width: 720px; line-height: 1.5; }}

.fx-contexto {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.3rem; }}
.fx-chip {{
    background: {SUPERFICIE}; border: 1px solid {BORDE}; border-radius: 999px;
    padding: 0.3rem 0.85rem; font-size: 0.8rem; color: {TEXTO_SECUNDARIO};
}}
.fx-chip strong {{ color: {TEXTO}; font-weight: 600; }}
.fx-chip-activo {{ border-color: {ACENTO}; color: {ACENTO}; }}
.fx-chip-activo strong {{ color: {ACENTO}; }}

.fx-kpi {{
    background: {SUPERFICIE}; border: 1px solid {BORDE}; border-left: 3px solid {ACENTO};
    border-radius: 10px; padding: 1rem 1.1rem; height: 100%;
}}
.fx-kpi-etiqueta {{
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: {TEXTO_SECUNDARIO}; margin-bottom: 0.45rem;
}}
.fx-kpi-valor {{ font-size: 1.6rem; font-weight: 640; color: {TEXTO}; line-height: 1.15; white-space: nowrap; }}
.fx-kpi-detalle {{ font-size: 0.78rem; color: {TEXTO_SECUNDARIO}; margin-top: 0.4rem; }}
.fx-positivo {{ color: {POSITIVO}; }}
.fx-negativo {{ color: {NEGATIVO}; }}

.fx-seccion {{
    font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em;
    color: {TEXTO_SECUNDARIO}; font-weight: 600;
    margin: 2.2rem 0 0.6rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid {BORDE};
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 1.6rem; border-bottom: 1px solid {BORDE}; }}
.stTabs [data-baseweb="tab"] {{ color: {TEXTO_SECUNDARIO}; font-size: 0.9rem; padding: 0.4rem 0; }}
.stTabs [aria-selected="true"] {{ color: {TEXTO}; }}

div[data-testid="stExpander"] {{ border: 1px solid {BORDE}; border-radius: 10px; background: {SUPERFICIE}; }}

.fx-pie {{
    margin-top: 2.4rem; padding-top: 1rem; border-top: 1px solid {BORDE};
    font-size: 0.78rem; color: {TEXTO_SECUNDARIO};
}}
</style>
"""
st.markdown(ESTILOS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Utilidades de formato (notación española: coma decimal, punto de millares)
# ---------------------------------------------------------------------------
def formato_numero(valor: float, decimales: int = 2) -> str:
    """Devuelve el número con separador decimal ',' y de millares '.'."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def formato_importe(valor: float, divisa: str) -> str:
    return f"{formato_numero(valor)} {divisa}"


def formato_porcentaje(valor: float, decimales: int = 2, con_signo: bool = False) -> str:
    """Formatea una proporción (0,0123) como porcentaje (1,23 %)."""
    if pd.isna(valor):
        return "No disponible"
    signo = "+" if con_signo and valor > 0 else ""
    return f"{signo}{formato_numero(valor * 100, decimales)} %"


def formato_fecha(fecha: pd.Timestamp) -> str:
    return fecha.strftime("%d/%m/%Y")


def clase_signo(valor: float) -> str:
    return "fx-positivo" if valor >= 0 else "fx-negativo"


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def descargar_cierres(ticker: str, periodo: str) -> pd.Series | None:
    """Descarga la serie diaria de precios de cierre desde Yahoo Finance.

    Devuelve ``None`` si el ticker no existe o no hay datos suficientes.
    """
    try:
        datos = yf.download(
            ticker, period=periodo, interval="1d", progress=False, auto_adjust=False
        )
    except Exception:
        return None

    if datos is None or datos.empty or "Close" not in datos.columns:
        return None

    cierres = datos["Close"]
    # yfinance puede devolver columnas con MultiIndex (un nivel por ticker).
    if isinstance(cierres, pd.DataFrame):
        cierres = cierres.iloc[:, 0]

    cierres = cierres.dropna()
    cierres.index = pd.to_datetime(cierres.index)
    cierres = cierres.sort_index()
    cierres.name = ticker

    return cierres if len(cierres) >= 2 else None


@st.cache_data(show_spinner=False, ttl=3600)
def obtener_divisa(ticker: str) -> str:
    """Divisa de cotización del activo; USD si Yahoo Finance no la informa."""
    try:
        divisa = yf.Ticker(ticker).fast_info.get("currency")
    except Exception:
        divisa = None
    return divisa if isinstance(divisa, str) and divisa else "USD"


@st.cache_data(show_spinner=False, ttl=3600)
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


# ---------------------------------------------------------------------------
# Cálculos
# ---------------------------------------------------------------------------
def rentabilidades_diarias(precios: pd.Series) -> pd.Series:
    """Variación porcentual diaria del precio de cierre."""
    return precios.pct_change().dropna()


def rentabilidad_periodo(precios: pd.Series) -> float:
    """Rentabilidad total del periodo: (último cierre / primer cierre) - 1."""
    return (precios.iloc[-1] / precios.iloc[0]) - 1.0


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


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
def figura_base(titulo: str, titulo_y: str, altura: int = 380) -> go.Figure:
    """Lienzo común: misma tipografía, rejilla, fondo y formato de fechas."""
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15, color=TEXTO), x=0, xanchor="left"),
        height=altura,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor=SUPERFICIE,
        plot_bgcolor=SUPERFICIE,
        font=dict(family=FUENTE, size=12, color=TEXTO_SECUNDARIO),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=FONDO, bordercolor=BORDE, font=dict(color=TEXTO)),
        showlegend=False,
        separators=",.",
    )
    fig.update_xaxes(
        gridcolor=REJILLA,
        zeroline=False,
        tickformatstops=ESCALAS_FECHA,
        showspikes=False,
    )
    fig.update_yaxes(title_text=titulo_y, gridcolor=REJILLA, zeroline=False)
    return fig


def grafico_precio(precios: pd.Series, ticker: str, divisa: str, nombre: str) -> go.Figure:
    titulo = f"Precio de cierre diario · {nombre} ({ticker})"
    fig = figura_base(titulo, f"Precio ({divisa})", altura=430)
    fig.add_trace(go.Scatter(
        x=precios.index, y=precios.values, mode="lines", name=ticker,
        line=dict(color=ACENTO, width=2),
        hovertemplate="%{x|%d/%m/%Y}<br>Cierre: %{y:,.2f} " + divisa + "<extra></extra>",
    ))
    return fig


def grafico_rentabilidad_acumulada(precios: pd.Series, ticker: str) -> go.Figure:
    serie = rentabilidad_acumulada(precios)
    fig = figura_base(
        "Rentabilidad acumulada · base 100 al inicio del periodo",
        "Valor de la inversión (base 100)",
    )
    fig.add_hline(y=100, line_dash="dot", line_color=BORDE)
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines", name=ticker,
        line=dict(color=ACENTO, width=2),
        hovertemplate="%{x|%d/%m/%Y}<br>Valor acumulado: %{y:,.2f}<extra></extra>",
    ))
    return fig


def grafico_volatilidad(precios: pd.Series, ventana: int) -> go.Figure:
    serie = volatilidad_movil(precios, ventana)
    fig = figura_base(
        f"Volatilidad anualizada móvil · ventana de {ventana} sesiones",
        "Volatilidad anualizada",
    )
    fig.update_yaxes(tickformat=".0%")
    if serie.empty:
        return fig
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines", name="Volatilidad móvil",
        line=dict(color=ACENTO_SECUNDARIO, width=2),
        hovertemplate="%{x|%d/%m/%Y}<br>Volatilidad: %{y:.2%}<extra></extra>",
    ))
    media = float(serie.mean())
    fig.add_hline(
        y=media,
        line_dash="dot",
        line_color=TEXTO_SECUNDARIO,
        annotation_text=f"Media del periodo: {formato_porcentaje(media, 1)}",
        annotation_position="top left",
        annotation_font=dict(color=TEXTO_SECUNDARIO, size=11),
    )
    return fig


def grafico_drawdown(precios: pd.Series) -> go.Figure:
    serie = serie_drawdown(precios)
    fig = figura_base(
        "Caída desde máximos históricos del periodo",
        "Caída respecto al máximo",
    )
    fig.update_yaxes(tickformat=".0%")
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines", name="Caída",
        line=dict(color=NEGATIVO, width=1.6),
        fill="tozeroy", fillcolor="rgba(229, 83, 75, 0.18)",
        hovertemplate="%{x|%d/%m/%Y}<br>Caída: %{y:.2%}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=BORDE)
    return fig


def grafico_comparacion(
    serie_principal: pd.Series,
    serie_comparada: pd.Series,
    ticker_principal: str,
    ticker_comparado: str,
) -> go.Figure:
    fig = figura_base(
        "Comparación de rentabilidad acumulada · base 100 en la primera sesión común",
        "Valor de la inversión (base 100)",
        altura=430,
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(color=TEXTO_SECUNDARIO)),
    )
    fig.add_hline(y=100, line_dash="dot", line_color=BORDE)
    for serie, ticker, color in (
        (serie_principal, ticker_principal, ACENTO),
        (serie_comparada, ticker_comparado, ACENTO_SECUNDARIO),
    ):
        fig.add_trace(go.Scatter(
            x=serie.index, y=serie.values, mode="lines", name=ticker,
            line=dict(color=color, width=2),
            hovertemplate=f"{ticker}: " + "%{y:,.2f}<extra></extra>",
        ))
    return fig


# ---------------------------------------------------------------------------
# Componentes de interfaz
# ---------------------------------------------------------------------------
def tarjeta_kpi(etiqueta: str, valor: str, detalle: str, clase_detalle: str = "") -> str:
    return (
        '<div class="fx-kpi">'
        f'<div class="fx-kpi-etiqueta">{etiqueta}</div>'
        f'<div class="fx-kpi-valor">{valor}</div>'
        f'<div class="fx-kpi-detalle {clase_detalle}">{detalle}</div>'
        "</div>"
    )


def alinear_series(serie_a: pd.Series, serie_b: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Recorta ambas series a sus fechas comunes para comparar sin sesgos."""
    fechas_comunes = serie_a.index.intersection(serie_b.index)
    return serie_a.loc[fechas_comunes], serie_b.loc[fechas_comunes]


# ---------------------------------------------------------------------------
# Barra lateral — selección
# ---------------------------------------------------------------------------
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
        comparar = st.checkbox("Añadir un activo de referencia", value=False)
        ticker_comparado = ""
        if comparar:
            ticker_comparado = st.text_input(
                "Ticker de referencia",
                value="SPY",
                placeholder="Por ejemplo: SPY, QQQ",
            ).strip().upper()

    st.caption("Datos: Yahoo Finance (yfinance). Precios de cierre diarios.")


# ---------------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="fx-cabecera">'
    '<div class="fx-marca">Análisis histórico de mercados</div>'
    '<div class="fx-titulo">Explorador de Datos Financieros</div>'
    '<p class="fx-subtitulo">Consulta el histórico real de un activo, revisa sus '
    'métricas de rentabilidad y riesgo, y compáralo con una referencia del mercado.</p>'
    "</div>",
    unsafe_allow_html=True,
)

if not ticker:
    st.info("Escribe un ticker en la barra lateral para comenzar el análisis.")
    st.stop()

with st.spinner(f"Descargando el histórico de {ticker}…"):
    precios = descargar_cierres(ticker, periodo)

if precios is None:
    st.error(
        f"No se han encontrado datos para «{ticker}» en el periodo seleccionado. "
        "Revisa que el ticker exista en Yahoo Finance (por ejemplo, AAPL o SAN.MC)."
    )
    st.stop()

divisa = obtener_divisa(ticker)
nombre_activo = obtener_nombre(ticker)

# ---------------------------------------------------------------------------
# Contexto del análisis
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="fx-contexto">'
    f'<div class="fx-chip fx-chip-activo"><strong>{ticker}</strong> · {nombre_activo}</div>'
    f'<div class="fx-chip">Periodo: <strong>{etiqueta_periodo}</strong></div>'
    f'<div class="fx-chip">Del <strong>{formato_fecha(precios.index[0])}</strong> '
    f'al <strong>{formato_fecha(precios.index[-1])}</strong></div>'
    f'<div class="fx-chip">Sesiones: <strong>{formato_numero(len(precios), 0)}</strong></div>'
    f'<div class="fx-chip">Divisa: <strong>{divisa}</strong></div>'
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Métricas principales
# ---------------------------------------------------------------------------
ultimo_precio = float(precios.iloc[-1])
variacion_sesion = float(precios.iloc[-1] / precios.iloc[-2] - 1.0)
rentabilidad_total = float(rentabilidad_periodo(precios))
volatilidad = volatilidad_anualizada(precios)
caidas = serie_drawdown(precios)
caida_maxima = float(caidas.min())
fecha_caida_maxima = caidas.idxmin()

st.markdown('<div class="fx-seccion">Métricas del periodo</div>', unsafe_allow_html=True)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        tarjeta_kpi(
            "Último precio de cierre",
            formato_importe(ultimo_precio, divisa),
            f"Última sesión: {formato_porcentaje(variacion_sesion, 2, con_signo=True)}",
            clase_signo(variacion_sesion),
        ),
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        tarjeta_kpi(
            "Rentabilidad del periodo",
            formato_porcentaje(rentabilidad_total, 2, con_signo=True),
            f"Desde el {formato_fecha(precios.index[0])}",
            clase_signo(rentabilidad_total),
        ),
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        tarjeta_kpi(
            "Volatilidad anualizada",
            formato_porcentaje(volatilidad, 2),
            "Variabilidad diaria del precio, en términos anuales",
        ),
        unsafe_allow_html=True,
    )

with kpi4:
    st.markdown(
        tarjeta_kpi(
            "Máxima caída del periodo",
            formato_porcentaje(caida_maxima, 2),
            f"Mínimo alcanzado el {formato_fecha(fecha_caida_maxima)}",
            "fx-negativo",
        ),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Gráfico principal
# ---------------------------------------------------------------------------
st.markdown('<div class="fx-seccion">Evolución del precio</div>', unsafe_allow_html=True)
st.plotly_chart(
    grafico_precio(precios, ticker, divisa, nombre_activo),
    width="stretch",
    config=CONFIG_PLOTLY,
)

# ---------------------------------------------------------------------------
# Análisis complementario
# ---------------------------------------------------------------------------
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
    if len(precios) > ventana_volatilidad:
        st.plotly_chart(
            grafico_volatilidad(precios, ventana_volatilidad),
            width="stretch",
            config=CONFIG_PLOTLY,
        )
        st.caption(
            f"Cada punto resume la variabilidad de las {ventana_volatilidad} sesiones "
            "anteriores, expresada en términos anuales."
        )
    else:
        st.info(
            f"El periodo seleccionado tiene {formato_numero(len(precios), 0)} sesiones, "
            f"menos que la ventana de {ventana_volatilidad} sesiones elegida. "
            "Selecciona un periodo más largo o una ventana inferior."
        )

with pestañas[2]:
    st.plotly_chart(grafico_drawdown(precios), width="stretch", config=CONFIG_PLOTLY)
    st.caption(
        "Distancia porcentual entre el precio de cierre y el máximo alcanzado "
        "hasta esa fecha. El valor 0 % indica que el activo está en máximos."
    )

if comparar:
    with pestañas[3]:
        if not ticker_comparado:
            st.info("Indica el ticker de referencia en la barra lateral.")
        elif ticker_comparado == ticker:
            st.info("El activo de referencia debe ser distinto del activo analizado.")
        else:
            with st.spinner(f"Descargando el histórico de {ticker_comparado}…"):
                precios_comparados = descargar_cierres(ticker_comparado, periodo)

            if precios_comparados is None:
                st.warning(
                    f"No se han encontrado datos para «{ticker_comparado}». "
                    "La comparación no está disponible."
                )
            else:
                base, referencia = alinear_series(precios, precios_comparados)
                if len(base) < 2:
                    st.warning(
                        "Los dos activos no comparten suficientes sesiones en este "
                        "periodo para poder compararlos."
                    )
                else:
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
                    diferencia = rent_base - rent_referencia
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown(
                            tarjeta_kpi(
                                f"Rentabilidad de {ticker}",
                                formato_porcentaje(rent_base, 2, con_signo=True),
                                "Sesiones comunes a ambos activos",
                                clase_signo(rent_base),
                            ),
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        st.markdown(
                            tarjeta_kpi(
                                f"Rentabilidad de {ticker_comparado}",
                                formato_porcentaje(rent_referencia, 2, con_signo=True),
                                "Sesiones comunes a ambos activos",
                                clase_signo(rent_referencia),
                            ),
                            unsafe_allow_html=True,
                        )
                    with col_c:
                        st.markdown(
                            tarjeta_kpi(
                                "Diferencia",
                                formato_porcentaje(diferencia, 2, con_signo=True),
                                f"{ticker} frente a {ticker_comparado}",
                                clase_signo(diferencia),
                            ),
                            unsafe_allow_html=True,
                        )
                    st.caption(
                        "Ambas series se reescalan a 100 en la primera sesión que "
                        "comparten, de modo que la comparación no depende del precio."
                    )

# ---------------------------------------------------------------------------
# Metodología
# ---------------------------------------------------------------------------
st.markdown('<div class="fx-seccion">Metodología y limitaciones</div>', unsafe_allow_html=True)
with st.expander("Cómo se obtienen los datos y cómo se calcula cada métrica"):
    st.markdown(
        f"""
**Origen de los datos.** Precios diarios de cierre descargados de Yahoo Finance
con la biblioteca `yfinance`. Se ordenan por fecha y se descartan las sesiones
sin cotización. Los datos se guardan en caché durante una hora para evitar
descargas repetidas.

**Rentabilidad diaria.** Variación porcentual del precio de cierre entre
sesiones consecutivas.

**Rentabilidad del periodo.** Cociente entre el último y el primer cierre
disponibles, menos uno.

**Volatilidad anualizada.** Desviación estándar de las rentabilidades diarias
multiplicada por la raíz de {SESIONES_POR_AÑO}, el número aproximado de sesiones
bursátiles de un año. La versión móvil repite ese cálculo sobre una ventana
deslizante de {ventana_volatilidad} sesiones.

**Máxima caída.** Diferencia porcentual entre el precio de cierre y el máximo
acumulado hasta esa fecha; se muestra el valor más negativo del periodo.

**Rentabilidad acumulada.** Capitalización de las rentabilidades diarias
partiendo de una base 100 en la primera sesión del periodo.

**Limitaciones.**
- Solo se utilizan precios de cierre: no se consideran dividendos, splits
  posteriores ni operaciones intradía.
- La cobertura y la calidad de los datos dependen íntegramente de Yahoo Finance.
- Las métricas describen el pasado y no anticipan el comportamiento futuro.
- La comparación entre activos es descriptiva: no mide causalidad ni ajusta
  por riesgo o divisa.
- Esta herramienta tiene una finalidad analítica y divulgativa; no constituye
  asesoramiento financiero ni una recomendación de inversión.
"""
    )

st.markdown(
    '<div class="fx-pie">Explorador de Datos Financieros · Datos de Yahoo Finance '
    "obtenidos con yfinance · Herramienta de análisis histórico sin fines de "
    "asesoramiento.</div>",
    unsafe_allow_html=True,
)
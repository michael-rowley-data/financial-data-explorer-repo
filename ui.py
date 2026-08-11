"""Componentes de interfaz y formato del Explorador de Datos Financieros.

Funciones de presentación: formato numérico en español, estilos CSS y tarjetas
KPI. Las funciones de formato son puras y testables; las de interfaz dependen
de Streamlit o devuelven HTML.
"""

from __future__ import annotations

import pandas as pd

from config import (
    ACENTO,
    ACENTO_SECUNDARIO,
    BORDE,
    FONDO,
    FUENTE,
    NEGATIVO,
    POSITIVO,
    SUPERFICIE,
    TEXTO,
    TEXTO_SECUNDARIO,
)

# ---------------------------------------------------------------------------
# Formato (notación española: coma decimal, punto de millares)
# ---------------------------------------------------------------------------
def formato_numero(valor: float, decimales: int = 2) -> str:
    """Devuelve el número con separador decimal ',' y de millares '.'."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def formato_importe(valor: float, divisa: str, decimales: int = 2) -> str:
    """Formatea un importe con su divisa."""
    return f"{formato_numero(valor, decimales)} {divisa}"


def formato_porcentaje(valor: float, decimales: int = 2, con_signo: bool = False) -> str:
    """Formatea una proporción (0,0123) como porcentaje (1,23 %)."""
    if pd.isna(valor):
        return "No disponible"
    signo = "+" if con_signo and valor > 0 else ""
    return f"{signo}{formato_numero(valor * 100, decimales)} %"


def formato_fecha(fecha: pd.Timestamp) -> str:
    """Formatea una fecha en formato español dd/mm/aaaa."""
    return fecha.strftime("%d/%m/%Y")


def clase_signo(valor: float) -> str:
    """Clase CSS según el signo del valor (positivo/negativo)."""
    return "fx-positivo" if valor >= 0 else "fx-negativo"


def simbolo_signo(valor: float) -> str:
    """Símbolo visible ▲/▼ además del color para accesibilidad."""
    return "▲" if valor >= 0 else "▼"


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
ESTILOS = f"""
<style>
:root {{
    --fx-fondo: {FONDO};
    --fx-superficie: {SUPERFICIE};
    --fx-borde: {BORDE};
    --fx-texto: {TEXTO};
    --fx-texto-2: {TEXTO_SECUNDARIO};
    --fx-acento: {ACENTO};
    --fx-acento-2: {ACENTO_SECUNDARIO};
    --fx-positivo: {POSITIVO};
    --fx-negativo: {NEGATIVO};
    --fx-fuente: {FUENTE};
    --fx-radio: 12px;
    --fx-sombra: 0 1px 2px rgba(0, 0, 0, 0.25), 0 4px 12px rgba(0, 0, 0, 0.18);
}}

* {{ font-family: var(--fx-fuente); }}
.stApp {{ background-color: var(--fx-fondo); }}
.block-container {{ max-width: 1240px; padding-top: 2.4rem; padding-bottom: 3.2rem; }}

/* ---- Barra lateral: contenedor de control homogéneo ---- */
[data-testid="stSidebar"] {{
    background-color: #0F141B;
    border-right: 1px solid var(--fx-borde);
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.8rem; padding-left: 1.4rem; padding-right: 1.4rem; }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
    font-size: 0.95rem; letter-spacing: 0.01em; color: var(--fx-texto);
}}
[data-testid="stSidebar"] hr {{ border-color: var(--fx-borde); margin: 1rem 0; }}

/* ---- Tipografía base ---- */
h1, h2, h3, h4 {{ color: var(--fx-texto); font-family: var(--fx-fuente); letter-spacing: -0.015em; }}
p, li, label, span, div {{ font-family: var(--fx-fuente); }}
.stMarkdown, .stCaption {{ color: var(--fx-texto-2); }}

/* ---- Cabecera ---- */
.fx-cabecera {{
    display: flex; flex-direction: column; gap: 0.35rem;
    border-bottom: 1px solid var(--fx-borde);
    padding-bottom: 1.3rem; margin-bottom: 1.6rem;
}}
.fx-marca {{
    font-size: 0.72rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--fx-acento); font-weight: 600; margin: 0;
}}
.fx-titulo {{
    font-size: 2.1rem; font-weight: 680; color: var(--fx-texto);
    margin: 0; line-height: 1.1; letter-spacing: -0.02em;
}}
.fx-subtitulo {{
    font-size: 0.98rem; color: #C2CBD6; margin: 0.15rem 0 0 0;
    max-width: 760px; line-height: 1.55;
}}

/* ---- Chips de contexto ---- */
.fx-contexto {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.5rem; }}
.fx-chip {{
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: var(--fx-superficie); border: 1px solid var(--fx-borde);
    border-radius: 999px; padding: 0.32rem 0.8rem;
    font-size: 0.78rem; color: var(--fx-texto-2); line-height: 1.2;
}}
.fx-chip strong {{ color: var(--fx-texto); font-weight: 600; }}
.fx-chip-activo {{ border-color: var(--fx-acento); color: var(--fx-acento); background: rgba(224, 164, 88, 0.08); }}
.fx-chip-activo strong {{ color: var(--fx-acento); }}

/* ---- Tarjetas KPI: equilibradas y con profundidad sutil ---- */
.fx-kpi {{
    display: flex; flex-direction: column; justify-content: space-between;
    background: linear-gradient(180deg, #18202B 0%, var(--fx-superficie) 100%);
    border: 1px solid var(--fx-borde);
    border-left: 3px solid var(--fx-acento);
    border-radius: var(--fx-radio);
    padding: 1.05rem 1.15rem; height: 100%;
    box-shadow: var(--fx-sombra);
}}
.fx-kpi-etiqueta {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em;
    color: var(--fx-texto-2); margin: 0 0 0.5rem 0;
}}
.fx-kpi-valor {{
    font-size: 1.62rem; font-weight: 660; color: var(--fx-texto);
    line-height: 1.1; white-space: nowrap; margin: 0;
}}
.fx-kpi-detalle {{ font-size: 0.8rem; color: var(--fx-texto-2); margin: 0.55rem 0 0 0; line-height: 1.35; }}
.fx-positivo {{ color: var(--fx-positivo); }}
.fx-negativo {{ color: var(--fx-negativo); }}

/* ---- Separadores de sección ---- */
.fx-seccion {{
    font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.14em;
    color: #C2CBD6; font-weight: 600;
    margin: 2.4rem 0 0.9rem 0; padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--fx-borde);
}}

/* ---- Selectores y botones homogéneos ---- */
.stSelectbox > div > div, .stTextInput > div > div, .stSlider {{
    border-radius: 9px;
}}
.stButton > button, .stDownloadButton > button {{
    border-radius: 9px; border: 1px solid var(--fx-borde);
    background: var(--fx-superficie); color: var(--fx-texto);
    font-weight: 600; transition: border-color 0.15s ease, background 0.15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    border-color: var(--fx-acento); background: #1B2330;
}}

/* ---- Pestañas con indicador ---- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 1.4rem; border-bottom: 1px solid var(--fx-borde);
}}
.stTabs [data-baseweb="tab"] {{
    color: var(--fx-texto-2); font-size: 0.9rem; padding: 0.5rem 0;
    border-bottom: 2px solid transparent;
}}
.stTabs [aria-selected="true"] {{
    color: var(--fx-texto); font-weight: 600;
    border-bottom: 2px solid var(--fx-acento);
}}

/* ---- Expanders coherentes ---- */
div[data-testid="stExpander"] {{
    border: 1px solid var(--fx-borde); border-radius: var(--fx-radio);
    background: var(--fx-superficie);
}}
div[data-testid="stExpander"] summary {{ color: var(--fx-texto); font-weight: 500; }}

/* ---- Pie ---- */
.fx-pie {{
    margin-top: 2.8rem; padding-top: 1.1rem; border-top: 1px solid var(--fx-borde);
    font-size: 0.78rem; color: var(--fx-texto-2); line-height: 1.5;
}}
</style>
"""

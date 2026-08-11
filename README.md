# Explorador de Datos Financieros

Aplicación de análisis descriptivo de activos financieros construida con
Streamlit. Descarga el histórico real de cotizaciones desde Yahoo Finance y
presenta métricas, visualizaciones interactivas y un resumen de *insights*
sobre el comportamiento pasado de un activo. Es una herramienta de consulta,
**no** predictiva ni de asesoramiento.

## Propósito

Permitir a cualquier persona (con conocimientos básicos de finanzas o datos)
explorar el comportamiento histórico de un activo —rentabilidad, riesgo y
forma de la distribución de retornos— sin escribir código, mediante una
interfaz clara y profesional.

## Funcionalidades reales

- **Selección de activo:** lista de activos habituales o ticker manual
  (cualquier símbolo de Yahoo Finance).
- **Periodos:** YTD, 1Y, 5Y y Máx (histórico).
- **Métricas principales:** último precio, rentabilidad del periodo,
  rentabilidad anualizada (CAGR), volatilidad anualizada y máxima caída.
- **Análisis histórico:** % de días positivos, mejor/peor sesión, ratio
  retorno/riesgo, **Sharpe** y **Sortino** (históricos, tasa libre de
  riesgo = 0).
- **Estadísticos de retornos diarios:** media, volatilidad, asimetría
  (*skewness*) y exceso de curtosis (*kurtosis*).
- **Visualizaciones (Plotly):** precio con media móvil opcional,
  rentabilidad acumulada base 100, volatilidad móvil y drawdown.
- **Comparación con referencia:** dos activos normalizados a 100, con
  rentabilidad y volatilidad de cada uno.
- **Exportación CSV** de la serie de cierres y retornos diarios.
- **Insights** descriptivos generados a partir de las métricas calculadas.
- **Metodología y limitaciones** documentadas en la propia app.

## Stack tecnológico

| Tecnología | Uso |
|---|---|
| Python 3.10.9 | Lenguaje |
| Streamlit | Aplicación web |
| pandas / numpy | Procesamiento de datos |
| scipy | Estadísticos de retornos (skew/kurtosis) |
| yfinance | Descarga de datos (Yahoo Finance) |
| Plotly | Gráficos interactivos |

## Fuente de datos

[Yahoo Finance](https://finance.yahoo.com) vía `yfinance`. Precios de cierre
diarios con ajuste por dividendos y splits (`auto_adjust=True`), ordenados por
fecha y sin sesiones sin cotización. Se cachean 1 hora (`@st.cache_data`) para
evitar descargas repetidas. La cobertura y calidad dependen de Yahoo Finance.

## Metodología analítica

- **Retorno diario:** `pct_change()` sobre el cierre.
- **Retorno del periodo:** `cierre_final / cierre_inicial − 1`.
- **CAGR:** `(1 + retorno_periodo)^(252 / n_sesiones) − 1`.
- **Volatilidad anualizada:** desviación típica de retornos diarios × √252.
- **Volatilidad móvil:** igual, sobre una ventana deslizante (defecto 21).
- **Máxima caída:** `precio / máximo acumulado − 1` (valor más negativo).
- **Sharpe / Sortino:** `(CAGR − 0) / volatilidad` y `(CAGR − 0) /
  desviación a la baja`, anualizados con √252. Tasa libre de riesgo = 0.
- **Estadísticos:** media y volatilidad diarias, *skewness* y exceso de
  *kurtosis* (Fisher) de los retornos diarios.
- **Comparación:** ambas series reescaladas a 100 en su primera sesión común.

Todas las métricas describen el **pasado**; no son predicciones.

## Estructura del proyecto

```
financial_data_explorer/
├── app.py            # Orquestador Streamlit y layout de la UI
├── config.py         # Constantes, catálogos y paleta visual
├── datos.py          # Descarga y limpieza (yfinance + caché)
├── calculos.py       # Métricas financieras puras (testeables)
├── graficos.py       # Figuras Plotly
├── ui.py             # Formato español, estilos CSS y tarjetas KPI
├── validacion.py     # Validación de ticker, series y ventanas
├── requirements.txt
├── README.md
└── tests/            # pytest + AppTest (Streamlit)
```

## Instalación

Requiere Python 3.10.9.

```bash
cd financial_data_explorer
python -m venv venv        # opcional pero recomendado
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución (Streamlit)

```bash
streamlit run app.py
```

La app se abre en el navegador. Escribe o elige un ticker, selecciona periodo
y (opcionalmente) un activo de referencia para comparar.

## Ejecución de tests

```bash
pytest
```

Incluye tests unitarios de `calculos` y `validacion`, y `AppTest` (Streamlit)
que renderiza la app con datos sintéticos y sin red.

## Limitaciones conocidas

- Datos puramente históricos; no anticipan el futuro ni recomiendan inversiones.
- Calidad y cobertura dependen de Yahoo Finance.
- La comparación entre activos es descriptiva: no ajusta por divisa ni riesgo.
- Sin gestión de cartera, modelos predictivos, sentimiento ni Monte Carlo.
- La tasa libre de riesgo se asume 0 (no se introducen tipos reales).

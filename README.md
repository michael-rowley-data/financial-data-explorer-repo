# Explorador de Datos Financieros

Herramienta de exploración histórica de activos financieros construida con
Streamlit. Permite descargar datos reales de Yahoo Finance y analizar rápidamente
el comportamiento de un activo mediante métricas y visualizaciones interactivas.

## Para quién es

Diseñada para personas con conocimientos básicos/intermedios de finanzas o
datos que quieren explorar el comportamiento histórico de un activo sin
escribir código.

## Funcionalidades

- **Selección de activo:** introduce o elige un ticker de la lista.
- **Selección de periodo:** 6 meses, 1 año, 2 años, 3 años, 5 años o
  máximo histórico.
- **Métricas principales:** último precio, rentabilidad del periodo,
  volatilidad anualizada y máxima caída (maximum drawdown).
- **Visualizaciones interactivas (Plotly):**
  1. Precio histórico.
  2. Rentabilidad acumulada normalizada a 100.
  3. Volatilidad anualizada móvil (ventana ajustable).
  4. Drawdown (caída desde máximos).
- **Comparación opcional:** compara dos activos normalizados a 100.
- **Metodología y limitaciones:** sección desplegable con explicación de
  cálculos y limitaciones.
- **Gestión de errores:** mensajes comprensibles en español para tickers
  inválidos, descargas vacías o datos insuficientes.

## Stack

| Tecnología | Uso |
|---|---|
| Python 3.10.9 | Lenguaje |
| Streamlit | Framework web |
| pandas / numpy | Procesamiento de datos |
| yfinance | Descarga de datos (Yahoo Finance) |
| Plotly | Visualizaciones interactivas |

## Instalación

```bash
cd financial_data_explorer
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

## Metodología básica

- **Rentabilidad diaria:** `pct_change()` sobre el precio de cierre.
- **Rentabilidad del periodo:** `(precio_final / precio_inicial) - 1`.
- **Volatilidad anualizada:** desviación estándar de rentabilidades diarias × √252.
- **Volatilidad móvil:** ventana de 21 sesiones por defecto (ajustable).
- **Maximum drawdown:** `precio / máximo acumulado - 1` (valor mínimo).
- **Rentabilidad acumulada:** normalizada a 100 en el primer día.

## Limitaciones

- Los datos son históricos y no garantizan resultados futuros.
- La calidad depende de Yahoo Finance.
- No constituye asesoramiento financiero.
- La comparación entre activos es puramente informativa.

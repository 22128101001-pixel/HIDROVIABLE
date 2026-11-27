import io
import math
from datetime import date

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as backend_pdf
import numpy_financial as npf
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Informe PDF | HIDROVIABLE",
    page_icon="📄",
    layout="wide",
)

st.title("Descargar informe en PDF")
st.write(
    "Configura los mismos supuestos de la evaluación y genera un informe descargable "
    "con los parámetros, indicadores y proyección financiera del proyecto."
)
st.info(
    "Esta es una página independiente: ingresa aquí los valores que quieras incluir "
    "en el informe."
)

with st.sidebar:
    st.subheader("Datos para el informe")
    with st.expander("1 · Recurso hídrico", expanded=True):
        q_lps = st.number_input("Caudal aprovechable (L/s)", min_value=0.0, value=300.0, step=10.0)
        h_bruta = st.number_input("Altura bruta (m)", min_value=0.0, value=30.0, step=1.0)
        perdidas = st.number_input("Pérdidas de carga (m)", min_value=0.0, value=5.0, step=0.5)

    with st.expander("2 · Parámetros técnicos", expanded=True):
        eficiencia_pct = st.slider("Eficiencia global (%)", 10, 95, 75)
        factor_pct = st.slider("Factor de capacidad (%)", 1, 100, 60)

    with st.expander("3 · Supuestos financieros", expanded=True):
        inversion = st.number_input("Inversión inicial (S/)", min_value=0.0, value=450000.0, step=10000.0)
        costo_om = st.number_input("Operación y mantenimiento anual (S/)", min_value=0.0, value=18000.0, step=1000.0)
        tarifa = st.number_input("Valor de electricidad (S/kWh)", min_value=0.0, value=0.50, step=0.05, format="%.3f")
        tasa_pct = st.number_input("Tasa de descuento (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        vida = st.number_input("Vida útil (años)", min_value=1, max_value=60, value=20, step=1)

    with st.expander("4 · Supuestos adicionales"):
        crecimiento = st.number_input("Crecimiento anual de ingresos (%)", min_value=-50.0, max_value=50.0, value=0.0, step=1.0)
        crecimiento_costos = st.number_input("Crecimiento anual de costos (%)", min_value=-20.0, max_value=50.0, value=0.0, step=1.0)
        valor_residual = st.number_input("Valor residual (S/)", min_value=0.0, value=0.0, step=1000.0)

q = q_lps / 1000
h_neta = h_bruta - perdidas
if q <= 0 or h_neta <= 0:
    st.error("El caudal y la altura neta deben ser mayores que cero. Revisa los datos ingresados.")
    st.stop()

eficiencia = eficiencia_pct / 100
factor = factor_pct / 100
tasa = tasa_pct / 100
potencia_kw = 9.81 * q * h_neta * eficiencia
energia_dia = potencia_kw * 24 * factor
energia_anual = potencia_kw * 8760 * factor
ingreso_anual = energia_anual * tarifa

flujos = [-inversion]
for ano in range(1, int(vida) + 1):
    ingresos_ano = ingreso_anual * ((1 + crecimiento / 100) ** (ano - 1))
    costos_ano = costo_om * ((1 + crecimiento_costos / 100) ** (ano - 1))
    flujo = ingresos_ano - costos_ano
    if ano == int(vida):
        flujo += valor_residual
    flujos.append(flujo)

van = sum(flujos[t] / ((1 + tasa) ** t) for t in range(1, len(flujos))) - inversion
try:
    valor_tir = npf.irr(flujos)
    tir = float(valor_tir) if valor_tir is not None and math.isfinite(float(valor_tir)) else None
except (ValueError, OverflowError, TypeError):
    tir = None

acumulado = -inversion
pri = None
for ano, flujo in enumerate(flujos[1:], start=1):
    anterior = acumulado
    acumulado += flujo
    if acumulado >= 0:
        pri = (ano - 1) + (-anterior / flujo) if flujo > 0 else float(ano)
        break

if van > 0 and tir is not None and tir > tasa:
    conclusion = "Preliminarmente favorable: el VAN es positivo y la TIR supera la tasa de descuento."
elif van < 0 or (tir is not None and tir < tasa):
    conclusion = "Preliminarmente no favorable bajo los supuestos ingresados."
else:
    conclusion = "No se puede emitir una conclusión definitiva con los supuestos disponibles."

tabla = pd.DataFrame({
    "Año": list(range(0, int(vida) + 1)),
    "Flujo de caja (S/)": flujos,
    "Flujo acumulado (S/)": pd.Series(flujos).cumsum(),
})

st.subheader("Vista previa del informe")
metricas = st.columns(4)
metricas[0].metric("Potencia estimada", f"{potencia_kw:,.2f} kW")
metricas[1].metric("Generación anual", f"{energia_anual:,.0f} kWh")
metricas[2].metric("Valor Actual Neto", f"S/ {van:,.2f}")
metricas[3].metric("Tasa Interna de Retorno", "No calculable" if tir is None else f"{tir * 100:,.2f}%")
st.caption(conclusion)
with st.expander("Revisar proyección anual"):
    st.dataframe(
        tabla.style.format({"Flujo de caja (S/)": "S/ {:,.2f}", "Flujo acumulado (S/)": "S/ {:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )


def crear_informe_pdf():
    salida = io.BytesIO()
    with backend_pdf.PdfPages(salida) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        fig.text(0.09, 0.94, "HIDROVIABLE", fontsize=12, color="#2a7b67", weight="bold")
        fig.text(0.09, 0.895, "Informe preliminar de viabilidad hidroeléctrica", fontsize=19, color="#16324f", weight="bold")
        fig.text(0.09, 0.865, f"Generado el {date.today().strftime('%d/%m/%Y')}", fontsize=10, color="#647684")
        fig.text(0.09, 0.81, "Resumen ejecutivo", fontsize=13, color="#16324f", weight="bold")
        resumen = [
            ("Potencia estimada", f"{potencia_kw:,.2f} kW"),
            ("Generación diaria", f"{energia_dia:,.0f} kWh"),
            ("Generación anual", f"{energia_anual:,.0f} kWh"),
            ("Ingreso anual estimado", f"S/ {ingreso_anual:,.2f}"),
            ("Valor Actual Neto (VAN)", f"S/ {van:,.2f}"),
            ("Tasa Interna de Retorno (TIR)", "No calculable" if tir is None else f"{tir * 100:,.2f}%"),
            ("Recuperación simple", "No se recupera" if pri is None else f"{pri:,.2f} años"),
        ]
        y = 0.77
        for etiqueta, valor in resumen:
            fig.text(0.11, y, etiqueta, fontsize=10, color="#526675")
            fig.text(0.57, y, valor, fontsize=10, color="#1c2b36", weight="bold")
            y -= 0.042
        fig.text(0.09, y - 0.01, "Conclusión preliminar", fontsize=13, color="#16324f", weight="bold")
        fig.text(0.09, y - 0.045, conclusion, fontsize=10, color="#1c2b36", wrap=True)
        fig.text(0.09, y - 0.12, "Parámetros del proyecto", fontsize=13, color="#16324f", weight="bold")
        parametros = [
            f"Caudal aprovechable: {q_lps:,.1f} L/s ({q:.3f} m³/s)",
            f"Altura bruta: {h_bruta:,.2f} m  |  Pérdidas de carga: {perdidas:,.2f} m  |  Altura neta: {h_neta:,.2f} m",
            f"Eficiencia global: {eficiencia_pct}%  |  Factor de capacidad: {factor_pct}%",
            f"Inversión inicial: S/ {inversion:,.2f}  |  Operación y mantenimiento anual: S/ {costo_om:,.2f}",
            f"Tarifa eléctrica: S/ {tarifa:,.3f}/kWh  |  Tasa de descuento: {tasa_pct:.1f}%  |  Vida útil: {int(vida)} años",
            f"Crecimiento de ingresos: {crecimiento:.1f}%  |  Crecimiento de costos: {crecimiento_costos:.1f}%  |  Valor residual: S/ {valor_residual:,.2f}",
        ]
        y_param = y - 0.16
        for texto in parametros:
            fig.text(0.11, y_param, texto, fontsize=9, color="#1c2b36")
            y_param -= 0.035
        fig.text(0.09, 0.08, "Evaluación preliminar; no sustituye estudios de ingeniería, hidrología, ambiente o finanzas.", fontsize=8, color="#647684")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig2, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis("off")
        ax.set_title("Proyección del flujo de caja", fontsize=16, color="#16324f", weight="bold", pad=22)
        filas = [[f"{int(fila['Año'])}", f"S/ {fila['Flujo de caja (S/)']:,.2f}", f"S/ {fila['Flujo acumulado (S/)']:,.2f}"] for _, fila in tabla.iterrows()]
        tabla_pdf = ax.table(
            cellText=filas,
            colLabels=["Año", "Flujo de caja", "Flujo acumulado"],
            loc="upper center",
            cellLoc="right",
            colLoc="right",
            colWidths=[0.16, 0.38, 0.42],
        )
        tabla_pdf.auto_set_font_size(False)
        tabla_pdf.set_fontsize(8)
        tabla_pdf.scale(1, 1.35)
        for (fila, _), celda in tabla_pdf.get_celld().items():
            celda.set_edgecolor("#dfe7ec")
            if fila == 0:
                celda.set_facecolor("#16324f")
                celda.get_text().set_color("white")
                celda.get_text().set_weight("bold")
            elif fila % 2 == 0:
                celda.set_facecolor("#f4f7f9")
        fig2.text(0.09, 0.04, "Los resultados dependen de los supuestos ingresados y deben validarse con estudios especializados.", fontsize=8, color="#647684")
        pdf.savefig(fig2, bbox_inches="tight")
        plt.close(fig2)

    salida.seek(0)
    return salida.getvalue()


st.download_button(
    label="📄 Descargar informe completo en PDF",
    data=crear_informe_pdf(),
    file_name="informe_hidroviable.pdf",
    mime="application/pdf",
    type="primary",
    use_container_width=True,
)
st.caption("El PDF incluye los datos ingresados, indicadores calculados y la proyección anual del flujo de caja.")

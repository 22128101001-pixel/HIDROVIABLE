import io
import math
from datetime import date

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as backend_pdf
import numpy_financial as npf
import pandas as pd
import streamlit as st

LOGO_PATH = "Logo.png"

st.set_page_config(
    page_title="HIDROVIABLE | Plataforma de Evaluación Energética",
    page_icon=LOGO_PATH,
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700&display=swap');
:root { --navy:#16324f; --blue:#1f5c99; --green:#2a7b67; --ink:#1c2b36; --muted:#647684; --line:#dfe7ec; --surface:#f4f7f9; }
html, body, [class*="css"] { font-family:'Inter',sans-serif; }
.stApp { background:var(--surface); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(244,247,249,.92); }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
.block-container { max-width:1480px; padding:1.25rem 2rem 3rem; }
.brandbar { display:flex; align-items:center; justify-content:space-between; min-height:112px; border:1px solid var(--line); border-radius:10px; background:#fff; padding:8px 18px 8px 12px; margin-bottom:1.1rem; box-shadow:0 2px 8px rgba(22,50,79,.035); }
.brand-logo { display:block; height:94px; width:auto; max-width:62%; object-fit:contain; }
.status { color:var(--green); background:#edf6f3; border:1px solid #d8e9e3; border-radius:20px; padding:.42rem .75rem; font-size:.75rem; font-weight:700; }
.page-head { margin:.35rem 0 1.25rem; }
.page-head h1 { font-family:'Manrope',sans-serif; color:var(--navy); font-size:2rem; margin:0 0 .25rem; }
.page-head p { color:var(--muted); margin:0; }
div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:8px; padding:1.05rem 1.15rem; min-height:112px; box-shadow:0 2px 7px rgba(22,50,79,.025); }
div[data-testid="stMetricLabel"] { color:var(--muted); font-size:.82rem; font-weight:600; }
div[data-testid="stMetricValue"] { color:var(--navy); font-family:'Manrope',sans-serif; font-size:1.55rem; }
.panel { background:#fff; border:1px solid var(--line); border-radius:8px; padding:1.25rem; box-shadow:0 2px 7px rgba(22,50,79,.025); }
.section-title { color:var(--navy); font-family:'Manrope',sans-serif; font-size:1.08rem; font-weight:700; margin-bottom:.9rem; }
[data-testid="stTabs"] [role="tab"] { font-weight:600; color:var(--muted); }
[data-testid="stTabs"] [aria-selected="true"] { color:var(--blue); border-bottom-color:var(--blue); }
.disclaimer { background:#eef4f8; border-left:3px solid var(--blue); border-radius:4px; color:#526675; font-size:.82rem; padding:.75rem .9rem; margin-bottom:1.2rem; }
.download-card { background:#fff; border:1px solid var(--line); border-left:4px solid var(--green); border-radius:8px; padding:1.25rem 1.4rem; margin-top:.5rem; }
[data-testid="stExpander"] { border:1px solid var(--line)!important; border-radius:6px!important; background:#fff; }
hr { border-color:var(--line); }
@media (max-width:700px) { .block-container{padding-left:1rem;padding-right:1rem;} .brandbar{min-height:82px;padding:6px 10px;} .brand-logo{height:68px;max-width:82%;} .status{display:none;} }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image(LOGO_PATH, use_container_width=True)
    st.caption("Plataforma de Evaluación Energética")
    st.divider()
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

st.markdown(f"""
<div class="brandbar"><img class="brand-logo" src="{LOGO_PATH}" alt="HIDROVIABLE"><div class="status">ANÁLISIS PRELIMINAR</div></div>
<div class="page-head"><h1>Evaluación de viabilidad hidroeléctrica</h1><p>Estimación técnica, energética y financiera de pequeñas centrales hidroeléctricas.</p></div>
<div class="disclaimer">Nota técnica: los resultados constituyen una evaluación preliminar y no sustituyen estudios especializados de ingeniería, hidrología, ambiente o finanzas.</div>
""", unsafe_allow_html=True)

q = q_lps / 1000
h_neta = h_bruta - perdidas
eficiencia = eficiencia_pct / 100
factor = factor_pct / 100
tasa = tasa_pct / 100
if h_neta <= 0:
    st.error("La altura neta debe ser mayor que cero. Revise la altura bruta y las pérdidas de carga.")
    st.stop()
if q <= 0:
    st.error("El caudal aprovechable debe ser mayor que cero.")
    st.stop()

potencia_kw = 9.81 * q * h_neta * eficiencia
energia_dia = potencia_kw * 24 * factor
energia_anual = potencia_kw * 8760 * factor
ingreso_anual = energia_anual * tarifa
flujos = [-inversion]
for ano in range(1, int(vida) + 1):
    ingreso_ano = ingreso_anual * ((1 + crecimiento / 100) ** (ano - 1))
    costo_ano = costo_om * ((1 + crecimiento_costos / 100) ** (ano - 1))
    flujo = ingreso_ano - costo_ano
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

tabla = pd.DataFrame({
    "Año": list(range(0, int(vida) + 1)),
    "Flujo de caja (S/)": flujos,
    "Flujo acumulado (S/)": pd.Series(flujos).cumsum(),
})


def crear_informe_pdf():
    buffer = io.BytesIO()
    navy, green, muted, ink = "#16324f", "#2a7b67", "#647684", "#1c2b36"
    if van > 0 and tir is not None and tir > tasa:
        conclusion = "Resultado preliminar favorable: el VAN es positivo y la TIR supera la tasa de descuento."
    elif van < 0 or (tir is not None and tir < tasa):
        conclusion = "Resultado preliminar no favorable bajo los supuestos ingresados."
    else:
        conclusion = "No se puede emitir una conclusión definitiva con los supuestos disponibles."

    with backend_pdf.PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        fig.add_artist(plt.Rectangle((0, .955), 1, .045, transform=fig.transFigure, color=navy, zorder=-1))
        fig.add_artist(plt.Rectangle((0, .948), 1, .007, transform=fig.transFigure, color=green, zorder=-1))
        try:
            logo = plt.imread(LOGO_PATH)
            logo_ax = fig.add_axes([.07, .865, .22, .075])
            logo_ax.imshow(logo)
            logo_ax.axis("off")
        except (FileNotFoundError, OSError):
            fig.text(.07, .895, "HIDROVIABLE", fontsize=16, weight="bold", color=green)
        fig.text(.52, .905, "INFORME DE VIABILIDAD", fontsize=15, weight="bold", color=navy)
        fig.text(.52, .879, "PEQUEÑA CENTRAL HIDROELÉCTRICA", fontsize=8.5, weight="bold", color=green)
        fig.text(.52, .856, f"Fecha de emisión: {date.today().strftime('%d/%m/%Y')}", fontsize=8, color=muted)

        fig.text(.07, .812, "1. RESUMEN EJECUTIVO", fontsize=12, weight="bold", color=navy)
        fig.lines.append(plt.Line2D([.07, .93], [.797, .797], transform=fig.transFigure, color="#dfe7ec", lw=1))
        indicadores = [
            ("Potencia estimada", f"{potencia_kw:,.2f} kW"),
            ("Generación diaria", f"{energia_dia:,.0f} kWh"),
            ("Generación anual", f"{energia_anual:,.0f} kWh"),
            ("Ingreso anual estimado", f"S/ {ingreso_anual:,.2f}"),
            ("Valor Actual Neto (VAN)", f"S/ {van:,.2f}"),
            ("Tasa Interna de Retorno (TIR)", "No calculable" if tir is None else f"{tir*100:,.2f}%"),
            ("Recuperación simple", "No se recupera" if pri is None else f"{pri:,.2f} años"),
        ]
        y = .762
        for i, (etiqueta, valor) in enumerate(indicadores):
            fig.add_artist(plt.Rectangle((.07, y-.014), .86, .034, transform=fig.transFigure, color="#f4f7f9" if i % 2 == 0 else "white", zorder=-1))
            fig.text(.09, y, etiqueta, fontsize=9, color=muted, va="center")
            fig.text(.91, y, valor, fontsize=9, weight="bold", color=ink, va="center", ha="right")
            y -= .043

        fig.text(.07, .439, "Conclusión preliminar", fontsize=10, weight="bold", color=navy)
        fig.text(.07, .410, conclusion, fontsize=9, color=green if "favorable:" in conclusion else "#8a5a2b", wrap=True)
        fig.text(.07, .354, "2. DATOS TÉCNICOS", fontsize=12, weight="bold", color=navy)
        fig.lines.append(plt.Line2D([.07, .93], [.339, .339], transform=fig.transFigure, color="#dfe7ec", lw=1))
        datos_tecnicos = [
            f"Caudal aprovechable: {q_lps:,.1f} L/s ({q:.3f} m³/s)",
            f"Altura bruta: {h_bruta:,.2f} m | Pérdidas de carga: {perdidas:,.2f} m | Altura neta: {h_neta:,.2f} m",
            f"Eficiencia global: {eficiencia_pct}% | Factor de capacidad: {factor_pct}%",
        ]
        y = .307
        for item in datos_tecnicos:
            fig.text(.09, y, item, fontsize=8.5, color=ink)
            y -= .032

        fig.text(.07, .193, "3. SUPUESTOS FINANCIEROS", fontsize=12, weight="bold", color=navy)
        fig.lines.append(plt.Line2D([.07, .93], [.178, .178], transform=fig.transFigure, color="#dfe7ec", lw=1))
        datos_financieros = [
            f"Inversión inicial: S/ {inversion:,.2f} | O&M anual: S/ {costo_om:,.2f}",
            f"Tarifa eléctrica: S/ {tarifa:,.3f}/kWh | Tasa de descuento: {tasa_pct:.1f}% | Vida útil: {int(vida)} años",
            f"Crecimiento anual de ingresos: {crecimiento:.1f}% | Crecimiento de costos: {crecimiento_costos:.1f}%",
            f"Valor residual: S/ {valor_residual:,.2f}",
        ]
        y = .146
        for item in datos_financieros:
            fig.text(.09, y, item, fontsize=8.5, color=ink)
            y -= .029
        fig.text(.07, .045, "Documento de evaluación preliminar. No sustituye estudios especializados de ingeniería, hidrología, ambiente o finanzas.", fontsize=7, color=muted)
        fig.text(.93, .045, "HIDROVIABLE", fontsize=8, weight="bold", color=navy, ha="right")
        pdf.savefig(fig)
        plt.close(fig)

        # La proyección se divide en páginas para mantener legible la tabla en vidas útiles extensas.
        filas_por_pagina = 25
        for inicio in range(0, len(tabla), filas_por_pagina):
            pagina = inicio // filas_por_pagina + 2
            parte = tabla.iloc[inicio:inicio + filas_por_pagina]
            fig2, ax2 = plt.subplots(figsize=(8.27, 11.69))
            fig2.patch.set_facecolor("white")
            ax2.axis("off")
            fig2.text(.07, .94, "HIDROVIABLE", fontsize=11, weight="bold", color=green)
            fig2.text(.07, .905, "4. PROYECCIÓN FINANCIERA", fontsize=15, weight="bold", color=navy)
            fig2.text(.07, .878, "Flujo de caja proyectado durante la vida útil del proyecto", fontsize=9, color=muted)
            celdas = [[str(int(fila["Año"])), f"S/ {fila['Flujo de caja (S/)']:,.2f}", f"S/ {fila['Flujo acumulado (S/)']:,.2f}"] for _, fila in parte.iterrows()]
            tabla_pdf = ax2.table(cellText=celdas, colLabels=["Año", "Flujo de caja", "Flujo acumulado"], cellLoc="right", colLoc="right", bbox=[.07, .25, .86, .58], colWidths=[.12, .38, .40])
            tabla_pdf.auto_set_font_size(False)
            tabla_pdf.set_fontsize(8.5)
            for (fila, _), celda in tabla_pdf.get_celld().items():
                celda.set_edgecolor("#dfe7ec")
                if fila == 0:
                    celda.set_facecolor(navy)
                    celda.get_text().set_color("white")
                    celda.get_text().set_weight("bold")
                elif fila % 2 == 0:
                    celda.set_facecolor("#f4f7f9")
            fig2.text(.07, .105, "La proyección utiliza los supuestos ingresados; no considera impuestos, financiamiento, inflación ni riesgos extraordinarios.", fontsize=7.5, color=muted)
            fig2.text(.93, .055, f"Página {pagina}", fontsize=8, color=muted, ha="right")
            pdf.savefig(fig2)
            plt.close(fig2)
    buffer.seek(0)
    return buffer.getvalue()


st.markdown("#### Indicadores principales")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Potencia estimada", f"{potencia_kw:,.2f} kW")
c2.metric("Generación anual", f"{energia_anual:,.0f} kWh")
c3.metric("Ingreso anual", f"S/ {ingreso_anual:,.2f}")
c4.metric("Altura neta", f"{h_neta:,.2f} m")

st.write("")
tab_resumen, tab_finanzas, tab_metodo, tab_descarga = st.tabs(["Resumen ejecutivo", "Evaluación financiera", "Metodología", "Descargar informe"])

with tab_resumen:
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="section-title">Producción energética estimada</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6.2, 4))
        barras = ax.bar(["Diaria", "Anual"], [energia_dia, energia_anual], color=["#7eaec5", "#1f5c99"], width=.58)
        ax.set_ylabel("kWh", color="#647684")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#dfe7ec")
        ax.tick_params(axis="both", length=0, colors="#647684")
        ax.grid(axis="y", linestyle="--", alpha=.22)
        ax.set_axisbelow(True)
        for barra, valor in zip(barras, [energia_dia, energia_anual]):
            ax.text(barra.get_x()+barra.get_width()/2, barra.get_height(), f"{valor:,.0f}", ha="center", va="bottom", fontsize=9, color="#1c2b36")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="section-title">Proyección de flujo de caja</div>', unsafe_allow_html=True)
        fig2, ax2 = plt.subplots(figsize=(7.2, 4))
        ax2.plot(tabla["Año"], tabla["Flujo de caja (S/)"], color="#1f5c99", marker="o", markersize=3.5, linewidth=2)
        ax2.fill_between(tabla["Año"], tabla["Flujo de caja (S/)"], 0, color="#a9c4d8", alpha=.28)
        ax2.axhline(0, color="#7d8d98", linewidth=1)
        ax2.set_xlabel("Año", color="#647684")
        ax2.set_ylabel("Soles (S/)", color="#647684")
        ax2.spines[["top", "right", "left"]].set_visible(False)
        ax2.spines["bottom"].set_color("#dfe7ec")
        ax2.tick_params(length=0, colors="#647684")
        ax2.grid(axis="y", linestyle="--", alpha=.22)
        ax2.set_axisbelow(True)
        fig2.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        st.markdown('</div>', unsafe_allow_html=True)
    with st.expander("Consultar proyección detallada"):
        st.dataframe(tabla.style.format({"Flujo de caja (S/)": "S/ {:,.2f}", "Flujo acumulado (S/)": "S/ {:,.2f}"}), use_container_width=True, hide_index=True)

with tab_finanzas:
    st.markdown("#### Indicadores de rentabilidad")
    f1, f2, f3 = st.columns(3)
    f1.metric("Valor Actual Neto", f"S/ {van:,.2f}", help="Valor presente de los flujos futuros menos la inversión inicial.")
    f2.metric("Tasa Interna de Retorno", "No calculable" if tir is None else f"{tir*100:,.2f}%")
    f3.metric("Recuperación simple", "No se recupera" if pri is None else f"{pri:,.2f} años")
    if van > 0 and tir is not None and tir > tasa:
        st.success("Resultado preliminar favorable: el VAN es positivo y la TIR supera la tasa de descuento ingresada.")
    elif van < 0 or (tir is not None and tir < tasa):
        st.warning("Resultado preliminar no favorable bajo los supuestos ingresados. Revisar inversión, costos, tarifa y producción.")
    else:
        st.info("El resultado no permite emitir una conclusión definitiva con los supuestos disponibles.")

with tab_metodo:
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("#### Parámetros hidráulicos")
        st.write(f"Caudal: **{q_lps:,.1f} L/s** ({q:.3f} m³/s)")
        st.write(f"Altura bruta: **{h_bruta:,.2f} m**")
        st.write(f"Pérdidas de carga: **{perdidas:,.2f} m**")
        st.write(f"Altura neta: **{h_neta:,.2f} m**")
        st.write(f"Eficiencia global: **{eficiencia_pct}%**")
        st.write(f"Factor de capacidad: **{factor_pct}%**")
    with m2:
        st.markdown("#### Supuestos financieros")
        st.write(f"Inversión inicial: **S/ {inversion:,.2f}**")
        st.write(f"Operación y mantenimiento: **S/ {costo_om:,.2f}**")
        st.write(f"Tarifa eléctrica: **S/ {tarifa:,.3f} por kWh**")
        st.write(f"Tasa de descuento: **{tasa_pct:.1f}%**")
        st.write(f"Vida útil: **{int(vida)} años**")
    st.markdown("#### Formulación empleada")
    f1, f2 = st.columns(2)
    with f1:
        st.latex(r"H_n = H_b - h_f")
        st.latex(r"P(kW) = 9.81 \times Q(m^3/s) \times H_n(m) \times \eta")
    with f2:
        st.latex(r"E_a = P \times 8760 \times FC")
        st.latex(r"VAN = -I_0 + \sum_{t=1}^{n}\frac{FC_t}{(1+r)^t}")

with tab_descarga:
    st.markdown("### Descargar informe")
    st.markdown('<div class="download-card"><strong>Informe formal de evaluación hidroeléctrica</strong><br><span style="color:#647684">Genera un PDF con el resumen ejecutivo, resultados técnicos y financieros, supuestos y proyección anual.</span></div>', unsafe_allow_html=True)
    st.write("")
    st.download_button(
        label="📄 Descargar informe en PDF",
        data=crear_informe_pdf(),
        file_name="Informe_HIDROVIABLE.pdf",
        mime="application/pdf",
        type="primary",
    )

st.divider()
st.caption("HIDROVIABLE · Herramienta preliminar de evaluación. No incorpora impuestos, deuda, inflación, indisponibilidad extraordinaria, costos de conexión, permisos ni impactos ambientales.")

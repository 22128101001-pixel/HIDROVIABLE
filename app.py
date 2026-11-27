import math

import matplotlib.pyplot as plt
import numpy_financial as npf
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HIDROVIABLE | Evaluación hidroeléctrica", page_icon="💧", layout="wide")

# Estilo visual de la aplicación
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --hv-ink: #14332f;
        --hv-muted: #66807b;
        --hv-green: #087f68;
        --hv-lime: #b7e4c7;
        --hv-surface: #f3f8f6;
        --hv-line: #dce9e4;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #f7faf9; color: var(--hv-ink); }
    [data-testid="stHeader"] { background: rgba(247, 250, 249, .85); }
    [data-testid="stSidebar"] { background: #edf5f1; border-right: 1px solid var(--hv-line); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { font-family: 'Manrope', sans-serif; color: var(--hv-ink); }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
    .hero {
        position: relative; overflow: hidden; padding: 2rem 2.2rem; margin-bottom: 1.2rem;
        border-radius: 24px; color: white;
        background: linear-gradient(120deg, #0d5148 0%, #087f68 58%, #20a17b 100%);
        box-shadow: 0 16px 38px rgba(13, 81, 72, .16);
    }
    .hero:after {
        content: '💧'; position: absolute; right: 4%; top: -34px; font-size: 180px;
        opacity: .10; transform: rotate(-15deg);
    }
    .hero-kicker { font-size: .76rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 700; opacity: .78; }
    .hero h1 { font-family: 'Manrope', sans-serif; font-size: clamp(2rem, 4vw, 3.2rem); margin: .25rem 0 .35rem; color: white; }
    .hero p { max-width: 720px; margin: 0; font-size: 1.02rem; color: rgba(255,255,255,.86); }
    .section-label { color: var(--hv-muted); font-weight: 700; font-size: .75rem; letter-spacing: .13em; text-transform: uppercase; margin: .2rem 0 .7rem; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid var(--hv-line); border-radius: 16px;
        padding: 1rem 1.1rem; box-shadow: 0 5px 16px rgba(18, 59, 49, .035);
    }
    div[data-testid="stMetricLabel"] { color: var(--hv-muted); font-weight: 600; }
    div[data-testid="stMetricValue"] { color: var(--hv-ink); font-family: 'Manrope', sans-serif; }
    [data-testid="stTabs"] [role="tab"] { font-weight: 700; }
    [data-testid="stTabs"] [aria-selected="true"] { color: var(--hv-green); }
    .notice {
        border: 1px solid #cfe7d9; border-left: 4px solid var(--hv-green); border-radius: 12px;
        background: #eff8f2; padding: .9rem 1rem; color: #355b4d; font-size: .92rem;
    }
    .stButton > button { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 💧 HIDROVIABLE")
    st.caption("Evaluación preliminar de pequeñas centrales hidroeléctricas")
    st.divider()

    with st.expander("01 · Recurso hídrico", expanded=True):
        q_lps = st.number_input("Caudal aprovechable", min_value=0.0, value=300.0, step=10.0, help="Caudal disponible luego de considerar usos existentes y caudal ecológico. En litros por segundo.")
        h_bruta = st.number_input("Altura bruta (m)", min_value=0.0, value=30.0, step=1.0)
        perdidas = st.number_input("Pérdidas de carga (m)", min_value=0.0, value=5.0, step=0.5)

    with st.expander("02 · Parámetros técnicos", expanded=True):
        eficiencia_pct = st.slider("Eficiencia global", min_value=10, max_value=95, value=75, format="%d%%")
        factor_pct = st.slider("Factor de capacidad", min_value=1, max_value=100, value=60, format="%d%%")

    with st.expander("03 · Inversión y operación", expanded=True):
        inversion = st.number_input("Inversión inicial (S/)", min_value=0.0, value=450000.0, step=10000.0)
        costo_om = st.number_input("Operación y mantenimiento anual (S/)", min_value=0.0, value=18000.0, step=1000.0)
        tarifa = st.number_input("Valor de electricidad (S/ por kWh)", min_value=0.0, value=0.50, step=0.05, format="%.3f")
        tasa_pct = st.number_input("Tasa de descuento (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        vida = st.number_input("Vida útil (años)", min_value=1, max_value=60, value=20, step=1)

    with st.expander("04 · Supuestos del proyecto"):
        crecimiento = st.number_input("Variación anual de ingresos (%)", min_value=-50.0, max_value=50.0, value=0.0, step=1.0)
        crecimiento_costos = st.number_input("Variación anual de costos (%)", min_value=-20.0, max_value=50.0, value=0.0, step=1.0)
        valor_residual = st.number_input("Valor residual (S/)", min_value=0.0, value=0.0, step=1000.0)

q = q_lps / 1000
h_neta = h_bruta - perdidas
eficiencia = eficiencia_pct / 100
factor = factor_pct / 100
tasa = tasa_pct / 100

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">Energía limpia · Evaluación preliminar</div>
      <h1>HIDROVIABLE</h1>
      <p>Explora el potencial energético y financiero de tu proyecto hidroeléctrico rural. Ajusta los parámetros en el panel para actualizar los resultados.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="notice">Los resultados son estimaciones referenciales; no sustituyen estudios hidrológicos, de ingeniería, ambientales ni financieros.</div>',
    unsafe_allow_html=True,
)
st.write("")

if h_neta <= 0:
    st.error("La altura neta debe ser mayor que cero. Revise la altura bruta y las pérdidas de carga.")
    st.stop()
if q <= 0:
    st.error("El caudal aprovechable debe ser mayor que cero.")
    st.stop()

# P(kW) = rho*g*Q*H*eta/1000; con agua, equivale a 9.81*Q*H*eta.
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
    tir_calculada = npf.irr(flujos)
    tir = float(tir_calculada) if tir_calculada is not None and math.isfinite(float(tir_calculada)) else None
except (ValueError, OverflowError, TypeError):
    tir = None

# Periodo simple de recuperación con flujos acumulados no descontados.
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

st.markdown('<div class="section-label">Resumen del proyecto</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Potencia estimada", f"{potencia_kw:,.2f} kW", help="Potencia considerando caudal, altura neta y eficiencia.")
k2.metric("Generación anual", f"{energia_anual:,.0f} kWh")
k3.metric("Ingreso anual", f"S/ {ingreso_anual:,.2f}")
k4.metric("Altura neta", f"{h_neta:,.2f} m")

st.write("")
tab_resumen, tab_economico, tab_detalle = st.tabs(["⚡  Resumen", "📊  Evaluación económica", "🧮  Supuestos y fórmulas"])

with tab_resumen:
    st.subheader("Producción y flujo del proyecto")
    chart_col, flow_col = st.columns([1, 1.35], gap="large")
    with chart_col:
        st.markdown("#### Energía estimada")
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        bars = ax.bar(["Diaria", "Anual"], [energia_dia, energia_anual], color=["#81c9a8", "#087f68"], width=0.55)
        ax.set_ylabel("Energía (kWh)", color="#66807b")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#dce9e4")
        ax.tick_params(axis="y", length=0, colors="#66807b")
        ax.tick_params(axis="x", length=0, colors="#14332f")
        ax.grid(axis="y", linestyle="--", alpha=.22)
        ax.set_axisbelow(True)
        for bar, value in zip(bars, [energia_dia, energia_anual]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:,.0f}", ha="center", va="bottom", fontsize=9, color="#14332f")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with flow_col:
        st.markdown("#### Flujo de caja anual")
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        fig2.patch.set_facecolor("white")
        ax2.set_facecolor("white")
        ax2.plot(tabla["Año"], tabla["Flujo de caja (S/)"], color="#087f68", marker="o", markersize=4, linewidth=2)
        ax2.fill_between(tabla["Año"], tabla["Flujo de caja (S/)"], 0, color="#b7e4c7", alpha=.35)
        ax2.axhline(0, color="#91a8a0", linewidth=1)
        ax2.set_xlabel("Año", color="#66807b")
        ax2.set_ylabel("Flujo de caja (S/)", color="#66807b")
        ax2.spines[["top", "right", "left"]].set_visible(False)
        ax2.spines["bottom"].set_color("#dce9e4")
        ax2.tick_params(length=0, colors="#66807b")
        ax2.grid(axis="y", linestyle="--", alpha=.22)
        ax2.set_axisbelow(True)
        fig2.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
    with st.expander("Ver tabla de flujo de caja"):
        st.dataframe(
            tabla.style.format({"Flujo de caja (S/)": "S/ {:,.2f}", "Flujo acumulado (S/)": "S/ {:,.2f}"}),
            use_container_width=True,
            hide_index=True,
        )

with tab_economico:
    st.subheader("Indicadores de rentabilidad")
    e1, e2, e3 = st.columns(3)
    e1.metric("Valor Actual Neto (VAN)", f"S/ {van:,.2f}", help="Valor presente de los flujos futuros menos la inversión inicial.")
    e2.metric("Tasa Interna de Retorno (TIR)", "No calculable" if tir is None else f"{tir * 100:,.2f}%")
    e3.metric("Recuperación simple", "No se recupera" if pri is None else f"{pri:,.2f} años")

    if van > 0 and tir is not None and tir > tasa:
        st.success("Diagnóstico preliminar favorable: el VAN es positivo y la TIR supera la tasa de descuento ingresada.")
    elif van < 0 or (tir is not None and tir < tasa):
        st.warning("Diagnóstico preliminar no favorable bajo estos supuestos. Revise inversión, costos, tarifa y producción estimada.")
    else:
        st.info("Resultado de equilibrio o insuficiente para emitir una conclusión financiera con estos supuestos.")

    st.caption("La TIR puede no ser calculable si los flujos no presentan una combinación de valores positivos y negativos que permita obtener una solución.")

with tab_detalle:
    st.subheader("Parámetros usados en la estimación")
    a, b = st.columns(2)
    with a:
        st.markdown("**Hidráulicos y técnicos**")
        st.write(f"Caudal aprovechable: **{q_lps:,.1f} L/s** ({q:.3f} m³/s)")
        st.write(f"Altura bruta: **{h_bruta:,.2f} m** · Pérdidas: **{perdidas:,.2f} m**")
        st.write(f"Eficiencia: **{eficiencia_pct}%** · Factor de capacidad: **{factor_pct}%**")
    with b:
        st.markdown("**Económicos y horizonte**")
        st.write(f"Inversión: **S/ {inversion:,.2f}** · O&M anual: **S/ {costo_om:,.2f}**")
        st.write(f"Tarifa: **S/ {tarifa:,.3f}/kWh** · Tasa de descuento: **{tasa_pct:.1f}%**")
        st.write(f"Vida útil: **{int(vida)} años** · Valor residual: **S/ {valor_residual:,.2f}**")

    st.markdown("#### Fórmulas utilizadas")
    f1, f2 = st.columns(2)
    with f1:
        st.latex(r"H_n = H_b - h_f")
        st.latex(r"P(kW) = 9.81 \times Q(m^3/s) \times H_n(m) \times \eta")
    with f2:
        st.latex(r"E_a = P \times 8760 \times FC")
        st.latex(r"VAN = -I_0 + \sum_{t=1}^{n}\frac{FC_t}{(1+r)^t}")

st.divider()
st.caption(
    "Estimación preliminar. No incorpora impuestos, deuda, inflación, indisponibilidad extraordinaria, costos de conexión, permisos ni impactos ambientales. "
    "El caudal debe ser el realmente aprovechable luego de respetar los usos existentes y el caudal ecológico determinado para el sitio."
)

import streamlit as st
import numpy_financial as npf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="HIDROVIABLE", page_icon="💧", layout="wide")

st.title("💧 HIDROVIABLE")
st.subheader("Calculadora de viabilidad de pequeñas centrales hidroeléctricas")
st.caption("Evaluación preliminar hidráulica, energética y económica para comunidades rurales.")

st.info(
    "Ingrese los datos del proyecto en el panel lateral. Los resultados son estimaciones "
    "preliminares y no reemplazan un estudio hidrológico, de ingeniería, ambiental o financiero."
)

with st.sidebar:
    st.header("1. Datos hidráulicos")
    q_lps = st.number_input("Caudal aprovechable (L/s)", min_value=0.0, value=300.0, step=10.0)
    h_bruta = st.number_input("Altura bruta (m)", min_value=0.0, value=30.0, step=1.0)
    perdidas = st.number_input("Pérdidas de carga (m)", min_value=0.0, value=5.0, step=0.5)

    st.header("2. Datos técnicos")
    eficiencia_pct = st.slider("Eficiencia global (%)", min_value=10, max_value=95, value=75)
    factor_pct = st.slider("Factor de capacidad (%)", min_value=1, max_value=100, value=60)

    st.header("3. Datos económicos")
    inversion = st.number_input("Inversión inicial (S/)", min_value=0.0, value=450000.0, step=10000.0)
    costo_om = st.number_input("Operación y mantenimiento anual (S/)", min_value=0.0, value=18000.0, step=1000.0)
    tarifa = st.number_input("Valor de electricidad (S/ por kWh)", min_value=0.0, value=0.50, step=0.05, format="%.3f")
    tasa_pct = st.number_input("Tasa de descuento (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
    vida = st.number_input("Vida útil del proyecto (años)", min_value=1, max_value=60, value=20, step=1)

    st.header("4. Supuestos adicionales")
    crecimiento = st.number_input("Variación anual de ingresos (%)", min_value=-50.0, max_value=50.0, value=0.0, step=1.0)
    crecimiento_costos = st.number_input("Variación anual de costos (%)", min_value=-20.0, max_value=50.0, value=0.0, step=1.0)
    valor_residual = st.number_input("Valor residual al final de la vida útil (S/)", min_value=0.0, value=0.0, step=1000.0)

q = q_lps / 1000
h_neta = h_bruta - perdidas
eficiencia = eficiencia_pct / 100
factor = factor_pct / 100
tasa = tasa_pct / 100

if h_neta <= 0:
    st.error("La altura neta debe ser mayor que cero. Revise la altura bruta y las pérdidas.")
    st.stop()
if q <= 0:
    st.error("El caudal aprovechable debe ser mayor que cero.")
    st.stop()

# P(kW) = rho*g*Q*H*eta/1000; para agua con rho≈1000 kg/m3, equivale a 9.81*Q*H*eta.
potencia_kw = 9.81 * q * h_neta * eficiencia
energia_dia = potencia_kw * 24 * factor
energia_anual = potencia_kw * 8760 * factor
ingreso_anual = energia_anual * tarifa
flujo_anual = ingreso_anual - costo_om

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
    tir = npf.irr(flujos)
except Exception:
    tir = None

# Recuperación simple con flujos acumulados no descontados.
acumulado = -inversion
pri = None
for ano, flujo in enumerate(flujos[1:], start=1):
    anterior = acumulado
    acumulado += flujo
    if acumulado >= 0:
        if flujo > 0:
            pri = (ano - 1) + (-anterior / flujo)
        else:
            pri = float(ano)
        break

st.markdown("## Resultados del proyecto")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Altura neta", f"{h_neta:,.2f} m")
c2.metric("Potencia estimada", f"{potencia_kw:,.2f} kW")
c3.metric("Energía anual", f"{energia_anual:,.0f} kWh")
c4.metric("Ingreso anual", f"S/ {ingreso_anual:,.2f}")

st.markdown("### Evaluación económica")
e1, e2, e3 = st.columns(3)
e1.metric("VAN", f"S/ {van:,.2f}")
e2.metric("TIR", "No calculable" if tir is None else f"{tir*100:,.2f}%")
e3.metric("Recuperación simple", "No se recupera" if pri is None else f"{pri:,.2f} años")

if van > 0 and tir is not None and tir > tasa:
    st.success("Diagnóstico financiero preliminar: favorable según el VAN y la comparación entre TIR y tasa de descuento.")
elif van < 0 or (tir is not None and tir < tasa):
    st.warning("Diagnóstico financiero preliminar: no favorable bajo los supuestos ingresados. Revise costos, tarifa, inversión y producción.")
else:
    st.info("Diagnóstico financiero preliminar: resultado de equilibrio o insuficiente para emitir una conclusión.")

st.markdown("### Flujo de caja proyectado")
tabla = pd.DataFrame({
    "Año": list(range(0, int(vida) + 1)),
    "Flujo de caja (S/)": flujos,
    "Flujo acumulado (S/)": pd.Series(flujos).cumsum()
})
st.dataframe(tabla.style.format({"Flujo de caja (S/)": "S/ {:,.2f}", "Flujo acumulado (S/)": "S/ {:,.2f}"}), use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("### Producción eléctrica estimada")
    fig, ax = plt.subplots()
    ax.bar(["Diaria", "Anual"], [energia_dia, energia_anual])
    ax.set_ylabel("Energía (kWh)")
    ax.set_title("Energía estimada")
    st.pyplot(fig)
    plt.close(fig)

with col_b:
    st.markdown("### Flujo de caja anual")
    fig2, ax2 = plt.subplots()
    ax2.plot(tabla["Año"], tabla["Flujo de caja (S/)"], marker="o")
    ax2.axhline(0, linewidth=1)
    ax2.set_xlabel("Año")
    ax2.set_ylabel("S/")
    ax2.set_title("Flujo de caja proyectado")
    st.pyplot(fig2)
    plt.close(fig2)

st.markdown("### Fórmulas utilizadas")
st.latex(r"H_n = H_b - h_f")
st.latex(r"P(kW) = 9.81 \times Q(m^3/s) \times H_n(m) \times \eta")
st.latex(r"E_a = P \times 8760 \times FC")
st.latex(r"VAN = -I_0 + \sum_{t=1}^{n}\frac{FC_t}{(1+r)^t}")

st.caption(
    "Notas: el aplicativo supone disponibilidad de la energía calculada y utiliza una tarifa/valor "
    "constante ajustable. No incorpora impuestos, deuda, inflación, indisponibilidad extraordinaria, "
    "costos de conexión, permisos ni impactos ambientales. El caudal ingresado debe ser el caudal "
    "realmente aprovechable después de respetar usos existentes y caudal ecológico determinado para el sitio."
)

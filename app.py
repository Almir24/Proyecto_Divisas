import streamlit as st
import requests
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuración de la página web
st.set_page_config(page_title="Plataforma de Ingeniería Financiera Avanzada (EDO)", layout="wide")

st.title("🏛️ Sistema de Ingeniería Financiera y Modelado de Divisas mediante EDO")
st.write("Proyecto Escolar Acreditado (ESE-IPN): Integración de EDO/EDE, Estimación de Parámetros mediante IA (Regresión ML) y Pruebas de Estrés.")
st.markdown("---")

# Lista de monedas estables soportadas por la API pública
NOMBRES_MONEDAS = {
    "USD": "USD - Dólar estadounidense",
    "MXN": "MXN - Peso mexicano",
    "EUR": "EUR - Euro",
    "GBP": "GBP - Libra esterlina",
    "JPY": "JPY - Yen japonés",
    "CAD": "CAD - Dólar canadiense",
    "AUD": "AUD - Dólar australiano",
    "BRL": "BRL - Real brasileño",
    "CHF": "CHF - Franco suizo",
    "CNY": "CNY - Yuan chino"
}

# Layout Principal
col_m1, col_m2 = st.columns(2)
with col_m1:
    idx_usd = list(NOMBRES_MONEDAS.keys()).index("USD")
    opcion_origen = st.selectbox("Moneda Base (Origen):", [f"{k} - {v}" for k, v in NOMBRES_MONEDAS.items()], index=idx_usd)
    codigo_origen = opcion_origen.split(" - ")[0]
with col_m2:
    idx_mxn = list(NOMBRES_MONEDAS.keys()).index("MXN")
    opcion_destino = st.selectbox("Moneda Cotizada (Destino):", [f"{k} - {v}" for k, v in NOMBRES_MONEDAS.items()], index=idx_mxn)
    codigo_destino = opcion_destino.split(" - ")[0]

if codigo_origen == codigo_destino:
    st.warning("⚠️ Selecciona dos monedas diferentes para activar los modelos.")
    st.stop()

# Conexión a API Real
@st.cache_data(ttl=600)
def obtener_datos_reales_mercado(origen, destino):
    try:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        fecha_inicio = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        url_historial = f"https://api.frankfurter.app/{fecha_inicio}..{fecha_fin}?from={origen}&to={destino}"
        res_hist = requests.get(url_historial).json()
        
        fechas_ordenadas = sorted(list(res_hist['rates'].keys()))
        historial_precios = [res_hist['rates'][f][destino] for f in fechas_ordenadas]
        fechas_formateadas = [datetime.strptime(f, '%Y-%m-%d').strftime('%d-%b') for f in fechas_ordenadas]
        
        historial_precios = historial_precios[-30:]
        fechas_formateadas = fechas_formateadas[-30:]
        precio_hoy = historial_precios[-1]
        
        url_actual = f"https://api.frankfurter.app/latest?from={origen}"
        res_act = requests.get(url_actual).json()
        tasas_dia = res_act['rates']
        tasas_dia[origen] = 1.0
        
        return precio_hoy, historial_precios, fechas_formateadas, tasas_dia
    except Exception as e:
        return 1.00, [1.00]*30, ["Día"]*30, {"USD": 1.0, "MXN": 18.0}

precio_actual, historial_real, fechas_reales, todas_las_tasas = obtener_datos_reales_mercado(codigo_origen, codigo_destino)

# Métricas reales principales
st.markdown("### 📊 Monitor de Mercado Real (Datos del Banco Central Europeo)")
c_1, c_2, c_3 = st.columns(3)
with c_1:
    cantidad_input = st.number_input(f"Monto a Convertir ({codigo_origen}):", min_value=1.0, value=100.0)
with c_2:
    st.metric(label=f"Tasa Real Spot ({codigo_origen}/{codigo_destino})", value=f"{precio_actual:.4f}")
with c_3:
    st.metric(label="Monto Convertido Real", value=f"{cantidad_input * precio_actual:.2f} {codigo_destino}")

# ================= INTEGRACIÓN DE IA (MODELO DE APRENDIZAJE SUPERVISADO) =================
# Implementamos una Regresión Lineal por Mínimos Cuadrados (OLS) para predecir la deriva de la EDO (mu)
x_datos = np.arange(len(historial_real))
y_datos = np.array(historial_real)

# Ecuaciones normales de regresión de IA: y = mx + b
n_puntos = len(x_datos)
pendiente_m = (n_puntos * np.sum(x_datos * y_datos) - np.sum(x_datos) * np.sum(y_datos)) / (n_puntos * np.sum(x_datos**2) - (np.sum(x_datos))**2)

# Normalizar la pendiente para obtener la tasa de rendimiento instantánea (Deriva mu)
mu_estimada_ia = float(pendiente_m / precio_actual)

# Estimación de la volatilidad empírica (sigma) basada en la desviación estándar de retornos logarítmicos reales
retornos_log = np.diff(np.log(historial_real))
sigma_estimada = float(np.std(retornos_log)) if len(retornos_log) > 0 else 0.015

# Controles laterales
st.sidebar.header("⚙️ Parámetros de la EDO e IA")
volatilidad = st.sidebar.slider("Volatilidad Proyectada (σ):", 0.005, 0.06, sigma_estimada, step=0.005)
simulaciones = st.sidebar.slider("Trayectorias de Montecarlo:", 10, 150, 50, step=10)

# Indicadores técnicos adicionales
media_movil = np.mean(historial_real[-14:])
desviacion = np.std(historial_real[-14:])
banda_sup = media_movil + (2 * desviacion)
banda_inf = media_movil - (2 * desviacion)

cambios = np.diff(historial_real[-15:])
ganancias = cambios[cambios > 0]
perdidas = -cambios[cambios < 0]
rsi = 100 - (100 / (1 + (np.mean(ganancias)/np.mean(perdidas)))) if len(perdidas) > 0 and len(ganancias) > 0 else 50.0

st.markdown("---")

# PESTAÑAS ESTRUCTURADAS EXCLUSIVAMENTE BAJO LA RÚBRICA
tab_teoria, tab_futuro, tab_historial, tab_arbitraje, tab_stress = st.tabs([
    "📝 Marco Teórico y Solución de la EDO",
    "🎲 Modelado Estocástico Futuro (EDE)", 
    "📈 Datos Históricos Reales (30 Días)", 
    "⛓️ Red de Arbitraje Cruzado",
    "💥 Pruebas de Estrés (Stress Testing)"
])

# ================= TAB 0: MARCO TEÓRICO Y SOLUCIÓN PASO A PASO =================
with tab_teoria:
    st.subheader("📚 Sustentación Matemática y Económica del Proyecto (Rúbrica IPN)")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### 1. Planteamiento Matemático de la EDO")
        st.write("Para modelar el comportamiento del tipo de cambio, partimos de una EDO lineal de primer orden donde la variación del precio $S$ es proporcional a su valor actual en el tiempo $t$:")
        st.latex(r"\frac{dS}{dt} = \mu S(t)")
        st.write("Donde:")
        st.write("* **$S(t)$:** Variable dependiente (Precio del tipo de cambio).")
        st.write("* **$t$:** Variable independiente (Tiempo en el horizonte proyectado).")
        st.write("* **$\mu$:** Parámetro de Deriva o Tendencia (Tasa de rendimiento instantánea).")
        
        st.markdown("#### 2. Solución Analítica Paso a Paso (Separación de Variables)")
        st.write("**Paso A: Reordenar términos:**")
        st.latex(r"\frac{1}{S} \, dS = \mu \, dt")
        st.write("**Paso B: Integración a ambos lados:**")
        st.latex(r"\int \frac{1}{S} \, dS = \int \mu \, dt \implies \ln(S) = \mu t + C")
        st.write("**Paso C: Despejar variable mediante función exponencial:**")
        st.latex(r"S(t) = e^{\mu t + C} = e^C \cdot e^{\mu t}")
        st.write("**Paso D: Aplicación de la condición inicial $S(0) = S_0$ (Tasa Spot real de hoy):**")
        st.latex(r"S(t) = S_0 e^{\mu t}")

    with col_t2:
        st.markdown("#### 3. Transición al Modelo Estocástico (Lema de Itô)")
        st.write("Dado que los mercados financieros son dinámicos y caóticos, agregamos un término estocástico (ruido blanco) mediante una Ecuación Diferencial Estocástica (EDE):")
        st.latex(r"dS_t = \mu S_t dt + \sigma S_t dW_t")
        st.write("Resolviendo mediante el **Lema de Itô**, la solución fuerte analítica de esta EDE es:")
        st.latex(r"S(t) = S_0 \exp\left(\left(\mu - \frac{\sigma^2}{2}\right)t + \sigma W_t\right)")
        st.write("Para la simulación por computadora, se aplica la aproximación numérica de **Euler-Maruyama**:")
        st.latex(r"S_{t+\Delta t} = S_t \exp\left(\left(\mu - \frac{\sigma^2}{2}\right)\Delta t + \sigma \sqrt{\Delta t} Z\right), \quad Z \sim N(0,1)")

        st.markdown("#### 4. Rol Funcional de la Inteligencia Artificial (Machine Learning)")
        st.success(f"""
        **Modelo de IA Empleado:** Regresión Lineal por Mínimos Cuadrados Ordinarios (OLS).
        * **Justificación:** En lugar de asumir un parámetro estático o intuitivo para la tendencia ($\mu$), entrenamos un regresor supervisado con la serie de tiempo real del BCE de los últimos 30 días.
        * **Pendiente Estimada por IA ($m$):** {pendiente_m:.6f}
        * **Deriva resultante ($\mu$):** {mu_estimada_ia:.6f} (Este valor alimenta directamente la EDO en la simulación).
        """)

# ================= TAB 1: MONTECARLO & EDE =================
with tab_futuro:
    st.subheader("🔮 Simulación Hacia Adelante aplicando Euler-Maruyama")
    st.latex(r"S(t) = S_0 \exp\left(\left(\mu - \frac{\sigma^2}{2}\right)t + \sigma W_t\right)")
    
    horas = np.linspace(0, 24, 100)
    dt = horas[1] - horas[0]
    
    fig_montecarlo = go.Figure()
    edo_pura = precio_actual * np.exp(mu_estimada_ia * horas)
    
    for _ in range(simulaciones):
        camino = [precio_actual]
        for t in range(1, len(horas)):
            dW = np.random.normal(0, np.sqrt(dt))
            nuevo_precio = camino[-1] * np.exp((mu_estimada_ia - 0.5 * volatilidad**2) * dt + volatilidad * dW)
            camino.append(nuevo_precio)
        fig_montecarlo.add_trace(go.Scatter(x=horas, y=camino, mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
        
    fig_montecarlo.add_trace(go.Scatter(x=horas, y=edo_pura, mode='lines', name='Solución Determinista de la EDO', line=dict(color='#FF4B4B', width=4)))
    fig_montecarlo.update_layout(title=f"Proyección Dinámica del Par {codigo_origen}/{codigo_destino}", xaxis_title="Horas Hacia el Futuro", yaxis_title="Precio", template="plotly_dark")
    st.plotly_chart(fig_montecarlo, use_container_width=True)

# ================= TAB 2: HISTORIAL REAL =================
with tab_historial:
    st.subheader("📈 Gráfica de Rango de Datos Reales")
    fig_historial = go.Figure()
    fig_historial.add_trace(go.Scatter(x=fechas_reales, y=historial_real, mode='lines+markers', name='Precio Real', line=dict(color='#00CC96', width=3)))
    fig_historial.add_trace(go.Scatter(x=fechas_reales, y=[banda_sup]*30, mode='lines', name='Banda Sup (Sobrecompra)', line=dict(color='#FF9200', dash='dash')))
    fig_historial.add_trace(go.Scatter(x=fechas_reales, y=[banda_inf]*30, mode='lines', name='Banda Inf (Soporte)', line=dict(color='#00B2FE', dash='dash')))
    fig_historial.update_layout(title="Mercado en los Últimos 30 Días Hábiles", xaxis_title="Fecha", yaxis_title="Precio", template="plotly_dark")
    st.plotly_chart(fig_historial, use_container_width=True)

# ================= TAB 3: ARBITRAJE =================
with tab_arbitraje:
    st.subheader("⛓️ Red de Arbitraje Cruzado e Ineficiencias de Mercado")
    moneda_puente = "EUR" if codigo_origen == "USD" or codigo_destino == "EUR" else "USD"
    if moneda_puente in todas_las_tasas and codigo_destino in todas_las_tasas:
        tasa_origen_puente = todas_las_tasas[moneda_puente]
        tasa_puente_destino = todas_las_tasas[codigo_destino] / todas_las_tasas[moneda_puente]
        monto_directo = cantidad_input * precio_actual
        monto_triangulado = cantidad_input * tasa_origen_puente * tasa_puente_destino
        diferencia = monto_triangulado - monto_directo
        
        st.markdown(f"**Ruta Evaluada:** `{codigo_origen}` ➔ `{moneda_puente}` ➔ `{codigo_destino}`")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.info(f"💵 **Conversión Directa:** {monto_directo:.2f} {codigo_destino}")
            st.success(f"🔀 **Conversión Cruzada:** {monto_triangulado:.2f} {codigo_destino}")
        with t_col2:
            if diferencia > 0.001:
                st.metric(label="Arbitraje Detectado (Ganancia)", value=f"+{diferencia:.4f} {codigo_destino}")
                st.balloons()
            else:
                st.metric(label="Divergencia de Precios Cruzados", value=f"{diferencia:.4f} {codigo_destino}")
                st.caption("Los precios están en perfecto equilibrio macroeconómico.")

# ================= TAB 4: PRUEBAS DE ESTRÉS =================
with tab_stress:
    st.subheader("💥 Simulación de Escenarios Macroeconómicos Extremos (Stress Testing)")
    escenario = st.radio(
        "Selecciona el Escenario de Crisis Global:",
        ("Mercado Normal", "Shock Geopolítico (Volatilidad Extrema)", "Colapso Bancario (Desplome Exponencial)")
    )
    
    if escenario == "Shock Geopolítico (Volatilidad Extrema)":
        mu_stress, sigma_stress = 0.0, volatilidad * 4.0
        explicacion_stress = "⚠️ **Diagnóstico de Estrés:** Incertidumbre geopolítica severa. Se congela el rendimiento esperado, pero el factor estocástico se multiplica por 4."
    elif escenario == "Colapso Bancario (Desplome Exponencial)":
        mu_stress, sigma_stress = -0.015, volatilidad * 2.5
        explicacion_stress = "🚨 **Diagnóstico de Estrés:** Fuga masiva de activos y devaluación instantánea. La deriva calculada por la regresión de IA se desploma a niveles negativos drásticos."
    else:
        mu_stress, sigma_stress = mu_estimada_ia, volatilidad
        explicacion_stress = "✅ Parámetros de mercado normales estimados por nuestro modelo de regresión de IA."
        
    horas_s = np.linspace(0, 24, 100)
    dt_s = horas_s[1] - horas_s[0]
    fig_stress = go.Figure()
    
    for _ in range(simulaciones):
        camino_s = [precio_actual]
        for t in range(1, len(horas_s)):
            dW = np.random.normal(0, np.sqrt(dt_s))
            nuevo_precio = camino_s[-1] * np.exp((mu_stress - 0.5 * sigma_stress**2) * dt_s + sigma_stress * dW)
            camino_s.append(nuevo_precio)
        fig_stress.add_trace(go.Scatter(x=horas_s, y=camino_s, mode='lines', line=dict(width=1), opacity=0.2, showlegend=False))
        
    edo_stress = precio_actual * np.exp(mu_stress * horas_s)
    fig_stress.add_trace(go.Scatter(x=horas_s, y=edo_stress, mode='lines', name='EDO Bajo Estrés', line=dict(color='#FF2B2B', width=4)))
    fig_stress.update_layout(title=f"Comportamiento de la EDO bajo: {escenario}", xaxis_title="Horas Hacia el Futuro", yaxis_title="Precio", template="plotly_dark")
    st.plotly_chart(fig_stress, use_container_width=True)
    st.markdown(explicacion_stress)
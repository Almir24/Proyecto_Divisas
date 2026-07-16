import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

# 1. Configuración de la página y título centrado en EDO y Economía
st.set_page_config(page_title="Simulador EDO Divisas", layout="wide", initial_sidebar_state="expanded")

st.title("💱 Simulador del Tipo de Cambio mediante Ecuaciones Diferenciales e Inteligencia Artificial")
st.markdown("---")

# 2. Sidebar: Selección de parámetros y consumo de API en tiempo real
st.sidebar.header("⚙️ Configuración del Modelo")

@st.cache_data(ttl=3600)
def obtener_datos_historicos(base_currency, target_currency):
    """Obtiene datos reales de los últimos 30 días usando una API pública."""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=45) # Margen para asegurar 30 días hábiles
    
    url = f"https://api.exchangerate.host/timeseries?start_date={start_date.strftime('%Y-%m-%d')}&end_date={end_date.strftime('%Y-%m-%d')}&base={base_currency}&symbols={target_currency}"
    
    try:
        response = requests.get(url).json()
        rates = response.get('rates', {})
        fechas = sorted(list(rates.keys()))
        precios = [rates[fecha][target_currency] for fecha in fechas if target_currency in rates[fecha]]
        
        df = pd.DataFrame({"Fecha": pd.to_datetime(fechas[-30:]), "Precio": precios[-30:]})
        return df
    except Exception:
        # Respaldo local en caso de falla de red o API
        fechas_mock = pd.date_range(end=datetime.today(), periods=30, freq='D')
        precios_mock = np.linspace(17.5, 18.2, 30) + np.random.normal(0, 0.1, 30)
        return pd.DataFrame({"Fecha": fechas_mock, "Precio": precios_mock})

# Opciones de divisas
base_div = st.sidebar.selectbox("Moneda Base", ["USD", "EUR", "GBP"])
target_div = st.sidebar.selectbox("Moneda Destino", ["MXN", "BRL", "ARS", "EUR", "JPY"], index=0)

df_historico = obtener_datos_historicos(base_div, target_div)

# 3. Inteligencia Artificial: Ajuste por Regresión Lineal
X = np.arange(len(df_historico)).reshape(-1, 1)
y = df_historico['Precio'].values

modelo_ia = LinearRegression()
modelo_ia.fit(X, y)

# Parámetros clave extraídos por la IA
pendiente_m = modelo_ia.coef_[0]
S_0 = y[-1] # Último precio real conocido del mercado
mu_calculada = pendiente_m / S_0

# Configuración de simulaciones estocásticas internas en sidebar
volatilidad = st.sidebar.slider("Volatilidad del mercado (σ)", min_value=0.005, max_value=0.080, value=0.020, step=0.005)
caminos_simulados = st.sidebar.slider("Número de trayectorias alternativas", min_value=5, max_value=50, value=15, step=5)

# 4. Diseño de pestañas funcionales del proyecto
tab1, tab2, tab3 = st.tabs(["📊 Simulación y EDO", "📐 Fundamentación Matemática", "🚨 Pruebas de Estrés"])

# ==========================================
# PESTAÑA 1: SIMULACIÓN Y EDO
# ==========================================
with tab1:
    st.header("📈 Análisis de Tendencia y Proyección Dinámica")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.subheader("📋 Parámetros calculados por la IA")
        st.write("A partir del análisis de mínimos cuadrados sobre la tendencia histórica de 30 días, se han parametrizado las variables de la EDO:")
        
        st.metric(label="Tipo de cambio actual ($S_0$)", value=f"{S_0:.4f} {target_div}")
        st.metric(label="Pendiente de la regresión ($m$)", value=f"{pendiente_m:.6f}")
        st.metric(label="Tasa intrínseca de deriva ($\mu = m / S_0$)", value=f"{mu_calculada:.6f}")
        
        st.subheader("📝 Ecuaciones del Momento")
        st.markdown("**Ecuación Diferencial Ajustada:**")
        st.latex(rf"\frac{{dS}}{{dt}} = {mu_calculada:.5f} \cdot S(t)")
        
        st.markdown("**Solución Particular del Sistema:**")
        st.latex(rf"S(t) = {S_0:.4f} \cdot e^{{{mu_calculada:.5f} \cdot t}}")
        
        # 7. Sección Automática de Interpretación Económica
        st.subheader("💡 Interpretación Económica")
        if mu_calculada > 0.0001:
            st.success(f"**Tendencia Creciente ($\mu > 0$):** El modelo matemático indica una depreciación de la moneda base frente al {target_div}. Se proyecta una presión al alza en el tipo de cambio debido a fuerzas sostenidas del mercado.")
        elif mu_calculada < -0.0001:
            st.warning(f"**Tendencia Decreciente ($\mu < 0$):** El sistema matemático muestra una trayectoria de apreciación. El par de divisas tiende a la baja, lo que indica un fortalecimiento de la moneda de destino.")
        else:
            st.info(rf"**Tendencia Estable ($\mu \approx 0$):** El mercado se encuentra en un equilibrio dinámico estacionario. No se registran presiones estructurales significativas en ninguna dirección.")

    with col_der:
        st.subheader("📉 Comparación: EDO Determinista vs Trayectoria Real e Incertidumbre")
        
        # Simulación del futuro (24 periodos / horas adelante)
        T = 24
        t_sim = np.arange(T + 1)
        
        # Solución exacta de la EDO
        solucion_edo = S_0 * np.exp(mu_calculada * t_sim)
        
        fig = go.Figure()
        
        # Añadir trayectorias de simulación con incertidumbre (Euler-Maruyama interno)
        for i in range(caminos_simulados):
            caminos = [S_0]
            for t in range(T):
                shock = np.random.normal(0, 1)
                # Modelo dinámico con ruido blanco incorporado
                S_siguiente = caminos[-1] * (1 + mu_calculada + volatilidad * shock)
                caminos.append(S_siguiente)
            fig.add_trace(go.Scatter(x=t_sim, y=caminos, mode='lines', line=dict(width=1), opacity=0.35, showlegend=False))
            
        # Graficar solución central analítica de la EDO
        fig.add_trace(go.Scatter(x=t_sim, y=solucion_edo, mode='lines+markers', name='Solución Analítica EDO', line=dict(color='#00FFCC', width=3.5)))
        
        fig.update_layout(
            title=f"Proyección del Tipo de Cambio para las próximas 24 horas ({base_div}/{target_div})",
            xaxis_title="Tiempo futuro (Horas)",
            yaxis_title=f"Unidades de {target_div}",
            template="plotly_dark",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig, use_container_width=True)

# 8. Gráfica Comparativa con Histórico Real
st.markdown("---")
st.subheader("📅 Ajuste del Modelo sobre los Datos Históricos Reales (Últimos 30 días)")

dias_historicos = np.arange(len(df_historico))
precio_inicial_hist = df_historico['Precio'].iloc[0]
curva_edo_historica = precio_inicial_hist * np.exp(mu_calculada * dias_historicos)

fig_hist = go.Figure()
fig_hist.add_trace(go.Scatter(x=df_historico['Fecha'], y=df_historico['Precio'], mode='markers+lines', name='Precios Reales de Mercado', line=dict(color='#FF9900', width=2)))
fig_hist.add_trace(go.Scatter(x=df_historico['Fecha'], y=curva_edo_historica, mode='lines', name='Trayectoria Teórica EDO', line=dict(color='#00CCFF', width=2.5, dash='dash')))

fig_hist.update_layout(
    xaxis_title="Línea de Tiempo",
    yaxis_title=f"Precio ({target_div})",
    template="plotly_dark",
    margin=dict(l=40, r=40, t=20, b=40)
)
st.plotly_chart(fig_hist, use_container_width=True)


# ==========================================
# PESTAÑA 2: FUNDAMENTACIÓN MATEMÁTICA
# ==========================================
with tab2:
    st.header("📐 Estructura Matemática del Sistema Dinámico Económico")
    
    st.markdown("""
    ### 🏛️ Fenómeno Económico Estudiado
    En la teoría microeconómica y financiera moderna, el precio de una divisa refleja un flujo constante de información disponible en los mercados globales. Si asumimos un mercado eficiente y continuo sin fricciones externas instantáneas, la variación del valor del tipo de cambio respecto al tiempo es directamente proporcional al valor actual del activo.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("#### 🛠️ Ecuación Diferencial Ordinaria (EDO)")
        st.write("Planteamos un modelo lineal homogéneo de primer orden:")
        st.latex(r"\frac{dS}{dt} = \mu S(t)")
        st.write("Donde:")
        st.markdown(f"- **$S(t)$**: Es el tipo de cambio en el tiempo $t$.\n- **$\mu$**: Tasa intrínseca de rendimiento o velocidad de deriva constante.")
        
    with col2:
        st.info("#### 🔬 Método de Solución: Separación de Variables")
        st.write("Agrupamos términos semejantes en cada lado de la igualdad:")
        st.latex(r"\frac{1}{S} dS = \mu dt")
        st.write("Aplicando el operador de integración indefinida en ambos lados:")
        st.latex(r"\int \frac{1}{S} dS = \int \mu dt \implies \ln|S| = \mu t + C")
        
    st.markdown("### 🔑 Solución Analítica General y Particular")
    st.write("Despejando nuestra variable dependiente mediante la función exponencial obtenemos la solución explícita:")
    st.latex(r"S(t) = e^{\mu t + C} = e^C \cdot e^{\mu t} \implies S(t) = S_0 e^{\mu t}")
    st.write(f"Donde $S_0$ representa las condiciones iniciales del mercado capturadas en tiempo real por la Inteligencia Artificial al instante de ejecución ($S_0 = {S_0:.4f}$).")


# ==========================================
# PESTAÑA 3: PRUEBAS DE ESTRÉS
# ==========================================
with tab3:
    st.header("🚨 Simulación de Escenarios y Crisis Macroeconómicas")
    st.write("Modificación controlada de los coeficientes de la ecuación diferencial para analizar comportamientos de la divisa ante impactos financieros extremos mundiales.")
    
    escenario = st.radio("Seleccione el Escenario a evaluar:", 
                         ["Estable (Línea Base de la IA)", "Shock Geopolítico Global", "Colapso Estructural de la Moneda"])
    
    # Redefinición dinámica de variables EDO según el test
    if escenario == "Estable (Línea Base de la IA)":
        mu_stress = mu_calculada
        sigma_stress = volatilidad
        desc_escenario = "Mantiene los parámetros óptimos detectados mediante la regresión de aprendizaje predictivo."
    elif escenario == "Shock Geopolítico Global":
        mu_stress = 0.0000 
        sigma_stress = volatilidad * 3.5
        desc_escenario = "Simula parálisis comercial internacional masiva: La tendencia media se colapsa a cero, pero la volatilidad se multiplica drásticamente por 350%."
    else: # Colapso Estructural
        mu_stress = -0.025
        sigma_stress = volatilidad * 1.8
        desc_escenario = "Simula una fuga masiva de capitales de la región. La tasa de cambio decae exponencialmente de forma severa y continua."
        
    st.markdown(f"**Condición Operativa:** {desc_escenario}")
    
    # Ejecución de la EDO bajo condiciones críticas
    solucion_stress = S_0 * np.exp(mu_stress * t_sim)
    
    fig_stress = go.Figure()
    for i in range(caminos_simulados):
        caminos_st = [S_0]
        for t in range(T):
            shock = np.random.normal(0, 1)
            S_sig = caminos_st[-1] * (1 + mu_stress + sigma_stress * shock)
            caminos_st.append(S_sig)
        fig_stress.add_trace(go.Scatter(x=t_sim, y=caminos_st, mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
        
    fig_stress.add_trace(go.Scatter(x=t_sim, y=solucion_stress, mode='lines', name='Trayectoria EDO en Crisis', line=dict(color='#FF0055', width=3)))
    fig_stress.update_layout(xaxis_title="Tiempo (Horas)", yaxis_title="Precio de la Divisa", template="plotly_dark")
    st.plotly_chart(fig_stress, use_container_width=True)
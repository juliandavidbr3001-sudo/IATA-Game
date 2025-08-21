import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import time

# ==============================
# CARGAR DATOS
# ==============================
@st.cache_data
def load_data():
    df = pd.read_csv("departamentos_colombia.csv")
    return df

df = load_data()

# ==============================
# CONFIGURACIÓN DE LA PÁGINA
# ==============================
st.set_page_config(page_title="Colombia GeoGame", layout="wide")
st.title("🌎 Colombia GeoGame - Aprende y Diviértete!")

# ==============================
# MODOS DE JUEGO
# ==============================
modes = ["Departamentos", "Capitales", "Aeropuertos", "Códigos IATA", "Práctica", "Distancia", "Altitud"]
mode = st.sidebar.selectbox("Modo de Juego", modes)
difficulty = st.sidebar.selectbox("Dificultad", ["Fácil", "Media", "Difícil"])
show_instructions = st.sidebar.checkbox("Mostrar Instrucciones")

# ==============================
# INSTRUCCIONES
# ==============================
if show_instructions:
    st.sidebar.markdown("""
    ## 📝 Cómo Jugar - Colombia GeoGame

    **Modos de juego:**
    - **Departamentos:** Adivina a qué departamento pertenece la ciudad seleccionada.
    - **Capitales:** Adivina la capital del departamento mostrado.
    - **Aeropuertos:** Adivina en qué ciudad se encuentra el aeropuerto.
    - **Códigos IATA:** Adivina el código IATA del aeropuerto indicado.
    - **Práctica:** Muestra toda la información para estudiar.
    - **Distancia:** Selecciona en el mapa la ubicación correcta del aeropuerto.
    - **Altitud:** Adivina la altitud aproximada del aeropuerto.

    **Colores de los indicadores en el mapa:**
    - **Gris:** Punto no seleccionado
    - **Azul:** Punto seleccionado
    - **Verde:** Respuesta correcta
    - **Rojo:** Respuesta incorrecta

    **Controles:**
    - Escribe tu respuesta y pulsa **Responder**.
    - Pulsar **Siguiente Pregunta** para avanzar sin responder.
    - En modo distancia, puedes seleccionar más de un punto para calcular distancia.

    ---
    """)

# ==============================
# VARIABLES DE SESIÓN
# ==============================
if "score" not in st.session_state:
    st.session_state.score = 0
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "best_scores" not in st.session_state:
    st.session_state.best_scores = []
if "selected_points" not in st.session_state:
    st.session_state.selected_points = []

# ==============================
# FUNCIONES DE PREGUNTAS
# ==============================
def get_question(row, mode):
    if mode == "Departamentos":
        return f"¿A qué departamento pertenece la ciudad {row['lugar_aeropuerto']}?", row["departamento"]
    elif mode == "Capitales":
        return f"¿Cuál es la capital del departamento de {row['departamento']}?", row["capital"]
    elif mode == "Aeropuertos":
        return f"¿En qué ciudad está ubicado el aeropuerto {row['aeropuerto']}?", row["lugar_aeropuerto"]
    elif mode == "Códigos IATA":
        return f"¿Cuál es el código IATA del aeropuerto en {row['lugar_aeropuerto']}?", row["iata"]
    elif mode == "Altitud":
        return f"¿Cuál es la altitud aproximada del aeropuerto {row['aeropuerto']} (en metros)?", row["altitud"]
    elif mode == "Práctica":
        return f"""
Departamento: {row['departamento']}  
Capital: {row['capital']}  
Aeropuerto: {row['aeropuerto']}  
Ciudad del Aeropuerto: {row['lugar_aeropuerto']}  
Código IATA: {row['iata']}  
Altitud: {row['altitud']} m
""", None
    elif mode == "Distancia":
        return f"Selecciona la ciudad del aeropuerto {row['aeropuerto']} en el mapa.", (row['latitud'], row['longitud'])
    else:
        return "", None

# ==============================
# SELECCIÓN DE PREGUNTA
# ==============================
if st.session_state.question_index >= len(df):
    st.session_state.question_index = 0

row = df.iloc[st.session_state.question_index]
question, correct_answer = get_question(row, mode)

st.subheader("Pregunta:")
st.write(question)

# ==============================
# MAPA INTERACTIVO MEJORADO
# ==============================
m = folium.Map(location=[4.5709, -74.2973], zoom_start=6, use_container_width=True, use_container_height=True)


for idx, r in df.iterrows():
    color = "gray"
    radius = 8
    if (r['latitud'], r['longitud']) in st.session_state.selected_points:
        color = "blue"
        radius = 12
    folium.CircleMarker(
        location=[r['latitud'], r['longitud']],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=f"{r['departamento']} - {r['capital']} - Altitud: {r['altitud']} m"
    ).add_to(m)

st_data = st_folium(m, width=900, height=500)

# ==============================
# MODO DISTANCIA - SELECCIÓN MÚLTIPLE
# ==============================
if mode == "Distancia" and st_data["last_clicked"]:
    click = (st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"])
    if click in st.session_state.selected_points:
        st.session_state.selected_points.remove(click)
    else:
        st.session_state.selected_points.append(click)

if mode == "Distancia" and correct_answer:
    if st.session_state.selected_points:
        dist = geodesic(correct_answer, st.session_state.selected_points[-1]).kilometers
        if dist < 20:
            st.success(f"✅ Correcto! Estás a {dist:.2f} km del aeropuerto.")
            st.session_state.score += 10
        else:
            st.error(f"❌ Incorrecto! Estás a {dist:.2f} km. La ubicación correcta estaba aquí.")
        time.sleep(5)
        st.session_state.selected_points = []
        st.session_state.question_index += 1

# ==============================
# OTROS MODOS - RESPUESTA TEXTO
# ==============================
if mode not in ["Distancia", "Práctica"] and correct_answer:
    user_input = st.text_input("Escribe tu respuesta aquí:")

    if st.button("Responder"):
        if mode == "Altitud":
            try:
                if abs(float(user_input) - float(correct_answer)) <= 50:  # tolerancia 50 m
                    st.success(f"✅ Correcto! La altitud era {correct_answer} m.")
                    st.session_state.score += 10
                else:
                    st.error(f"❌ Incorrecto! La altitud correcta era {correct_answer} m.")
            except:
                st.error("❌ Ingresa un número válido.")
        else:
            if str(user_input).strip().lower() == str(correct_answer).strip().lower():
                st.success("✅ Correcto!")
                st.session_state.score += 10
            else:
                st.error(f"❌ Incorrecto! La respuesta correcta era: {correct_answer}")
        time.sleep(5)
        st.session_state.question_index += 1

# ==============================
# BOTÓN SIGUIENTE PREGUNTA
# ==============================
if st.button("Siguiente Pregunta"):
    st.session_state.question_index += 1

# ==============================
# PUNTAJE Y HISTORIAL
# ==============================
st.sidebar.subheader("Puntaje Actual")
st.sidebar.write(st.session_state.score)

st.sidebar.subheader("Mejores Puntajes")
best_scores_sorted = sorted(st.session_state.best_scores + [st.session_state.score], reverse=True)[:10]
st.session_state.best_scores = best_scores_sorted
for s in best_scores_sorted:
    st.sidebar.write(s)





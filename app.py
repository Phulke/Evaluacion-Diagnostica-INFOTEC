import streamlit as st
import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import io
from fpdf import FPDF

st.set_page_config(page_title="Evaluación Daignóstica", layout="wide")

#Archivos
archivo_respuestas = "respuestas.csv"
archivo_preguntas = "preguntas.json"
archivo_generaciones = "generaciones.json"

#Contraseña administrador segura 
ADMIN_PASSWORD = st.secrets["admin"]["password"]

#Funciones
def cargar_preguntas():
    with open (archivo_preguntas, "r") as f:
        return json.load(f)

def guardar_respuesta(datos):
    if os.path.exists(archivo_respuestas):
        df = pd.read_csv(archivo_respuestas)
    else:
        df = pd.DataFrame()
        df = pd.concat([df, pd.DataFrame([datos])],
ignore_index=True)
        df.to_csv(archivo_respuestas, index=False)

def calcular_nivel(respuestas, preguntas):
    puntaje = 0
    for r,p in zip(respuestas, preguntas):
        if r == p['correcta']:
            puntaje +=1
    total= len(preguntas)
    porcentaje = puntaje/total
    if porcentaje < 0.25:
        return "Sin conocimientos"
    elif porcentaje < 0.5:
        return "Básico"
    elif porcentaje < 0.75:
        return "Intermedio"
    else:
        return "Avanzado"
    

#Cargar generaciones
if os.path.exists(archivo_generaciones):
    with open(archivo_generaciones, "r") as f:
        generaciones = json.load(f)
else:
    generaciones = []


#Interfaz
st.title("Evaluación Daignóstica")
modo = st.sidebar.selectbox("Seleccionar modo", ["Alumno", "Administrador"])

#Modo Alumno
if modo == "Alumno":
    st.header("Formulario de Evaluación")
    nombre = st.text_input("Nombre completo")
    if generaciones:
        generacion = st.selectbox("Selecciona tu generación", generaciones)
    else:
        st.warning("No hay generaciones disponibles. Contacta con al administrador.")
        generacion = None

    preguntas = cargar_preguntas()
    respuestas = []
    for i, p in enumerate(preguntas):
        r = st.selectbox(f"{i+1}. {p['pregunta']}", p["opciones"], key=i)
        respuestas.append(r)

    if st.button("Enviar"):
        if nombre.strip() == "" or generacion is None:
            st.warning("Por favor ingresa tu nombre y selecciona una generación.")
        else:
            nivel = calcular_nivel(respuestas, preguntas)
            datos = {
                "nombre": nombre,
                "generación": generacion,
                "respuestas": respuestas,
                "puntaje": sum([1 for r,p in zip(respuestas,preguntas) if r == p["correcta"]]),
                "nivel": nivel
            }
            guardar_respuesta(datos)
            st.success(f"Gracias! Tu nivel es: {nivel}")

#Modo administrador
if modo == "Administrador":
    password = st.text_input("Ingrese la contraseña", type = "password")
    if password != ADMIN_PASSWORD:
        st.warning("Contraseña incorrecta")
    else:
        st.header("Panel de administrador")
        opcion_admin = st.selectbox("Seleccionar opción", [
            "Ver respuestas",
            "Agregar preguntas",
            "Estadísticas y gráficos",
            "Exportar CSV",
            "Eliminar Alumno"
            "Administrar generaciones"
        ])

        #Ver respuestas
        if opcion_admin == "Ver respuetas":
            if os.path.exists(archivo_respuestas):
                df = pd.read_csv(archivo_respuestas)
                st.dataframe(df)
            else:
                st.info("No hay respuestas registradas")

        #Agregar preguntas
        elif opcion_admin == "Agregar preguntas":
            nueva_pregunta = st.text_input("Nueva pregunta")
            opciones = st.text_input("Opciones separadas por coma")
            correcta = st.text_input("Opción correcta exacta")
            if st.button("Agregar"):
                preguntas = cargar_preguntas()
                preguntas.append({
                    "pregunta": nueva_pregunta,
                    "opciones": [o.strip() for o in opciones.split(",")],
                    "correcta": o.strip()
                })
                with open (archivo_preguntas, "w") as f:
                    json.dump(preguntas, f)
                    st.success("Pregunta agregada correctamente")
        
        #Estadísticas y gráficos
        elif opcion_admin == " Estadísticas y gráficos":
            if os.path.exists(archivo_respuestas):
                df = pd.read_csv(archivo_respuestas)
                st.subheader("Distrubución de nieveles por generación")
                gen_filter = st.selectbox("Filtrar por generación", ["Todas"] + generaciones)
                if gen_filter != "Todas":
                    df = df[df["generacion"] == gen_filter]
                nivel_counts = df["nivel"].value_counts() 
                st.bar_cart(nivel_counts)

                st.subheader("Histograma de Puntajes")
                fig, ax =plt.sublots()
                ax.hist(df["puntaje"], bins = range (0, len(preguntas)+2), color='skyblue', edgecolor="black")
                ax.set_xlabel("Puntaje")
                ax.set_ylabel("Número de alumnos")
                st.pyplot(fig)

                buf = io.BytesIO()
                fig.savefig(buf, formal="png")
                buf.seek(0)
                st.download_button("Descargar histograma como PNG", buf, file_name="histrograma_puntajes.png", mime= "image/png")

        #Exportar a CSV
        elif opcion_admin == "Exportar CSV":
            if os.path.exists(archivo_preguntas):
                df = pd.read_csv(archivo_respuestas)
                filtro_gen = st.selectbox("Sellecciona una generación para exportar:", ["Todas"] + generaciones)
                if filtro_gen != "Todas":
                    df= df[df["generacion"] == filtro_gen]
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label = "Descargar CSV",
                    data = csv_buffer.getvalue(),
                    file_name = "respuestas_exportadas.csv",
                    mime = "text/csv"
                )
            else:
                st.warning("No hay datos para exportar.")

        #Eliminar alumno
        elif opcion_admin == "Eliminar alumno":
            if os.path.exists(archivo_respuestas):
                df = pd.read_csv(archivo_respuestas)
                gen_filter = st.selectbox("Filtrar por generación", ["Todas"] + generaciones)
                if gen_filter != "Todas":
                    df_filtrado = df[df["generacion"] == gen_filter]
            else:
                df_filtrado = df.copy()

                if not df_filtrado.empty:
                    alumno_a_borrar = st.selectbox("Selecciona el alumno a borrar", df_filtrado["nombre"].tolist())
                    if st.button("Eliminar"):
                        df = df[df["nombre"] != alumno_a_borrar]
                        df.to_csv(archivo_respuestas, index= False)
                        st.success(f"Alumno{alumno_a_borrar}eliminado correctamente")
                    else:
                        st.info("No hay alumnos para eliminar en esta generación.")
                else:
                    st.warning("No hay datos registrados.")

        #Administrador de generaciones
        elif opcion_admin == "Administrar generaciones":
            st.subheader("Generaciones actuales")
            st.write(generaciones if generaciones else "No hay generaciones registradas.")

            nueva_gen = st.text_input("Nombre de nueva la generación")
            if st.button("Agregar generación"):
                if nueva_gen.strip() != "" and nueva_gen not in generaciones:
                    generaciones.append(nueva_gen.strip())
                    with open(archivo_generaciones, "w") as f:
                        json.dump(generaciones, f)
                        st.success(f"Generación'{nueva_gen}'agregada correctamente")
                else:
                    st.warning("Generación inválida o ya existente.")




import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
import json
import os

st.set_page_config(page_title="Reportes RIMO", layout="wide")
st.title("📋 Generador de Reportes de Turno con IA - RIMO")

# Inicializar el cliente de Gemini API (utiliza GEMINI_API_KEY automáticamente)
client = genai.Client()

# --- SECCIÓN 2: CARGA DE TABLERO Y ANÁLISIS ---
st.header("2. Registro de Novedades y Tablero de Producción")

foto_tablero = st.file_uploader(
    "📸 Subir foto del Tablero de Producción:",
    type=["png", "jpg", "jpeg"]
)

# Variable para almacenar el DataFrame analizado
df_resultado = None

if foto_tablero:
    image = Image.open(foto_tablero)
    st.image(image, caption="Imagen cargada del tablero", use_column_width=True)

    if st.button("🔍 Analizar Imagen con IA"):
        with st.spinner("Analizando tablero y extrayendo datos de máquinas..."):
            try:
                # Prompt estructurado para forzar respuesta en JSON estricto
                prompt = """
                Analiza detenidamente la imagen de este tablero de producción. 
                Extrae la información relevante de cada máquina visible y responde EXCLUSIVAMENTE con un arreglo de objetos en formato JSON estricto sin markdown ni bloques de código adicionales.
                
                Estructura por cada máquina:
                [
                  {
                    "Maquina": "Nombre o número de la máquina",
                    "Articulo": "Nombre o referencia del artículo/producto",
                    "Programadas": "Unidades programadas (número o N/A)",
                    "Faltantes": "Unidades faltantes (número o N/A)",
                    "Rechazo": "Cantidad o porcentaje de rechazo (número o N/A)"
                  }
                ]
                """

                # Llamada al modelo vision
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[image, prompt]
                )

                # Limpieza por si la respuesta trae caracteres de formato markdown
                raw_text = response.text.strip().replace("```json", "").replace("```", "")
                datos = json.loads(raw_text)

                # Convertir a DataFrame de Pandas
                df_resultado = pd.DataFrame(datos)
                st.session_state['df_tablero'] = df_resultado
                st.success("¡Análisis completado con éxito!")

            except Exception as e:
                st.error(f"Error al analizar la imagen: {e}")

# Mostrar y permitir editar los datos extraídos
if 'df_tablero' in st.session_state and st.session_state['df_tablero'] is not None:
    st.subheader("📊 Resumen Extraído de Máquinas en Operación")
    st.info("Puedes editar los campos de la tabla directamente si deseas corregir algún número.")
    
    # Renderizar tabla editable
    df_editado = st.data_editor(st.session_state['df_tablero'], use_container_width=True)
    st.session_state['df_tablero'] = df_editado

st.markdown("---")

# --- NOVEDADES MANUALES ---
maquinas_paradas = st.text_input("🔴 Máquinas Paradas / Fuera de Servicio:")
novedades_calidad = st.text_input("🟠 Novedades de Calidad / Rechazos:")
novedades_mantenimiento = st.text_input("🔵 Novedades de Mantenimiento / Servicios:")
observaciones_generales = st.text_area("📝 Observaciones Generales del Turno:")

# --- RESUMEN DE TEXTO LISTO PARA WHATSAPP ---
if st.button("📱 Generar Texto Formateado para WhatsApp"):
    texto_whatsapp = "*📋 REPORTE DE TURNO - RIMO*\n\n"
    
    if 'df_tablero' in st.session_state and not st.session_state['df_tablero'].empty:
        texto_whatsapp += "*📊 MÁQUINAS EN TRABAJO:*\n"
        for _, row in st.session_state['df_tablero'].iterrows():
            texto_whatsapp += (
                f"• *Máq:* {row.get('Maquina', '-')}\n"
                f"  - *Artículo:* {row.get('Articulo', '-')}\n"
                f"  - *Prog:* {row.get('Programadas', '-')}\n"
                f"  - *Faltantes:* {row.get('Faltantes', '-')}\n"
                f"  - *Rechazo:* {row.get('Rechazo', '-')}\n\n"
            )
    
    texto_whatsapp += f"🔴 *Mantenimiento/Paradas:* {maquinas_paradas or 'Ninguna'}\n"
    texto_whatsapp += f"🟠 *Novedades Calidad:* {novedades_calidad or 'Ninguna'}\n"
    texto_whatsapp += f"🔵 *Servicios:* {novedades_mantenimiento or 'Ninguna'}\n"
    texto_whatsapp += f"📝 *Obs:* {observaciones_generales or 'Sin observaciones'}\n"

    st.text_area("Copia y pega este texto directo en WhatsApp:", value=texto_whatsapp, height=300)

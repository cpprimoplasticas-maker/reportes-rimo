import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Reporte de Turno RIMO", layout="wide")

st.title("📋 Generador de Reportes de Turno - RIMO")

# 1. Cargar imagen desde cámara o galería
st.subheader("1. Adjuntar Foto de Evidencia / Planilla")
foto_galeria = st.file_uploader(
    "Seleccionar foto desde la galería", 
    type=["jpg", "jpeg", "png"]
)
foto_camara = st.camera_input("O tomar foto con la cámara del celular")

foto_final = foto_galeria if foto_galeria is not None else foto_camara

# 2. Campo opcional para observaciones adicionales
observaciones = st.text_area(
    "Observaciones adicionales del turno (Novedades, paros, etc.):",
    placeholder="Ejemplo: Máquina W320 detuvo producción por mantenimiento de molde durante 2 horas."
)

# 3. Procesar foto y generar reporte
if foto_final:
    st.image(foto_final, caption="Foto cargada", use_container_width=True)
    
    if st.button("🚀 Generar Tabla de Reporte", type="primary"):
        with st.spinner("Analizando la imagen y extrayendo datos de producción..."):
            try:
                imagen = Image.open(foto_final)
                api_key = st.secrets["GEMINI_API_KEY"]
                client = genai.Client(api_key=api_key)
                
                # Prompt detallado para extraer la tabla exacta
                prompt_reporte = f"""
                Analiza la imagen adjunta (que corresponde a una pantalla o planilla de control de producción de máquinas/inyectoras) y genera un reporte detallado en formato de tabla Markdown.

                Extrae con precisión las siguientes columnas si están presentes en la imagen:
                - Centro / Máquina
                - Orden de Producción (Ord...)
                - Código de Referencia
                - Descripión de la Referencia
                - Ciclos
                - Unidades Producidas (Unds. Prod)
                - Unidades Programadas (Unds. Progra)
                - Total Producido
                - Faltante

                Información adicional / Observaciones del turno ingresadas por el usuario:
                {observaciones}

                Por favor entrega:
                1. Un resumen general del estado del turno en 2 o 3 viñetas.
                2. La tabla completa organizada y limpia con todos los datos extraídos de la foto.
                3. Resumen de alertas o faltantes críticos.
                """
                
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[imagen, prompt_reporte]
                )
                
                st.markdown("---")
                st.subheader("📊 Reporte Generado:")
                st.markdown(response.text)
                
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    st.error("⚠️ Se alcanzó la cuota temporal de la API. Espera 1 minuto antes de reintentar.")
                else:
                    st.error(f"Ocurrió un error al procesar el reporte: {e}")

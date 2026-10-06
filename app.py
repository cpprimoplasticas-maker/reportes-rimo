import streamlit as st
from google import genai
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Generador de Reportes", layout="wide")

st.title("Generador de Reportes con Inteligencia Artificial")

# 1. Obtener la API Key desde los Secrets de Streamlit
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("No se encontró la 'GEMINI_API_KEY' en los Secrets de Streamlit. Por favor, configúrala en el panel de control.")
    st.stop()

# Inicializar cliente oficial de Gemini
client = genai.Client(api_key=api_key)

# 2. Función con Fallback (Modelo principal -> Modelo secundario)
def generar_reporte_con_fallback(imagen, prompt_texto):
    # Primer intento: Modelo principal
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt_texto, imagen]
        )
        return response.text
    except Exception as e_principal:
        st.warning(f"El modelo principal no estuvo disponible. Intentando con modelo de respaldo... ({e_principal})")
        
        # Segundo intento: Modelo de respaldo
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[prompt_texto, imagen]
            )
            return response.text
        except Exception as e_fallback:
            raise Exception(f"Ambos modelos fallaron. Error final: {e_fallback}")

# 3. Interfaz de usuario de Streamlit
uploaded_file = st.file_uploader("Sube una imagen para generar el reporte", type=["jpg", "jpeg", "png"])
prompt_input = st.text_area("Instrucciones para el reporte:", "Analiza la imagen adjunta y genera una tabla detallada con los hallazgos.")

if uploaded_file is not None:
    imagen = Image.open(uploaded_file)
    st.image(imagen, caption="Imagen cargada", width='stretch')

    if st.button("Generar Tabla de Reporte", type="primary"):
        with st.spinner("Procesando reporte con Gemini..."):
            try:
                resultado = generar_reporte_con_fallback(imagen, prompt_input)
                st.success("¡Reporte generado con éxito!")
                st.markdown(resultado)
            except Exception as err:
                st.error(f"Error al procesar la solicitud: {err}")

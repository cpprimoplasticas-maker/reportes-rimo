import streamlit as st
from google import genai
from PIL import Image

# 1. Configuración de la página
st.set_page_config(
    page_title="Sistema de Reportes RIMO",
    page_icon="📊",
    layout="wide"
)

# 2. Obtener la API Key desde los Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ No se encontró la 'GEMINI_API_KEY' en los Secrets de Streamlit. Por favor, asegúrate de configurarla en el panel de Streamlit Cloud.")
    st.stop()

# Inicializar cliente de Gemini
client = genai.Client(api_key=api_key)

# 3. Barra Lateral (Sidebar): Estado e Información de Mantenimiento
with st.sidebar:
    st.header("⚙️ Estado del Sistema")
    st.success("🟢 API Conectada")
    
    st.markdown("---")
    st.subheader("🛠️ Panel de Mantenimiento")
    st.info("""
    **Modo de operación:**
    - Modelo Principal: `gemini-2.0-flash`
    - Modelo Respaldos: `gemini-2.0-flash-lite`
    
    *En caso de saturación del servicio (Error 503), el sistema alternará automáticamente al modelo de respaldo.*
    """)
    
    st.markdown("---")
    st.caption("Sistema de Análisis y Reportes v2.0")

# 4. Título Principal
st.title("📊 Generador de Tablas de Reporte")
st.write("Sube una imagen o documento para analizar y generar el reporte estructurado.")

# 5. Función de generación con Fallback
def generar_reporte_con_fallback(imagen, prompt_texto):
    try:
        # Intento con modelo principal
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt_texto, imagen]
        )
        return response.text
    except Exception as e_principal:
        st.warning("⚠️ El modelo principal se encuentra saturado. Intentando con el modelo de respaldo...")
        try:
            # Intento con modelo de respaldo
            response = client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[prompt_texto, imagen]
            )
            return response.text
        except Exception as e_fallback:
            raise Exception(f"Error en ambos modelos: {e_fallback}")

# 6. Área de Carga y Procesamiento
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Cargar Archivo")
    uploaded_file = st.file_uploader("Elige una imagen (PNG, JPG, JPEG)", type=["jpg", "jpeg", "png"])
    
    prompt_input = st.text_area(
        "Instrucciones para el reporte:", 
        value="Analiza detalladamente la imagen adjunta y genera una tabla completa con los hallazgos, métricas y observaciones clave.",
        height=120
    )

    if uploaded_file is not None:
        imagen = Image.open(uploaded_file)
        st.image(imagen, caption="Vista previa del archivo", use_container_width=True)

with col2:
    st.subheader("2. Resultado del Análisis")
    
    if uploaded_file is not None:
        if st.button("🚀 Generar Tabla de Reporte", type="primary", use_container_width=True):
            with st.spinner("Procesando la imagen y generando la tabla..."):
                try:
                    resultado = generar_reporte_con_fallback(imagen, prompt_input)
                    st.success("¡Reporte generado exitosamente!")
                    st.markdown(resultado)
                except Exception as err:
                    st.error(f"Error durante el procesamiento: {err}")
    else:
        st.info("👈 Sube una imagen en el panel izquierdo para habilitar la generación.")

import streamlit as st
from google import genai
from PIL import Image

st.title("📸 Reporte de Turno")

# Cargar imagen desde cámara o galería
foto_galeria = st.file_uploader(
    "Subir foto o evidencia desde el celular", 
    type=["jpg", "jpeg", "png"]
)
foto_camara = st.camera_input("O tomar una foto directamente")

foto_final = foto_galeria if foto_galeria is not None else foto_camara

if foto_final:
    st.image(foto_final, caption="Foto adjunta al reporte", use_container_width=True)
    
    if st.button("Generar Reporte con Foto"):
        try:
            imagen = Image.open(foto_final)
            
            # Leer la API Key almacenada en los Secrets de Streamlit Cloud
            api_key = st.secrets["GEMINI_API_KEY"]
            client = genai.Client(api_key=api_key)
            
            # Cambio de modelo para solucionar el error 404
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[imagen, "Analiza esta imagen y genera un resumen ejecutivo para el reporte de turno."]
            )
            
            st.subheader("Análisis de la Imagen:")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error al procesar la imagen: {e}")

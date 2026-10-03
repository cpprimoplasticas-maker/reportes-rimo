import streamlit as st
from google import genai
from PIL import Image

st.title("📸 Reporte de Turno")

# 1. Opción para cargar o tomar la foto
foto_galeria = st.file_uploader(
    "Subir foto o evidencia desde el celular", 
    type=["jpg", "jpeg", "png"]
)

foto_camara = st.camera_input("O tomar una foto directamente")

# 2. Definir foto_final para evitar el NameError
foto_final = foto_galeria if foto_galeria is not None else foto_camara

# 3. Mostrar vista previa y botón de procesamiento
if foto_final:
    st.image(foto_final, caption="Foto adjunta al reporte", use_container_width=True)
    
    if st.button("Generar Reporte con Foto"):
        try:
            imagen = Image.open(foto_final)
            client = genai.Client()
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[imagen, "Analiza esta imagen y genera un resumen ejecutivo para el reporte de turno."]
            )
            
            st.subheader("Análisis de la Imagen:")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error al procesar la imagen: {e}")

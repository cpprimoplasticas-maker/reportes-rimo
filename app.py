from google import genai
from PIL import Image

if foto_final and st.button("Generar Reporte con Foto"):
    # Convertir el archivo subido a una imagen manipulable
    imagen = Image.open(foto_final)
    
    # Inicializar el cliente de Gemini
    client = genai.Client()
    
    # Enviar la imagen y la instrucción a la IA
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[imagen, "Analiza esta imagen y genera un resumen ejecutivo para el reporte de turno."]
    )
    
    st.subheader("Análisis de la Imagen:")
    st.write(response.text)

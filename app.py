import google.generativeai as genai
from google.api_core.exceptions import ServiceUnavailable, GoogleAPIError

def generar_reporte_con_fallback(imagen_bytes, prompt_texto):
    # 1. Intentar con el modelo principal (ejemplo: gemini-1.5-pro)
    try:
        model_principal = genai.GenerativeModel('gemini-1.5-pro')
        response = model_principal.generate_content([prompt_texto, imagen_bytes])
        return response.text

    except ServiceUnavailable:
        # 2. Si el modelo principal está saturado (503), intentar con el modelo de respaldo
        try:
            model_fallback = genai.GenerativeModel('gemini-1.5-flash')
            response = model_fallback.generate_content([prompt_texto, imagen_bytes])
            return response.text
        except Exception as e:
            raise Exception(f"El servicio secundario también falló: {e}")

    except GoogleAPIError as e:
        raise Exception(f"Error de la API de Google: {e}")

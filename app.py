# 2. Función con Fallback (Modelo principal -> Modelo secundario)
def generar_reporte_con_fallback(imagen, prompt_texto):
    # Primer intento: Modelo principal
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt_texto, imagen]
        )
        return response.text
    except Exception as e_principal:
        st.warning(f"El modelo principal no estuvo disponible. Intentando con modelo de respaldo...")
        
        # Segundo intento: Modelo de respaldo (lite)
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[prompt_texto, imagen]
            )
            return response.text
        except Exception as e_fallback:
            raise Exception(f"Ambos modelos fallaron. Error final: {e_fallback}")

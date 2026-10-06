import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
import json
import time

st.set_page_config(page_title="Reportes RIMO", layout="wide")
st.title("📋 Generador de Reportes de Turno con IA - RIMO")

# Inicializar cliente de Gemini API
client = genai.Client()

# Lista de modelos en orden de preferencia por si alguno está saturado (503)
MODELOS_DISPONIBLES = [
    'gemini-3.8-flash',
    'gemini-2.5-flash',
    'gemini-2.0-flash'
]

# --- SECCIÓN 2: CARGA DE TABLERO Y ANÁLISIS ---
st.header("2. Registro de Novedades y Tablero de Producción")

foto_tablero = st.file_uploader(
    "📸 Subir foto del Tablero de Producción:",
    type=["png", "jpg", "jpeg"]
)

df_resultado = None

if foto_tablero:
    image = Image.open(foto_tablero)
    st.image(image, caption="Imagen cargada del tablero", use_column_width=True)

    if st.button("🔍 Analizar Imagen con IA"):
        with st.spinner("Analizando tablero y extrayendo datos de máquinas..."):
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

            exito = False
            error_msg = ""

            # Probar modelos disponibles en caso de saturación 503
            for modelo in MODELOS_DISPONIBLES:
                for intento in range(2):  # Reintentar hasta 2 veces por modelo
                    try:
                        response = client.models.generate_content(
                            model=modelo,
                            contents=[image, prompt]
                        )

                        # Limpieza del texto JSON
                        raw_text = response.text.strip().replace("```json", "").replace("```", "")
                        datos = json.loads(raw_text)

                        # Convertir a DataFrame de Pandas
                        df_resultado = pd.DataFrame(datos)
                        st.session_state['df_tablero'] = df_resultado
                        st.success(f"¡Análisis completado con éxito (usando {modelo})!")
                        exito = True
                        break
                    except Exception as e:
                        error_msg = str(e)
                        time.sleep(1) # Esperar 1 segundo antes de reintentar
                
                if exito:
                    break

            if not exito:
                st.error(f"Los servidores están saturados temporalmente. Intenta nuevamente en 30 segundos. Detalle: {error_msg}")

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

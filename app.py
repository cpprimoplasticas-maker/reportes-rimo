import streamlit as st
from google import genai
from PIL import Image
import urllib.parse

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

# 2. Formulario para novedades y estado de máquinas
st.subheader("2. Registro de Novedades por Máquina")

col1, col2 = st.columns(2)

with col1:
    maquinas_paradas = st.text_input(
        "Máquinas Paradas / Fuera de Servicio:",
        placeholder="Ejemplo: W320 (Daño en molde), T650 (Sin material)"
    )
    
    novedades_calidad = st.text_area(
        "Novedades de Calidad / Rechazos:",
        placeholder="Ejemplo: Rebabas en producto de máquina W880-2 durante las primeras 2 horas."
    )

with col2:
    novedades_mantenimiento = st.text_area(
        "Novedades de Mantenimiento / Servicios:",
        placeholder="Ejemplo: Fuga de aceite en unidad de inyección máquina W1600."
    )
    
    observaciones_generales = st.text_area(
        "Observaciones Generales del Turno:",
        placeholder="Ejemplo: Cambio de turno realizado a tiempo. Sin faltantes de personal."
    )

# 3. Procesar foto y generar reporte
if foto_final:
    st.image(foto_final, caption="Foto cargada", use_container_width=True)
    
    if st.button("🚀 Generar Tabla de Reporte", type="primary"):
        with st.spinner("Analizando la imagen y procesando el reporte..."):
            try:
                imagen = Image.open(foto_final)
                api_key = st.secrets["GEMINI_API_KEY"]
                client = genai.Client(api_key=api_key)
                
                # Consolidar novedades ingresadas por el usuario
                novedades_texto = f"""
                * Máquinas Paradas: {maquinas_paradas if maquinas_paradas else 'Ninguna'}
                * Novedades de Calidad: {novedades_calidad if novedades_calidad else 'Sin novedades'}
                * Novedades de Mantenimiento: {novedades_mantenimiento if novedades_mantenimiento else 'Sin novedades'}
                * Observaciones Generales: {observaciones_generales if observaciones_generales else 'Sin observaciones'}
                """
                
                # Prompt estructurado para la IA
                prompt_reporte = f"""
                Analiza la imagen adjunta (planilla/pantalla de producción) y compón un reporte de turno claro en texto plano/Markdown.

                Usa esta estructura:
                📌 *REPORTE DE TURNO - RIMO*

                📊 *RESUMEN DE PRODUCCIÓN:*
                (Genera la tabla con: Centro/Máquina, Orden, Referencia, Unds Producidas, Unds Programadas, Faltantes).

                ⚠️ *NOVEDADES Y ESTADO DE MÁQUINAS:*
                {novedades_texto}

                🚨 *ALERTAS CRÍTICAS:*
                (Identifica las 2 o 3 máquinas con mayor desfase o faltante según la foto).
                """
                
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[imagen, prompt_reporte]
                )
                
                reporte_resultado = response.text
                
                # Guardar el resultado en la sesión
                st.session_state["reporte_texto"] = reporte_resultado
                
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    st.error("⚠️ Se alcanzó la cuota temporal de la API. Espera 1 minuto antes de reintentar.")
                else:
                    st.error(f"Ocurrió un error al procesar el reporte: {e}")

# 4. Mostrar reporte generado y botón de compartir por WhatsApp
if "reporte_texto" in st.session_state:
    st.markdown("---")
    st.subheader("📊 Reporte Final Generado:")
    st.markdown(st.session_state["reporte_texto"])
    
    # Preparar el enlace de WhatsApp
    texto_encoded = urllib.parse.quote(st.session_state["reporte_texto"])
    whatsapp_url = f"https://api.whatsapp.com/send?text={texto_encoded}"
    
    st.markdown("---")
    st.subheader("📲 Compartir Reporte:")
    st.markdown(
        f'''
        <a href="{whatsapp_url}" target="_blank">
            <button style="
                background-color: #25D366;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
            ">
                📲 Compartir Reporte por WhatsApp
            </button>
        </a>
        ''',
        unsafe_allow_html=True
    )

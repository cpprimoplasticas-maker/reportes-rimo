import streamlit as st
from google import genai
from PIL import Image
import urllib.parse
import time

st.set_page_config(page_title="Reporte de Turno RIMO", layout="wide")

st.title("📋 Generador de Reportes de Turno - RIMO")

# --- FUNCIONES DE UTILIDAD ---

def optimizar_imagen(imagen_uploaded, max_size=(1024, 1024)):
    """Reduce el tamaño de la imagen para ahorrar cuota de API."""
    img = Image.open(imagen_uploaded)
    img.thumbnail(max_size)
    return img

# --- INTERFAZ DE LA APP ---

# 1. Cargar imagen desde cámara o galería
st.subheader("1. Adjuntar Foto de Evidencia / Planilla")
foto_galeria = st.file_uploader(
    "Seleccionar foto desde la galería", 
    type=["jpg", "jpeg", "png"]
)
foto_camara = st.camera_input("O tomar foto con la cámara del celular")

foto_final = foto_galeria if foto_galeria is not None else foto_camara

# 2. Formulario para novedades
st.subheader("2. Registro de Novedades por Máquina")
col1, col2 = st.columns(2)

with col1:
    maquinas_paradas = st.text_input(
        "Máquinas Paradas / Fuera de Servicio:",
        placeholder="Ejemplo: W320 (Daño en molde), T650 (Sin material)"
    )
    novedades_calidad = st.text_area(
        "Novedades de Calidad / Rechazos:",
        placeholder="Ejemplo: Rebabas en producto de máquina W880-2."
    )

with col2:
    novedades_mantenimiento = st.text_area(
        "Novedades de Mantenimiento / Servicios:",
        placeholder="Ejemplo: Fuga de aceite en unidad de inyección W1600."
    )
    observaciones_generales = st.text_area(
        "Observaciones Generales del Turno:",
        placeholder="Ejemplo: Cambio de turno realizado a tiempo."
    )

# 3. Procesar foto y generar reporte
if foto_final:
    st.image(foto_final, caption="Foto cargada", use_container_width=True)
    
    if st.button("🚀 Generar Tabla de Reporte", type="primary"):
        with st.spinner("Analizando la imagen y procesando el reporte..."):
            try:
                imagen = optimizar_imagen(foto_final)
                
                api_key = st.secrets["GEMINI_API_KEY"]
                client = genai.Client(api_key=api_key)
                
                novedades_texto = f"""
                * Máquinas Paradas: {maquinas_paradas if maquinas_paradas else 'Ninguna'}
                * Novedades de Calidad: {novedades_calidad if novedades_calidad else 'Sin novedades'}
                * Novedades de Mantenimiento: {novedades_mantenimiento if novedades_mantenimiento else 'Sin novedades'}
                * Observaciones Generales: {observaciones_generales if observaciones_generales else 'Sin observaciones'}
                """
                
                prompt_reporte = f"""
                Analiza la imagen adjunta (planilla/pantalla de producción) y compón un reporte de turno claro en texto plano/Markdown.

                Usa esta estructura:
                📌 *REPORTE DE TURNO - RIMO*

                📊 *RESUMEN DE PRODUCCIÓN:*
                (Genera la tabla con las columnas: Centro/Máquina, Orden, Referencia, Unds Producidas, Unds Programadas, Faltantes. Extrae TODOS los datos de la foto).

                ⚠️ *NOVEDADES Y ESTADO DE MÁQUINAS:*
                {novedades_texto}

                🚨 *ALERTAS CRÍTICAS:*
                (Identifica las 2 o 3 máquinas con mayor desfase o faltante según la foto).
                """
                
                response = None
                for intento in range(3):
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[imagen, prompt_reporte]
                        )
                        break
                    except Exception as err:
                        if ("429" in str(err) or "RESOURCE_EXHAUSTED" in str(err)) and intento < 2:
                            time.sleep(3 * (intento + 1))
                        else:
                            raise err
                
                if response:
                    st.session_state["reporte_texto"] = response.text
                    st.rerun()
                
            except Exception as e:
                st.error(f"Ocurrió un error al procesar el reporte: {e}")

# 4. Mostrar reporte generado en tarjeta HTML estilizada y WhatsApp
if "reporte_texto" in st.session_state:
    st.markdown("---")
    st.subheader("📊 Reporte Final Generado:")
    
    # Renderizado dentro de una tarjeta HTML/CSS limpia
    st.markdown(
        f"""
        <div style="
            background-color: #FFFFFF; 
            padding: 24px; 
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            color: #0F172A;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        ">
            {st.session_state["reporte_texto"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Botón para compartir directo a WhatsApp
    texto_encoded = urllib.parse.quote(st.session_state["reporte_texto"])
    whatsapp_url = f"https://api.whatsapp.com/send?text={texto_encoded}"
    
    st.markdown("---")
    st.subheader("📲 Compartir Reporte:")
    st.markdown(
        f'''
        <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
            <button style="
                background-color: #25D366;
                color: white;
                border: none;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                text-align: center;
                display: block;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                📲 Compartir Reporte por WhatsApp
            </button>
        </a>
        ''',
        unsafe_allow_html=True
    )

import streamlit as st
from google import genai
from PIL import Image, ImageDraw, ImageFont
import urllib.parse
import time
import io

st.set_page_config(page_title="Reporte de Turno RIMO", layout="wide")

st.title("📋 Generador de Reportes de Turno - RIMO")

# --- FUNCIONES DE UTILIDAD ---

def optimizar_imagen(imagen_uploaded, max_size=(1024, 1024)):
    """Reduce el tamaño de la imagen para ahorrar cuota de API."""
    img = Image.open(imagen_uploaded)
    img.thumbnail(max_size)
    return img

def texto_a_imagen(texto_markdown):
    """Convierte el reporte Markdown en una imagen PNG limpia de forma segura."""
    ancho = 800
    color_fondo = (255, 255, 255)
    color_texto = (0, 0, 0)
    margen = 30
    
    # Cargar fuente básica
    font = ImageFont.load_default()

    lineas = texto_markdown.split('\n')
    lineas_procesadas = []

    for linea in lineas:
        linea_limpia = linea.replace('**', '').replace('*', '')
        # Divide frases muy largas en varias líneas
        while len(linea_limpia) > 80:
            corte = linea_limpia[:80].rfind(' ')
            if corte == -1: 
                corte = 80
            lineas_procesadas.append(linea_limpia[:corte])
            linea_limpia = linea_limpia[corte:].lstrip()
        lineas_procesadas.append(linea_limpia)

    alto_linea = 22
    alto_final = max(300, (len(lineas_procesadas) * alto_linea) + (2 * margen))
    
    img_final = Image.new('RGB', (ancho, alto_final), color_fondo)
    draw = ImageDraw.Draw(img_final)
    
    y = margen
    for text_line in lineas_procesadas:
        draw.text((margen, y), text_line, font=font, fill=color_texto)
        y += alto_linea
        
    img_bytes = io.BytesIO()
    img_final.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

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
                    try:
                        st.session_state["reporte_imagen"] = texto_a_imagen(response.text)
                    except Exception as img_err:
                        st.warning("No se pudo generar la imagen del reporte, pero aquí está el texto.")
                    st.rerun()
                
            except Exception as e:
                st.error(f"Ocurrió un error al procesar el reporte: {e}")

# 4. Mostrar reporte generado y opciones de compartir
if "reporte_texto" in st.session_state:
    st.markdown("---")
    st.subheader("📊 Reporte Final Generado:")
    
    # Muestra el texto Markdown formateado en la app
    st.markdown(st.session_state["reporte_texto"])

    # Opción de descargar imagen si se pudo generar
    if "reporte_imagen" in st.session_state:
        st.markdown("---")
        st.subheader("🖼️ Guardar para WhatsApp:")
        st.image(st.session_state["reporte_imagen"], caption="Vista previa en formato imagen", use_container_width=True)
        st.download_button(
            label="⬇️ Descargar Imagen del Reporte",
            data=st.session_state["reporte_imagen"],
            file_name="reporte_turno_rimo.png",
            mime="image/png"
        )

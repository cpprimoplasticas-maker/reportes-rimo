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
    """Convierte el reporte Markdown en una imagen limpia para compartir."""
    # Configuración de la imagen de salida
    ancho = 800
    alto_inicial = 2000 # Ajustable automáticamente
    color_fondo = (255, 255, 255) # Blanco
    color_texto = (0, 0, 0) # Negro
    margen = 40
    
    # Intentar cargar una fuente legible (arial o similar)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        font_bold = ImageFont.truetype("arialbd.ttf", 22)
    except IOError:
        font = ImageFont.load_default()
        font_bold = font

    # Crear una imagen temporal para calcular el alto necesario
    img_temp = Image.new('RGB', (ancho, alto_inicial), color_fondo)
    draw_temp = ImageDraw.Draw(img_temp)
    
    lineas = texto_markdown.split('\n')
    y_text = margen
    
    # Calcular alto total
    for linea in lineas:
        # Detectar títulos o negritas simples (**texto**)
        es_negrita = linea.startswith('**') or linea.startswith('📌') or linea.startswith('📊') or linea.startswith('⚠️') or linea.startswith('🚨')
        fuente_usar = font_bold if es_negrita else font
        linea_limpia = linea.replace('**', '')
        
        # Envolver texto largo
        palabras = linea_limpia.split(' ')
        linea_actual = ''
        for palabra in palabras:
            test_linea = linea_actual + palabra + ' '
            width, height = draw_temp.textsize(test_linea, font=fuente_usar)
            if width < (ancho - 2 * margen):
                linea_actual = test_linea
            else:
                y_text += height + 5
                linea_actual = palabra + ' '
        y_text += height + 5

    # Crear la imagen final con el alto correcto
    alto_final = y_text + margen
    img_final = Image.new('RGB', (ancho, alto_final), color_fondo)
    draw = ImageDraw.Draw(img_final)
    
    # Dibujar el texto
    y_text = margen
    for linea in lineas:
        es_negrita = linea.startswith('**') or linea.startswith('📌') or linea.startswith('📊') or linea.startswith('⚠️') or linea.startswith('🚨')
        fuente_usar = font_bold if es_negrita else font
        linea_limpia = linea.replace('**', '')
        
        palabras = linea_limpia.split(' ')
        linea_actual = ''
        for palabra in palabras:
            test_linea = linea_actual + palabra + ' '
            width, height = draw.textsize(test_linea, font=fuente_usar)
            if width < (ancho - 2 * margen):
                linea_actual = test_linea
            else:
                draw.text((margen, y_text), linea_actual, font=fuente_usar, fill=color_texto)
                y_text += height + 5
                linea_actual = palabra + ' '
        draw.text((margen, y_text), linea_actual, font=fuente_usar, fill=color_texto)
        y_text += height + 5
        
    # Convertir a bytes para Streamlit
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
                # Optimizar imagen antes de enviar
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
                
                # Bucle de reintentos (429)
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
                    # Guardar texto del reporte y generar la imagen
                    st.session_state["reporte_texto"] = response.text
                    with st.spinner("🔢 Convirtiendo el reporte a imagen..."):
                        st.session_state["reporte_imagen"] = texto_a_imagen(response.text)
                    st.rerun()
                
            except Exception as e:
                st.error(f"Ocurrió un error al procesar el reporte: {e}")

# 4. Mostrar reporte generado y botón de compartir
if "reporte_texto" in st.session_state:
    st.markdown("---")
    st.subheader("📊 Reporte Final Generado:")
    
    # Mostrar la imagen del reporte (así se verá en WhatsApp)
    st.image(st.session_state["reporte_imagen"], caption="Vista previa del reporte para compartir", use_container_width=True)

    # Botón para descargar la imagen
    st.download_button(
        label="⬇️ Descargar Imagen del Reporte",
        data=st.session_state["reporte_imagen"],
        file_name="reporte_turno_rimo.png",
        mime="image/png"
    )
    
    # Botón de WhatsApp (con CSS personalizado)
    st.markdown("---")
    st.subheader("📲 Compartir Reporte:")
    st.markdown(
        f'''
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
            text-align: center;
            display: block;
            margin-top: 10px;
        " onclick="window.alert('Para compartir por WhatsApp:\\n1. Presiona el botón ⬇️ Descargar Imagen del Reporte.\\n2. Abre WhatsApp y envía la imagen descargada a tu grupo.')">
            📲 Compartir Reporte por WhatsApp
        </button>
        ''',
        unsafe_allow_html=True
    )

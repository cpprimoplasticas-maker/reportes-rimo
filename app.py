import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

st.title("📋 Generador de Reportes de Turno - RIMO")

# --- SECCIÓN 2: REGISTRO DE NOVEDADES POR MÁQUINA ---
st.header("2. Registro de Novedades por Máquina")

# Formulario para capturar los datos
maquinas_paradas = st.text_input(
    "Máquinas Paradas / Fuera de Servicio:",
    placeholder="Ejemplo: W320 (Daño en molde), T650 (Sin material)"
)

novedades_calidad = st.text_input(
    "Novedades de Calidad / Rechazos:",
    placeholder="Ejemplo: Rebabas en producto de máquina W880-2."
)

novedades_mantenimiento = st.text_input(
    "Novedades de Mantenimiento / Servicios:",
    placeholder="Ejemplo: Fuga de aceite en unidad de inyección W1600."
)

observaciones_generales = st.text_area(
    "Observaciones Generales del Turno:",
    placeholder="Ejemplo: Cambio de turno realizado a tiempo."
)

# --- FUNCIÓN PARA GENERAR LA IMAGEN ---
def generar_imagen_reporte(m_paradas, n_calidad, n_mant, obs):
    # Dimensiones de la imagen (Ancho x Alto en píxeles)
    width, height = 800, 650
    # Crear lienzo blanco
    img = Image.new('RGB', (width, height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)

    # Cargar fuentes del sistema (fallback a la fuente por defecto si no las encuentra)
    try:
        title_font = ImageFont.truetype("arial.ttf", 26)
        header_font = ImageFont.truetype("arial.ttf", 18)
        text_font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        title_font = header_font = text_font = ImageFont.load_default()

    # Encabezado (Banda Superior)
    draw.rectangle([0, 0, width, 80], fill='#1E3A8A')  # Azul oscuro
    draw.text((30, 25), "REPORTE DE TURNO - RIMO", fill='#FFFFFF', font=title_font)

    # Dibujar Secciones y Texto
    y = 110
    
    secciones = [
        ("🔴 Máquinas Paradas / Fuera de Servicio:", m_paradas or "Ninguna"),
        ("🟠 Novedades de Calidad / Rechazos:", n_calidad or "Ninguna"),
        ("🔵 Novedades de Mantenimiento / Servicios:", n_mant or "Ninguna"),
        ("📝 Observaciones Generales del Turno:", obs or "Sin observaciones")
    ]

    for titulo, contenido in secciones:
        # Título del bloque
        draw.text((30, y), titulo, fill='#1F2937', font=header_font)
        y += 28
        
        # Fondo claro para el texto
        draw.rectangle([30, y, width - 30, y + 45], fill='#F3F4F6', outline='#E5E7EB', width=1)
        # Contenido del texto
        draw.text((40, y + 12), contenido[:90], fill='#374151', font=text_font)
        y += 65

    # Pie de página
    draw.text((30, height - 30), "Generado desde App de Reportes RIMO", fill='#9CA3AF', font=text_font)

    # Guardar en memoria (BytesIO)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


# --- BOTÓN Y VISTA PREVIA ---
st.markdown("---")
st.subheader("📸 Compartir Reporte en WhatsApp como Imagen")

if st.button("🖼️ Generar Imagen del Reporte"):
    # Generar la imagen con las entradas del usuario
    imagen_bytes = generar_imagen_reporte(
        maquinas_paradas,
        novedades_calidad,
        novedades_mantenimiento,
        observaciones_generales
    )

    # Vista previa en la app
    st.image(imagen_bytes, caption="Vista previa de la imagen generada", use_column_width=True)

    # Botón oficial de descarga
    st.download_button(
        label="📥 Descargar Imagen para WhatsApp",
        data=imagen_bytes,
        file_name="Reporte_Turno_RIMO.png",
        mime="image/png"
    )

# CONTEXTO DE DESARROLLO DE LA APP: REPORTES RIMO

**Objetivo:** Crear una aplicación web con Streamlit (Python) que permita a los operadores de planta en "RIMO" generar reportes de turno automáticos.

**Funcionalidad principal:**
1. El usuario toma una foto de la pantalla o planilla de control de producción (donde se ven códigos de referencia, máquinas, unidades programadas, producidas, ciclos, etc.).
2. El usuario llena opcionalmente casillas de novedades por máquina (máquinas paradas, calidad, mantenimiento).
3. La app envía la foto y novedades a Gemini-3.8-Flash.
4. Gemini extrae los datos de la foto, estructura una tabla detallada y compone un reporte de turno en texto Markdown.
5. La app muestra el reporte y habilita un botón verde para "Compartir Reporte por WhatsApp", el cual abre WhatsApp con el texto pre-cargado.

**Soluciones a Problemas Técnicos Implementadas:**
- Se ha implementado una optimización de imagen (`imagen.thumbnail((1024, 1024))`) antes de enviarla a la API. Esto reduce el peso de las fotos de los celulares de ~10 MB a ~300 KB, ahorrando ancho de banda y cuota de la API.
- Se ha implementado un bucle de reintentos con `time.sleep` si la API devuelve un error de alta demanda (429/RESOURCE_EXHAUSTED).

---

## CÓDIGO COMPLETO Y ACTUAL DE `app.py`:

A continuación, el código que debe ir en el repositorio de GitHub:

```python
import streamlit as st
from google import genai
from PIL import Image
import urllib.parse
import time

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
                # 🔹 OPTIMIZACIÓN DE LA IMAGEN: Reducir peso antes de enviar a Gemini
                imagen = Image.open(foto_final)
                imagen.thumbnail((1024, 1024)) # Escalar a max 1024px, reduce a ~300KB
                
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
                
                # 🔹 BUCLE DE REINTENTOS PARA EVITAR ERRORES DE ALTA DEMANDA (429)
                response = None
                for intento in range(3):
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[imagen, prompt_reporte]
                        )
                        break # Si funciona, salir del bucle
                    except Exception as err:
                        err_msg = str(err)
                        # Si es error de cuota o saturación, esperar y reintentar
                        if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and intento < 2:
                            time.sleep(3 * (intento + 1))  # Espera exponencial: 3s, luego 6s
                        else:
                            raise err # Si es otro error o agostamos intentos, lanzar error
                
                if response:
                    # Guardar el resultado en la sesión para que persista
                    st.session_state["reporte_texto"] = response.text
                
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    st.warning("⚠️ Servidores muy ocupados. Espera 30 segundos e intenta de nuevo el botón.")
                else:
                    st.error(f"Ocurrió un error al procesar el reporte: {e}")

# 4. Mostrar reporte generado y botón de compartir por WhatsApp
if "reporte_texto" in st.session_state:
    st.markdown("---")
    st.subheader("📊 Reporte Final Generado:")
    st.markdown(st.session_state["reporte_texto"])
    
    # Preparar el enlace de WhatsApp con el texto codificado
    texto_encoded = urllib.parse.quote(st.session_state["reporte_texto"])
    whatsapp_url = f"[https://api.whatsapp.com/send?text=](https://api.whatsapp.com/send?text=){texto_encoded}"
    
    # Botón verde de WhatsApp con CSS personalizado
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
                text-align: center;
                display: block;
                margin-top: 10px;
            ">
                📲 Compartir Reporte por WhatsApp
            </button>
        </a>
        ''',
        unsafe_allow_html=True
    )

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import json
import os
from datetime import datetime
from google import genai
from google.genai import types

# Configuración de la página
st.set_page_config(page_title="Reporte de Turno - Rimo Plásticas", page_icon="🏭", layout="wide")

st.title("🏭 Generador de Reporte de Turno")
st.subheader("RIMO Plásticas S.A. — Formato Oficial FR-PRO-12")

# --- LISTA OFICIAL DE MÁQUINAS (Como respaldo) ---
LISTA_MAQUINAS = [
    "320", "128-3", "400", "680", "680-2", "1600", "880", "880-2", 
    "268", "680-3", "650-2", "480", "218", "320-2", "1080", "168-3", 
    "880-3", "268-2", "500-2", "128-2", "168-2", "128", "168", "650", 
    "88", "320-3", "850", "900"
]

# --- OPCIONES DESPLEGABLES DE OBSERVACIONES ---
OPCIONES_NOVEDADES = [
    "Sin novedad / Trabaja normal",
    "Fuga de agua / refrigeración",
    "Ajuste de parámetros",
    "Mantenimiento mecánico",
    "Mantenimiento eléctrico",
    "Falta de materia prima",
    "Problema de calidad / deformación",
    "Parada programada / sin molde",
    "Falta de personal / operario",
    "Otro (especificar)"
]

# --- BARRA LATERAL (Configuraciones) ---
st.sidebar.header("⚙️ Configuración del Reporte")
api_key = st.sidebar.text_input("Ingresa tu API Key de Gemini:", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Datos del Encabezado")

responsable = st.sidebar.text_input("Responsable:", value="", placeholder="Ingresa el nombre del responsable")
fecha_seleccionada = st.sidebar.date_input("Fecha:", value=datetime.now())
turno = st.sidebar.selectbox("Turno:", options=[1, 2, 3], index=1)

fecha_str = fecha_seleccionada.strftime("%d/%m/%Y")

HISTORIAL_FILE = "historial_reportes.csv"

def guardar_en_historial(fecha_rep, turno_rep, resp_rep, contenido_rep):
    nuevo_registro = pd.DataFrame([{
        "Fecha y Hora Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Fecha Reporte": fecha_rep,
        "Turno": turno_rep,
        "Responsable": resp_rep,
        "Reporte Generado": contenido_rep
    }])
    
    if os.path.exists(HISTORIAL_FILE):
        nuevo_registro.to_csv(HISTORIAL_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        nuevo_registro.to_csv(HISTORIAL_FILE, index=False, encoding='utf-8-sig')

def generar_imagen_reporte_oficial(df_tabla, resp, fecha, tur, output_path="reporte_turno.png"):
    df_formatted = df_tabla.copy()
    
    max_chars = {
        "Responsable": 18,
        "Turno": 6,
        "Fecha": 10,
        "Máquina": 10,
        "Presión de cierre": 10,
        "Código Artículo": 10,
        "Código Mold": 8,
        "Referencia": 25,
        "Observaciones": 35
    }

    for col in df_formatted.columns:
        limit = max_chars.get(col, 20)
        df_formatted[col] = df_formatted[col].astype(str).apply(
            lambda x: "\n".join(textwrap.wrap(x, width=limit)) if len(x) > limit else x
        )

    max_lines_per_row = [
        max([len(str(val).split('\n')) for val in row]) for row in df_formatted.values
    ] if len(df_formatted) > 0 else [1]
    
    total_height = max(7, sum(max_lines_per_row) * 0.45 + 3.0)

    fig, ax = plt.subplots(figsize=(18, total_height), dpi=200)
    ax.axis('off')

    title_text = "REPORTE DE TURNO"
    sub_text = "CÓDIGO: FR-PRO-12  |  VERSIÓN: 1  |  FECHA FORMATO: Julio 26 de 2025"
    info_header = f"Responsable: {resp}    |    Fecha: {fecha}    |    Turno: {tur}"

    plt.text(0.5, 0.96, title_text, fontsize=18, fontweight='bold', ha='center', va='top', transform=ax.transAxes)
    plt.text(0.98, 0.98, sub_text, fontsize=9, color='gray', ha='right', va='top', transform=ax.transAxes)
    plt.text(0.5, 0.91, info_header, fontsize=11, fontweight='bold', ha='center', va='top', transform=ax.transAxes,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f2f6", edgecolor="#cccccc"))

    col_widths = {
        "Responsable": 0.11,
        "Turno": 0.04,
        "Fecha": 0.07,
        "Máquina": 0.06,
        "Presión de cierre": 0.08,
        "Código Artículo": 0.08,
        "Código Mold": 0.07,
        "Referencia": 0.20,
        "Observaciones": 0.29
    }
    widths = [col_widths.get(c, 0.1) for c in df_formatted.columns]

    tabla = ax.table(
        cellText=df_formatted.values,
        colLabels=df_formatted.columns,
        colWidths=widths,
        cellLoc='center',
        loc='center',
        bbox=[0.01, 0.02, 0.98, 0.83]
    )

    tabla.auto_set_font_size(False)
    tabla.set_fontsize(8.5)

    for (row, col), cell in tabla.get_celld().items():
        cell.set_edgecolor('#333333')
        cell.set_linewidth(0.8)
        
        if row == 0:
            cell.set_facecolor('#d9e1f2')
            cell.set_text_props(weight='bold', color='black', ha='center', va='center')
        else:
            if row % 2 == 0:
                cell.set_facecolor('#f9fbfd')
            else:
                cell.set_facecolor('#ffffff')
            
            col_name = df_formatted.columns[col]
            if col_name in ["Referencia", "Observaciones", "Responsable"]:
                cell.set_text_props(ha='left', va='center')
            else:
                cell.set_text_props(ha='center', va='center')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    return output_path

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2 = st.tabs(["🚀 Crear Reporte", "📜 Historial de Reportes"])

with tab1:
    if not api_key:
        st.info("💡 Por favor, ingresa tu API Key de Gemini en el menú lateral para comenzar.")
    else:
        uploaded_file = st.file_uploader("1. Sube la captura de pantalla de Elemental Pro", type=["png", "jpg", "jpeg"])

        if uploaded_file:
            st.image(uploaded_file, caption="Captura cargada", width=450)

            # Botón para detectar automáticamente las máquinas con punto verde
            if st.button("🔍 Detectar Máquinas Activas (Punto Verde)"):
                with st.spinner("Analizando la imagen para identificar las máquinas activas..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        image_bytes = uploaded_file.getvalue()
                        image_part = types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=uploaded_file.type,
                        )

                        prompt_deteccion = """
                        Analiza la imagen adjunta de Elemental Pro. 
                        Identifica únicamente las máquinas que estén ACTIVAS (las que tienen un indicador o punto VERDE al lado de su nombre o número).
                        Ignora completamente las máquinas que tengan punto rojo, gris o estén inactivas.

                        Devuelve EXCLUSIVAMENTE una lista JSON con los nombres de las máquinas activas encontradas, por ejemplo:
                        ["850", "880-3", "680-2"]
                        No agregues texto explicativo ni marcas markdown como ```json.
                        """

                        response_det = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=[prompt_deteccion, image_part]
                        )

                        raw_det = response_det.text.strip()
                        if "```" in raw_det:
                            raw_det = raw_det.replace("```json", "").replace("```", "").strip()

                        maquinas_detectadas = json.loads(raw_det)
                        st.session_state['maquinas_activas'] = maquinas_detectadas
                        st.success(f"✅ Se detectaron {len(maquinas_detectadas)} máquinas activas: {', '.join(maquinas_detectadas)}")

                    except Exception as e:
                        st.error(f"Ocurrió un error al detectar las máquinas: {e}")

        st.markdown("---")
        st.subheader("2. Revisa las máquinas activas e ingresa sus novedades")

        # Usar la lista detectada automáticamente o permitir ajuste manual
        default_maquinas = st.session_state.get('maquinas_activas', ["850", "880-3", "680-2"])

        maquinas_seleccionadas = st.multiselect(
            "Máquinas a incluir en el reporte (detectadas automáticamente / modificables):",
            options=LISTA_MAQUINAS,
            default=[m for m in default_maquinas if m in LISTA_MAQUINAS] if default_maquinas else []
        )

        datos_maquinas = []

        if maquinas_seleccionadas:
            st.write("### Novedades por Máquina")
            for maq in maquinas_seleccionadas:
                with st.expander(f"🟢 Máquina **{maq}**", expanded=True):
                    col1, col2, col3 = st.columns([1, 2, 2])
                    
                    with col1:
                        presion = st.text_input(f"Presión de Cierre ({maq}):", value="N/A", key=f"pres_{maq}")
                    
                    with col2:
                        obs_opcion = st.selectbox(
                            f"Novedad Principal ({maq}):",
                            options=OPCIONES_NOVEDADES,
                            key=f"obs_sel_{maq}"
                        )
                    
                    with col3:
                        obs_detalle = st.text_input(
                            f"Detalle adicional (opcional) ({maq}):",
                            placeholder="Ej. Se corrige fuga en manguera de 1/2\"",
                            key=f"obs_txt_{maq}"
                        )

                    if obs_detalle.strip():
                        observacion_final = f"{obs_opcion} - {obs_detalle.strip()}"
                    else:
                        observacion_final = obs_opcion

                    datos_maquinas.append({
                        "maquina": maq,
                        "presion": presion,
                        "observaciones": observacion_final
                    })

        st.markdown("---")

        if st.button("🚀 Generar Tabla de Reporte"):
            if not uploaded_file:
                st.warning("⚠️ Asegúrate de subir la imagen de Elemental Pro.")
            elif not maquinas_seleccionadas:
                st.warning("⚠️ Por favor selecciona o detecta al menos una máquina.")
            else:
                with st.spinner("Procesando datos y construyendo el reporte oficial FR-PRO-12..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        image_bytes = uploaded_file.getvalue()
                        image_part = types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=uploaded_file.type,
                        )

                        maquinas_info_prompt = json.dumps(datos_maquinas, ensure_ascii=False)

                        prompt = f"""
                        Actúa como un asistente de producción industrial. Extrae de la imagen suministrada (de Elemental Pro) los datos correspondientes a cada máquina.

                        Aquí tienes la lista de máquinas a procesar con sus observaciones y presiones ingresadas por el usuario:
                        {maquinas_info_prompt}

                        Genera una lista formateada exclusivamente en JSON válido (sin marcas markdown como ```json) para construir una tabla.

                        Para cada elemento del listado de máquinas suministrado arriba, crea un objeto JSON con estas llaves exactas:
                        - "Responsable": "{responsable}"
                        - "Turno": "{turno}"
                        - "Fecha": "{fecha_str}"
                        - "Máquina": (El nombre de la máquina entregado)
                        - "Presión de cierre": (La presión entregada para esa máquina)
                        - "Código Artículo": (Extraído de la imagen para esa máquina específica)
                        - "Código Mold": (Extraído de la imagen para esa máquina o N/A)
                        - "Referencia": (Nombre completo del producto extraído de la imagen para esa máquina)
                        - "Observaciones": (La observación entregada para esa máquina)
                        """

                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=[prompt, image_part]
                        )
                        
                        raw_text = response.text.strip()
                        if "```" in raw_text:
                            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                        
                        data_json = json.loads(raw_text)
                        df = pd.DataFrame(data_json)

                        columnas_orden = ["Responsable", "Turno", "Fecha", "Máquina", "Presión de cierre", "Código Artículo", "Código Mold", "Referencia", "Observaciones"]
                        df = df[[c for c in columnas_orden if c in df.columns]]

                        img_path = generar_imagen_reporte_oficial(df, responsable, fecha_str, turno)
                        guardar_en_historial(fecha_str, turno, responsable, json.dumps(data_json))

                        st.success("¡Reporte generado correctamente!")
                        st.markdown("---")

                        st.subheader("🖼 Imagen del Reporte (Lista para WhatsApp)")
                        st.image(img_path, use_container_width=True)

                        with open(img_path, "rb") as file:
                            st.download_button(
                                label="📥 Descargar Imagen del Reporte (PNG)",
                                data=file,
                                file_name=f"Reporte_Turno_{fecha_str.replace('/', '-')}_T{turno}.png",
                                mime="image/png"
                            )

                    except Exception as e:
                        st.error(f"Ocurrió un error al procesar el reporte: {e}")

with tab2:
    st.header("📜 Historial de Reportes Guardados")
    if os.path.exists(HISTORIAL_FILE):
        try:
            df_historial = pd.read_csv(HISTORIAL_FILE)
            for i, row in df_historial.iloc[::-1].iterrows():
                with st.expander(f"📌 Reporte: {row['Fecha Reporte']} | Turno {row['Turno']} - {row['Responsable']} ({row['Fecha y Hora Registro']})"):
                    st.write(row['Reporte Generado'])
        except Exception as e:
            st.error(f"Error al leer el historial: {e}")
    else:
        st.info("Aún no se han guardado reportes en el historial.")

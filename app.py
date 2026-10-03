def texto_a_imagen(texto_markdown):
    """Convierte el reporte Markdown en una imagen limpia para compartir."""
    ancho = 800
    color_fondo = (255, 255, 255) # Fondo blanco
    color_texto = (0, 0, 0)       # Texto negro
    margen = 40
    
    # Cargar fuente predeterminada
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
        font_bold = font

    # Imagen temporal para calcular dimensiones
    img_temp = Image.new('RGB', (ancho, 100), color_fondo)
    draw_temp = ImageDraw.Draw(img_temp)
    
    lineas = texto_markdown.split('\n')
    y_text = margen
    lineas_procesadas = []

    for linea in lineas:
        es_negrita = linea.startswith('**') or linea.startswith('📌') or linea.startswith('📊') or linea.startswith('⚠️') or linea.startswith('🚨')
        fuente_usar = font_bold if es_negrita else font
        linea_limpia = linea.replace('**', '')
        
        # Ajuste de texto al ancho de la imagen
        palabras = linea_limpia.split(' ')
        linea_actual = ''
        for palabra in palabras:
            test_linea = linea_actual + palabra + ' '
            # Usar textbbox en lugar de textsize
            bbox = draw_temp.textbbox((0, 0), test_linea, font=fuente_usar)
            w = bbox[2] - bbox[0]
            if w < (ancho - 2 * margen):
                linea_actual = test_linea
            else:
                lineas_procesadas.append((linea_actual, fuente_usar))
                linea_actual = palabra + ' '
        lineas_procesadas.append((linea_actual, fuente_usar))

    # Calcular alto total dinámicamente
    alto_linea = 28
    alto_final = (len(lineas_procesadas) * alto_linea) + (2 * margen)
    
    # Crear imagen final
    img_final = Image.new('RGB', (ancho, alto_final), color_fondo)
    draw = ImageDraw.Draw(img_final)
    
    y = margen
    for text_line, fnt in lineas_procesadas:
        draw.text((margen, y), text_line, font=fnt, fill=color_texto)
        y += alto_linea
        
    img_bytes = io.BytesIO()
    img_final.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

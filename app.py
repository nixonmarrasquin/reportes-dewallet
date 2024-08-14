import easyocr
import re
from datetime import datetime, timedelta
import os
import cv2
import numpy as np

def es_posible_factura(texto):
    palabras_clave = ['factura', 'dirección', 'nombre', 'apellido', 'ruc', 'telefono', 
                      'vendedor', 'clave de acceso', 'total', 'precio', 'subtotal']
    texto_completo = ' '.join(texto).lower()
    return any(palabra in texto_completo for palabra in palabras_clave)

def obtener_fecha(texto):
    patron_fecha = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
    fechas = [fecha for palabra in texto for fecha in re.findall(patron_fecha, palabra)]
    return fechas[0] if fechas else None

def fecha_valida(fecha_str):
    formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']
    for formato in formatos:
        try:
            fecha = datetime.strptime(fecha_str, formato)
            hoy = datetime.now()
            un_anio_atras = hoy - timedelta(days=365)
            return un_anio_atras <= fecha <= hoy
        except ValueError:
            continue
    return False

def mejorar_imagen(ruta_imagen):
    img = cv2.imread(ruta_imagen)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray)
    thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh

def procesar_imagen(ruta_imagen):
    reader = easyocr.Reader(['es'])
    
    # Intento inicial con la imagen original
    resultado = reader.readtext(ruta_imagen)
    texto = [r[1] for r in resultado]
    
    es_posible_factura_bool = es_posible_factura(texto)
    fecha = obtener_fecha(texto)
    
    # Si no se encuentra fecha, intentar con la imagen mejorada
    if not fecha:
        imagen_mejorada = mejorar_imagen(ruta_imagen)
        resultado_mejorado = reader.readtext(imagen_mejorada)
        texto_mejorado = [r[1] for r in resultado_mejorado]
        fecha = obtener_fecha(texto_mejorado)
        if fecha:
            texto = texto_mejorado  # Actualizar el texto si se encontró una fecha en la imagen mejorada
    
    fecha_valida_bool = fecha_valida(fecha) if fecha else False
    
    return {
        'es_posible_factura': es_posible_factura_bool,
        'fecha': fecha,
        'fecha_valida': fecha_valida_bool,
        'texto_detectado': texto
    }

def main(carpeta):
    imagenes_invalidas = []
    extensiones_validas = ('.jpg', '.jpeg', '.png')

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(extensiones_validas):
            ruta_completa = os.path.join(carpeta, archivo)
            print(f"\nProcesando imagen: {ruta_completa}")
            resultado = procesar_imagen(ruta_completa)
            
            print(f"Posible factura: {resultado['es_posible_factura']}")
            print(f"Fecha detectada: {resultado['fecha']}")
            print(f"Fecha válida: {resultado['fecha_valida']}")
            print(f"Texto detectado: {resultado['texto_detectado'][:5]}...")  # Muestra los primeros 5 elementos
            
            if not (resultado['es_posible_factura'] and resultado['fecha_valida']):
                imagenes_invalidas.append({
                    'ruta': ruta_completa,
                    'razon': ([] if resultado['es_posible_factura'] else ['No parece ser una factura']) + 
                             ([] if resultado['fecha'] else ['No se detectó fecha']) +
                             ([] if resultado['fecha_valida'] else ['Fecha inválida'])
                })
            
            print("--------------------")

    if imagenes_invalidas:
        print("\nImágenes que no cumplen los criterios:")
        for img in imagenes_invalidas:
            print(f"Ruta: {img['ruta']}")
            print(f"Razón: {', '.join(img['razon'])}")
        
        with open('imagenes_no_facturas.txt', 'w', encoding='utf-8') as f:
            f.write("Imágenes que no son facturas válidas:\n\n")
            for img in imagenes_invalidas:
                f.write(f"Ruta: {img['ruta']}\n")
                f.write(f"Razón: {', '.join(img['razon'])}\n\n")
        print("\nLos resultados se han guardado en 'imagenes_no_facturas.txt'")
    else:
        print("\nTodas las imágenes cumplen los criterios.")
        with open('imagenes_no_facturas.txt', 'w', encoding='utf-8') as f:
            f.write("Todas las imágenes son facturas válidas.\n")
        print("Se ha creado un archivo 'imagenes_no_facturas.txt' indicando que todas las imágenes son válidas.")

# Ejemplo de uso
carpeta_imagenes = 'C:\\Users\\Administrador\\Desktop\\facturas-dewallet'
main(carpeta_imagenes)
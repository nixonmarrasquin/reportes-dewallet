import pytesseract
from PIL import Image
import cv2
import re
from datetime import datetime, timedelta
import os
import requests
from io import BytesIO
import pyodbc

# Configuración de la ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuración de la conexión a la base de datos
def obtener_conexion():
    try:
        conexion = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=172.25.2.45;'  # Cambia esto por la IP o nombre de tu servidor
            'DATABASE=appmovil;'  # Nombre de tu base de datos
            'UID=sa;'  # Usuario
            'PWD=Sa21'  # Contraseña
        )
        print('Conectado a la base de datos')
        return conexion
    except pyodbc.Error as e:
        print(f'Error al conectar a la base de datos: {e}')
        return None

# Función para guardar los datos en la base de datos
def guardar_datos_en_bd(resultado, razon, estado, texto_detectado):
    conexion = obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            query = '''
            INSERT INTO ValidacionImagenesFactura (idImagen, codigo_identificador, observaciones, estado, fechaRegistro, textoEncontrado)
            VALUES (?, ?, ?, ?, ?, ?)
            '''
            texto_truncado = texto_detectado[:490]  # Truncar el texto a 490 caracteres
            datos = (
                None,                             # idImagen (puede ser NULL o un valor si lo tienes disponible)
                '100',                            # codigo_identificador (valor por defecto 100)
                razon,                            # observaciones (razón de la imagen)
                estado,                           # estado (valor dinámico)
                datetime.now(),                   # fechaRegistro (fecha y hora actuales)
                texto_truncado                    # textoEncontrado (primeros 490 caracteres)
            )
            cursor.execute(query, datos)
            conexion.commit()
            print('Datos guardados en la base de datos')
        except pyodbc.Error as e:
            print(f'Error al guardar datos: {e}')
        finally:
            cursor.close()
            conexion.close()


def es_posible_factura(texto):
    palabras_clave = ['factura', 'ambiente:', 'dirección', 'direccion', 'telefono', 'nombre', 'apellido', 'ruc', 'teléfono', 
                      'correo', 'email', 'vendedor', 'fecha', 'clave de acceso', 'total', 'precio', 'subtotal', 
                      'orden', 'producción', 'numero de autorizacion']
    
    texto_completo = ' '.join(texto).lower()  # Convertir texto completo a minúsculas
    
    for palabra_clave in palabras_clave:
        if palabra_clave.lower() in texto_completo:
            return True
    
    return False

def obtener_fecha(texto):
    patron_fecha = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'  # Formatos como 25-03-2024
    patron_fecha += r'| \b\d{4}[A-Z]{3}\d{2}\b'  # Formato como 2024MAR25
    patron_fecha += r'| \b\d{2}[/-]\d{2}[/-]\d{4}\b'  # Formatos como 03/25/2024 o 03-25-2024
    patron_fecha += r'| \b\d{2}[/-]\d{2}[/-]\d{2}\b'  # Formatos como 03/25/24 o 03-25-24
    patron_fecha += r'|\b\d{1,2}\s+(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\.?\s*/?\s*\d{2,4}\b'  # Nuevo patrón para "20 jul. /2024"

    fechas = [fecha for palabra in texto for fecha in re.findall(patron_fecha, palabra)]
    return fechas[0] if fechas else None

def fecha_valida(fecha_str):
    formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']
    for formato in formatos:
        try:
            fecha = datetime.strptime(fecha_str.strip(), formato)
            hoy = datetime.now()
            tres_meses_atras = hoy - timedelta(days=1*30)  # 3 meses en días
            return tres_meses_atras <= fecha <= hoy
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
    # Intento inicial con la imagen original
    img = Image.open(ruta_imagen)
    texto = pytesseract.image_to_string(img, lang='spa').split('\n')
    
    es_posible_factura_bool = es_posible_factura(texto)
    fecha = obtener_fecha(texto)
    
    # Si no se encuentra fecha, intentar con la imagen mejorada
    if not fecha:
        imagen_mejorada = mejorar_imagen(ruta_imagen)
        texto_mejorado = pytesseract.image_to_string(imagen_mejorada, lang='spa').split('\n')
        es_posible_factura_bool = es_posible_factura(texto_mejorado)
        fecha = obtener_fecha(texto_mejorado)
        texto_detectado = texto_mejorado[:5000]  # Actualizar el texto si se encontró una fecha en la imagen mejorada
    else:
        texto_detectado = texto[:5000]  # Captura el texto detectado para mostrar luego       
    fecha_valida_bool = fecha_valida(fecha) if fecha else False
    
    return {
        'texto_detectado': texto_detectado,
        'es_posible_factura': es_posible_factura_bool,
        'fecha': fecha,
        'fecha_valida': fecha_valida_bool,
    }

def descargar_imagen(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

def main(url):
    print(f"\nProcesando imagen desde URL: {url}")
    img = descargar_imagen(url)

    img_path = 'temp_image.png'
    img.save(img_path)  # Guardar la imagen temporalmente para procesar con OpenCV
    
    resultado = procesar_imagen(img_path)
    
    texto_detectado = ' '.join(resultado['texto_detectado'])  # Unir el texto en una sola cadena
    fecha = resultado['fecha']
    fecha_valida = resultado['fecha_valida']
    
    print(f"Texto detectado (primeros 100 caracteres): {texto_detectado[:5000]}...")
    print(f"Posible factura: {resultado['es_posible_factura']}")
    print(f"Fecha detectada: {fecha}")
    print(f"Fecha válida: {fecha_valida}")
    
# Lógica corregida para determinar el estado
    if resultado['es_posible_factura'] and fecha and fecha_valida:
        estado = 1  # Cumple todos los criterios
    elif fecha and not fecha_valida:
        estado = 3  # Se detecta fecha pero no es válida
    elif texto_detectado and not resultado['es_posible_factura']:
        estado = 2  # Se detecta texto, pero no parece factura
    elif not texto_detectado:
        estado = 0  # No se detecta texto en absoluto
    else:
        estado = 0  # Otros casos



    print(f"Estado determinado: {estado}")
    
# Lógica mejorada para generar la razón
    if estado == 1:
        razon_str = 'La imagen cumple los criterios.'
    else:
        razones = []
        if estado == 3:
            razones.append('Fecha inválida')
        elif estado == 2:
            razones.append('No parece ser una factura')
        elif estado == 0:
            if not texto_detectado:
                razones.append('No se detectó texto')
            else:
                razones.append('No cumple los criterios de factura')
        
        if not fecha and estado != 2:  # Añadimos esta razón solo si no hay fecha y no es el caso de "No parece ser una factura"
            razones.append('No se detectó fecha')
        
        razon_str = ', '.join(razones)

    print(f"\nRazón: {razon_str}")
    
    # Guardar los datos en la base de datos con el estado determinado y el texto detectado
    guardar_datos_en_bd(resultado, razon_str, estado, texto_detectado)
    
    # Eliminar la imagen temporal después de procesar
    os.remove(img_path)
    print("--------------------")

# Ejemplo de uso
url_imagen = 'http://3.139.221.163/images/facturas/1713831681_2024-07-01%2012:51:46.png'
main(url_imagen)
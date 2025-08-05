"""
EXIF Geo-Metadata Extractor & Mapper
------------------------------------
Script que extrae metadatos EXIF de imágenes (JPG/PNG), genera un reporte CSV con la información
y crea un mapa interactivo HTML con las ubicaciones geográficas encontradas.

Funcionalidades principales:
1. Extracción de metadatos EXIF (incluyendo coordenadas GPS)
2. Conversión de coordenadas GPS a formato decimal
3. Generación de archivo CSV con metadatos
4. Creación de mapa interactivo con marcadores en cada ubicación

Notas importantes:
- El CSV se genera en la carpeta padre del directorio de imágenes
- El HTML del mapa se guarda en el directorio de imágenes analizadas
- Requiere instalación previa de: Pillow, gmplot, pandas
"""

import os
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
import gmplot
import csv

# Configuración global
CSV_FILENAME = "metadata_report.csv"
MAP_FILENAME = "mapa_ubicaciones.html"

def convert_decimal_degrees(degree, minutes, seconds, direction):
    """
    Convierte coordenadas GPS en formato grados/minutos/segundos a grados decimales.
    
    Args:
        degree (float): Grados
        minutes (float): Minutos
        seconds (float): Segundos
        direction (str): Dirección (N/S/E/W)
    
    Returns:
        float: Coordenada convertida a grados decimales
    """
    decimal_degrees = degree + minutes / 60 + seconds / 3600
    if direction in ["S", "W"]:
        decimal_degrees *= -1
    return decimal_degrees


def google_maps(gps_coords, coord_collection):
    """
    Genera un mapa HTML con marcadores en las ubicaciones GPS y devuelve enlace de Google Maps.
    
    Args:
        gps_coords (dict): Diccionario con coordenadas GPS
        coord_collection (dict): Colección acumulativa de coordenadas para mapear
    
    Returns:
        str: Enlace de Google Maps para la última ubicación procesada
    """
    # Conversión a grados decimales
    dec_deg_lat = convert_decimal_degrees(
        float(gps_coords["lat"][0]), 
        float(gps_coords["lat"][1]), 
        float(gps_coords["lat"][2]), 
        gps_coords["lat_ref"]
    )
    
    dec_deg_lon = convert_decimal_degrees(
        float(gps_coords["lon"][0]), 
        float(gps_coords["lon"][1]), 
        float(gps_coords["lon"][2]), 
        gps_coords["lon_ref"]
    )
    
    # Actualiza colección de coordenadas
    coord_collection[dec_deg_lat] = dec_deg_lon
    
    # Crea mapa centrado en la primera coordenada
    if coord_collection:
        first_lat, first_lon = next(iter(coord_collection.items()))
        mapa = gmplot.GoogleMapPlotter(first_lat, first_lon, 12)
        
        # Añade marcadores para todas las coordenadas
        for latitud, longitud in coord_collection.items():
            mapa.marker(latitud, longitud, color="#FF0000")
        
        # Guarda el mapa como HTML
        mapa.draw(MAP_FILENAME)
    
    return f"https://maps.google.com/?q={dec_deg_lat},{dec_deg_lon}"


def extract_metadata():
    """
    Función principal que maneja:
    - Entrada de directorio
    - Procesamiento de imágenes
    - Extracción de metadatos
    - Generación de CSV
    - Creación de mapa
    """
    coord_collection = {}
    ruta = input("Ingresa la ruta de la carpeta que deseas analizar: ")
    
    if not os.path.exists(ruta):
        print("Error: La ruta especificada no existe")
        return
    
    os.chdir(ruta)
    files = os.listdir()
    
    if not files:
        print('No se encontraron archivos en la carpeta')
        return
    
    # CSV se guardará en el directorio padre (como menciona la nota)
    csv_path = os.path.join('..', CSV_FILENAME)
    
    with open(csv_path, "w", newline="", encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Metadata Tag", "Value", "Filename"])  # Encabezados
        
        for file in files:
            try:
                # Verifica si es imagen
                if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                    
                with Image.open(file) as image:
                    print(f"Procesando: {file}...")
                    gps_coords = {}
                    
                    if not image._getexif():
                        writer.writerow(["NO EXIF DATA", "", file])
                        continue
                        
                    for tag, value in image._getexif().items():
                        tag_name = TAGS.get(tag, tag)
                        
                        if tag_name == "GPSInfo":
                            for key, val in value.items():
                                gps_tag = GPSTAGS.get(key, key)
                                
                                # Almacena coordenadas para procesamiento posterior
                                if gps_tag == "GPSLatitude":
                                    gps_coords["lat"] = val
                                elif gps_tag == "GPSLongitude":
                                    gps_coords["lon"] = val
                                elif gps_tag == "GPSLatitudeRef":
                                    gps_coords["lat_ref"] = val
                                elif gps_tag == "GPSLongitudeRef":
                                    gps_coords["lon_ref"] = val
                                
                                writer.writerow([gps_tag, val, file])
                        else:
                            writer.writerow([tag_name, value, file])
                    
                    # Procesar coordenadas si existen
                    if gps_coords and all(k in gps_coords for k in ["lat", "lon", "lat_ref", "lon_ref"]):
                        maps_link = google_maps(gps_coords, coord_collection)
                        writer.writerow(["Google Maps Link", maps_link, file])
            
            except (IOError, OSError) as e:
                print(f"Error procesando {file}: {str(e)}")
    
    print("\nProceso completado:")
    print(f"- Reporte CSV generado en: {csv_path}")
    print(f"- Mapa interactivo generado en: {os.path.join(ruta, MAP_FILENAME)}")


if __name__ == "__main__":
    extract_metadata()

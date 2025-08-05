"""
EXIF Geo-Metadata Extractor & Mapper 
-----------------------------------------
Script que extrae metadatos EXIF de imágenes (JPG/PNG), genera reportes en múltiples formatos
y crea mapas interactivos con análisis de riesgos de seguridad.
 
 Funcionalidades:
1. Interfaz CLI profesional con argparse
2. Exportación a múltiples formatos (CSV, JSON, TXT)
3. Análisis de riesgos de seguridad
4. Detección avanzada de coordenadas GPS
5. Soporte para análisis de directorios completos
6. Módulo de saneamiento de metadatos
"""

import os
import argparse
import json
from datetime import datetime
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
import gmplot
import csv

# Configuración global
CSV_FILENAME = "metadata_report.csv"
JSON_FILENAME = "metadata_report.json"
TXT_FILENAME = "security_analysis.txt"
MAP_FILENAME = "mapa_ubicaciones.html"

# Configuración de riesgo
RISK_KEYWORDS = ['GPS', 'Location', 'Position', 'Address', 'Copyright', 'Author', 'Artist']
HIGH_RISK_TAGS = ['GPSLatitude', 'GPSLongitude', 'Copyright', 'Author', 'Artist']

def convert_decimal_degrees(degree, minutes, seconds, direction):
    """Convierte coordenadas GPS a grados decimales con precisión mejorada"""
    try:
        decimal_degrees = degree + minutes / 60 + seconds / 3600
        if direction in ["S", "W"]:
            decimal_degrees *= -1
        return round(decimal_degrees, 6)  # Precisión de 6 decimales
    except (TypeError, ValueError):
        return None

def detect_gps_location(gps_info):
    """Detección avanzada de coordenadas GPS con validación"""
    gps_coords = {}
    
    try:
        # Extracción de latitud
        if 1 in gps_info and 2 in gps_info and 3 in gps_info:
            gps_coords["lat"] = gps_info[2]
            gps_coords["lat_ref"] = gps_info[1]
        
        # Extracción de longitud
        if 4 in gps_info and 3 in gps_info:
            gps_coords["lon"] = gps_info[4]
            gps_coords["lon_ref"] = gps_info[3]
        
        # Validación básica de coordenadas
        if not all(k in gps_coords for k in ["lat", "lon", "lat_ref", "lon_ref"]):
            return None
            
        return gps_coords
    except (KeyError, TypeError):
        return None

def analyze_security_risk(metadata, filename):
    """Analiza riesgos de seguridad en los metadatos"""
    risk_report = {
        'filename': filename,
        'high_risk_items': [],
        'medium_risk_items': [],
        'recommendations': []
    }
    
    # Detección de información de alta sensibilidad
    for tag, value in metadata.items():
        if tag in HIGH_RISK_TAGS:
            risk_report['high_risk_items'].append({
                'tag': tag,
                'value': value,
                'risk': 'ALTO: Información de ubicación o propiedad expuesta'
            })
        elif any(kw in tag for kw in RISK_KEYWORDS):
            risk_report['medium_risk_items'].append({
                'tag': tag,
                'value': value,
                'risk': 'MEDIO: Información potencialmente sensible'
            })
    
    # Recomendaciones basadas en hallazgos
    if risk_report['high_risk_items']:
        risk_report['recommendations'].append(
            "Eliminar metadatos GPS antes de compartir esta imagen"
        )
    
    if risk_report['medium_risk_items']:
        risk_report['recommendations'].append(
            "Revisar y eliminar metadatos personales o sensibles"
        )
    
    if not risk_report['high_risk_items'] and not risk_report['medium_risk_items']:
        risk_report['recommendations'].append(
            "No se detectaron riesgos de seguridad significativos"
        )
    
    return risk_report

def sanitize_metadata(image):
    """Elimina metadatos sensibles manteniendo información técnica básica"""
    # Conservar solo estos tags "seguros"
    SAFE_TAGS = ['DateTime', 'ImageWidth', 'ImageLength', 'Make', 'Model', 'Software']
    
    exif_data = image.getexif() or {}
    new_exif = {}
    
    # Copiar solo los metadatos considerados seguros
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name in SAFE_TAGS:
            new_exif[tag_id] = value
    
    # Eliminar completamente los datos GPS
    if 34853 in new_exif:  # GPSInfo tag ID
        del new_exif[34853]
    
    return new_exif

def export_report(data, format, output_dir):
    """Exporta el reporte en diferentes formatos"""
    if format == 'csv':
        csv_path = os.path.join(output_dir, CSV_FILENAME)
        with open(csv_path, "w", newline="", encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Filename", "Metadata Tag", "Value"])
            for entry in data:
                writer.writerow([entry['filename'], entry['tag'], entry['value']])
        return csv_path
    
    elif format == 'json':
        json_path = os.path.join(output_dir, JSON_FILENAME)
        with open(json_path, "w", encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)
        return json_path
    
    elif format == 'txt':
        txt_path = os.path.join(output_dir, TXT_FILENAME)
        with open(txt_path, "w", encoding='utf-8') as txt_file:
            for entry in data:
                txt_file.write(f"Archivo: {entry['filename']}\n")
                txt_file.write(f"Tag: {entry['tag']}\n")
                txt_file.write(f"Valor: {entry['value']}\n")
                txt_file.write("-" * 50 + "\n")
        return txt_path
    
    return None

def generate_map(gps_data, output_dir):
    """Genera mapa interactivo con marcadores de ubicaciones"""
    if not gps_data:
        return None
    
    # Centro del mapa en el primer punto
    first_point = next(iter(gps_data.values()))
    gmap = gmplot.GoogleMapPlotter(first_point[0], first_point[1], 10)
    
    # Añadir marcadores
    for filename, (lat, lng) in gps_data.items():
        gmap.marker(lat, lng, title=filename)
    
    map_path = os.path.join(output_dir, MAP_FILENAME)
    gmap.draw(map_path)
    return map_path

def process_image(file_path, sanitize=False, risk_analysis=False):
    """Procesa una imagen individual y extrae sus metadatos"""
    results = []
    security_report = None
    gps_coords = None
    
    try:
        with Image.open(file_path) as img:
            filename = os.path.basename(file_path)
            exif_data = img._getexif() or {}
            
            # Opción de saneamiento
            if sanitize:
                new_exif = sanitize_metadata(img)
                img.save(file_path, exif=bytes(new_exif))
                exif_data = new_exif
            
            # Procesar metadatos
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                
                # Procesamiento especial para GPS
                if tag_name == "GPSInfo":
                    gps_data = detect_gps_location(value)
                    if gps_data:
                        dec_lat = convert_decimal_degrees(
                            float(gps_data["lat"][0]), 
                            float(gps_data["lat"][1]), 
                            float(gps_data["lat"][2]), 
                            gps_data["lat_ref"]
                        )
                        dec_lon = convert_decimal_degrees(
                            float(gps_data["lon"][0]), 
                            float(gps_data["lon"][1]), 
                            float(gps_data["lon"][2]), 
                            gps_data["lon_ref"]
                        )
                        
                        if dec_lat and dec_lon:
                            gps_coords = (dec_lat, dec_lon)
                            results.append({
                                'filename': filename,
                                'tag': 'GPSDecimal',
                                'value': f"{dec_lat}, {dec_lon}"
                            })
                            results.append({
                                'filename': filename,
                                'tag': 'GoogleMaps',
                                'value': f"https://maps.google.com/?q={dec_lat},{dec_lon}"
                            })
                
                # Almacenar todos los metadatos
                results.append({
                    'filename': filename,
                    'tag': tag_name,
                    'value': str(value)
                })
            
            # Análisis de riesgo si se solicita
            if risk_analysis:
                security_report = analyze_security_risk(
                    {TAGS.get(tag_id, tag_id): value for tag_id, value in exif_data.items()},
                    filename
                )
    
    except (IOError, OSError, ValueError) as e:
        print(f"Error procesando {file_path}: {str(e)}")
        results.append({
            'filename': os.path.basename(file_path),
            'tag': 'Error',
            'value': str(e)
        })
    
    return {
        'metadata': results,
        'gps': gps_coords,
        'security_report': security_report
    }

def process_directory(path, sanitize=False, risk_analysis=False, output_format='csv'):
    """Procesa un directorio completo de imágenes"""
    if not os.path.exists(path):
        print("Error: La ruta especificada no existe")
        return None, None, []
    
    all_metadata = []
    all_gps = {}
    security_reports = []
    processed_count = 0
    
    for root, _, files in os.walk(path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(root, file)
                result = process_image(file_path, sanitize, risk_analysis)
                
                if result['metadata']:
                    all_metadata.extend(result['metadata'])
                
                if result['gps']:
                    all_gps[file] = result['gps']
                
                if result['security_report']:
                    security_reports.append(result['security_report'])
                
                processed_count += 1
    
    # Exportar resultados
    report_path = export_report(all_metadata, output_format, path) if all_metadata else None
    
    # Generar mapa si hay coordenadas GPS
    map_path = generate_map(all_gps, path) if all_gps else None
    
    # Exportar reportes de seguridad si existen
    security_report_path = None
    if security_reports:
        security_report_path = os.path.join(path, "security_analysis.json")
        with open(security_report_path, "w", encoding="utf-8") as f:
            json.dump(security_reports, f, indent=4)
    
    return report_path, map_path, security_report_path, processed_count

def main():
    """Función principal con interfaz CLI mejorada"""
    parser = argparse.ArgumentParser(
        description='EXIF Geo-Metadata Extractor & Mapper Plus - Herramienta avanzada de análisis de metadatos',
        epilog='Ejemplos de uso:\n'
               '  python metadata_tool.py /ruta/a/imagenes\n'
               '  python metadata_tool.py /ruta/a/imagenes --sanitize --format json\n'
               '  python metadata_tool.py /ruta/a/imagenes --risk --format all'
    )
    parser.add_argument('path', help='Ruta al archivo o directorio de imágenes')
    parser.add_argument('--sanitize', action='store_true', help='Elimina metadatos sensibles de las imágenes')
    parser.add_argument('--risk', action='store_true', help='Genera reporte de análisis de riesgos')
    parser.add_argument('--format', choices=['csv', 'json', 'txt', 'all'], default='csv',
                        help='Formato de salida para el reporte (default: csv)')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    print(f"\n{'='*50}")
    print("EXIF Geo-Metadata Extractor & Mapper Plus")
    print(f"{'='*50}\n")
    
    # Determinar si es archivo o directorio
    if os.path.isfile(args.path):
        # Procesamiento de archivo individual
        result = process_image(args.path, args.sanitize, args.risk)
        
        if result['metadata']:
            # Crear directorio para reportes
            report_dir = os.path.join(os.path.dirname(args.path), "metadata_reports")
            os.makedirs(report_dir, exist_ok=True)
            
            # Exportar reporte
            export_format = 'csv' if args.format == 'all' else args.format
            report_path = export_report(result['metadata'], export_format, report_dir)
            
            print(f"\nProcesamiento completado para: {os.path.basename(args.path)}")
            if report_path:
                print(f"- Reporte generado en: {report_path}")
            
            if result['security_report']:
                security_path = os.path.join(report_dir, "security_analysis.json")
                with open(security_path, "w", encoding="utf-8") as f:
                    json.dump([result['security_report']], f, indent=4)
                print(f"- Reporte de seguridad en: {security_path}")
        else:
            print("No se encontraron metadatos en la imagen")
    else:
        # Procesamiento de directorio
        report_path, map_path, security_path, count = process_directory(
            args.path, args.sanitize, args.risk, args.format
        )
        
        print(f"\nProcesamiento completado:")
        print(f"- Imágenes procesadas: {count}")
        
        if args.format == 'all':
            print(f"- Reporte CSV generado en: {os.path.join(args.path, CSV_FILENAME)}")
            print(f"- Reporte JSON generado en: {os.path.join(args.path, JSON_FILENAME)}")
            print(f"- Reporte TXT generado en: {os.path.join(args.path, TXT_FILENAME)}")
        elif report_path:
            print(f"- Reporte generado en: {report_path}")
        
        if map_path:
            print(f"- Mapa interactivo generado en: {map_path}")
        
        if security_path:
            print(f"- Reporte de seguridad en: {security_path}")
    
    elapsed = datetime.now() - start_time
    print(f"\nTiempo total de ejecución: {elapsed.total_seconds():.2f} segundos")
    print(f"{'='*50}")

if _name_ == "_main_":
    main()

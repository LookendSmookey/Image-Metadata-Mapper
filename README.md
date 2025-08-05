# Image Metadata Mapper - Analizador de Metadatos EXIF

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Security](https://img.shields.io/badge/Security-Expert-blue?style=for-the-badge)

Herramienta forense para analizar y visualizar metadatos ocultos en imágenes, revelando información sensible como ubicaciones GPS, dispositivos utilizados y más. Ideal para pentesters, analistas forenses y auditores de seguridad.

> *Advertencia de Seguridad*: Los metadatos en imágenes pueden exponer información personal crítica. Utilice esta herramienta solo con fines legítimos de seguridad y análisis forense.

## 🔍 ¿Por qué importan los metadatos?

Los metadatos EXIF (Exchangeable Image File Format) contienen información oculta que puede incluir:
- 📍 Coordenadas GPS exactas
- 📅 Fecha y hora de captura
- 📷 Modelo de cámara y configuraciones
- 👤 Información del autor y copyright

Esta información puede ser explotada por atacantes para:
1. Identificar ubicaciones de usuarios
2. Determinar patrones de comportamiento
3. Realizar ingeniería social
4. Comprometer la privacidad personal/organizacional

##  Características Principales

- Extracción completa de metadatos EXIF
- Detección automática de coordenadas GPS
- Análisis de riesgo de información expuesta
- Soporte para múltiples formatos de imagen (JPEG, PNG, TIFF)
- Interfaz de línea de comandos (CLI) fácil de usar
- Exportación de resultados a JSON y CSV

## 🛠 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/LookendSmookey/Image-Metadata-Mapper.git
cd Image-Metadata-Mapper

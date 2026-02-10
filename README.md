# Home Assistant Entity Analyzer

Script en Python diseñado para analizar, clasificar y monitorizar entidades de Home Assistant a través de su API REST.

## 🚀 Características

- **Clasificación Automática**: Detecta y organiza entidades por dominios (luces, sensores, clima, persianans, etc.).
- **Monitor de Grupo Interactivo**: Permite seleccionar entidades específicas para monitorizar en tiempo real.
- **Registro Optimizado**: Guarda cambios de estado en un archivo CSV de forma eficiente (solo cuando ocurre un cambio).
- **Detección de Estancias**: Intenta asignar habitaciones basándose en el nombre de la entidad.

## 📋 Requisitos

- Python 3.9 o superior.
- Una instancia de Home Assistant accesible por red.
- Token de Acceso de Larga Duración (Long-Lived Access Token).

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/leopitrera/ha_knx_datalogger.git
cd ha_knx_datalogger

# Ejecutar el script
python3 ha-knx-datalogger.py
```

## ⚙️ Configuración

Define las variables de entorno necesarias:

```bash
export HA_BASE_URL="http://TU_IP:8123"
export HA_TOKEN="TU_TOKEN"
```

## 📊 Salida

Genera un archivo `entity_analysis.json` con el mapa completo de tu instalación y archivos CSV para las sesiones de monitorización.

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver archivo [LICENSE](LICENSE) para más detalles.

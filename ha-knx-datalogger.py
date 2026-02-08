#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
entity_analyzer.py - Análisis inteligente de entidades de Home Assistant
Características:
- Descarga automática de TODAS las entidades
- Clasificación inteligente por tipo y capacidades
- Detección automática de habitaciones
- Corrección por chat
- ⭐ Monitor de grupo con selección interactiva
- ⭐ Grabación en CSV SOLO cuando cambian valores (optimizado)
- ⭐ Añadir múltiples entidades una por una
- Optimizado para Hailo HAT 2+
"""

import os
import re
import json
import csv
import requests
import time
import threading
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

HA_BASE_URL = os.getenv("HA_BASE_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}


class EntityAnalyzer:
    """Analizador inteligente de entidades"""

    def __init__(self):
        self.entities: List[Dict[str, Any]] = []
        self.analysis: Dict[str, Any] = {}
        self.rooms: Set[str] = set()
        self.corrections: Dict[str, Dict[str, str]] = {}

    def fetch_all_entities(self) -> bool:
        """Descarga TODAS las entidades de Home Assistant"""
        try:
            print("📡 Conectando a Home Assistant...")
            r = requests.get(f"{HA_BASE_URL}/api/states", headers=HEADERS, timeout=10)
            r.raise_for_status()
            self.entities = r.json()
            print(f"✓ {len(self.entities)} entidades descargadas")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def detect_rooms(self) -> Set[str]:
        """Detecta habitaciones automáticamente desde los nombres de entidades"""
        room_keywords = {
            # Español
            "salon": "Salón",
            "salón": "Salón",
            "sala": "Salón",
            "living": "Salón",
            "cocina": "Cocina",
            "kitchen": "Cocina",
            "dormitorio": "Dormitorio",
            "habitacion": "Dormitorio",
            "habitación": "Dormitorio",
            "cuarto": "Dormitorio",
            "bedroom": "Dormitorio",
            "baño": "Baño",
            "bano": "Baño",
            "aseo": "Baño",
            "bathroom": "Baño",
            "pasillo": "Pasillo",
            "corredor": "Pasillo",
            "hall": "Pasillo",
            "entrada": "Entrada",
            "recibidor": "Entrada",
            "garaje": "Garaje",
            "garage": "Garaje",
            "jardin": "Jardín",
            "jardín": "Jardín",
            "exterior": "Exterior",
            "terraza": "Terraza",
            "balcon": "Balcón",
            "balcón": "Balcón",
            "despacho": "Despacho",
            "oficina": "Despacho",
            "estudio": "Despacho",
            "comedor": "Comedor",
            # Específicas
            "principal": "Principal",
            "master": "Principal",
            "niños": "Niños",
            "ninos": "Niños",
            "invitados": "Invitados",
        }

        rooms = set()
        for entity in self.entities:
            entity_id = entity.get("entity_id", "").lower()
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()

            for keyword, room_name in room_keywords.items():
                if keyword in entity_id or keyword in friendly_name:
                    rooms.add(room_name)

        self.rooms = rooms
        return rooms

    def classify_light(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica una luz por sus capacidades"""
        entity_id = entity.get("entity_id")
        attributes = entity.get("attributes", {})
        supported_features = attributes.get("supported_features", 0)

        classification = {
            "entity_id": entity_id,
            "friendly_name": attributes.get("friendly_name", entity_id),
            "type": "switch",
            "capabilities": [],
            "room": self._extract_room(entity),
        }

        if supported_features == 0:
            classification["type"] = "switch"
            classification["capabilities"] = ["on/off"]
        else:
            capabilities = []
            if supported_features & 1:
                classification["type"] = "dimmable"
                capabilities.append("brillo")
            if supported_features & 16:
                classification["type"] = "rgb"
                capabilities.append("color RGB")
            if supported_features & 128:
                if "rgb" not in classification["type"]:
                    classification["type"] = "tunable_white"
                capabilities.append("temperatura color")
            if supported_features & 4:
                capabilities.append("efectos")
            classification["capabilities"] = capabilities if capabilities else ["on/off"]

        return classification

    def classify_sensor(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica un sensor por su tipo"""
        entity_id = entity.get("entity_id")
        attributes = entity.get("attributes", {})
        device_class = attributes.get("device_class", "")
        unit = attributes.get("unit_of_measurement", "")
        state = entity.get("state", "")

        sensor_types = {
            "temperature": "Temperatura",
            "humidity": "Humedad",
            "pressure": "Presión",
            "battery": "Batería",
            "power": "Potencia",
            "energy": "Energía",
            "voltage": "Voltaje",
            "current": "Corriente",
            "illuminance": "Iluminancia",
            "motion": "Movimiento",
            "occupancy": "Ocupación",
            "opening": "Apertura",
            "presence": "Presencia",
            "smoke": "Humo",
            "gas": "Gas",
            "carbon_monoxide": "Monóxido de carbono",
            "moisture": "Humedad/Inundación",
            "pm25": "Partículas PM2.5",
            "pm10": "Partículas PM10",
            "carbon_dioxide": "CO2",
            "volatile_organic_compounds": "VOC",
            "aqi": "Calidad del aire",
        }

        sensor_type = sensor_types.get(device_class, "")

        if not sensor_type:
            if "°C" in unit or "°F" in unit:
                sensor_type = "Temperatura"
            elif "%" in unit:
                sensor_type = "Batería" if "batt" in entity_id.lower() else "Humedad"
            elif "W" in unit or "kW" in unit:
                sensor_type = "Potencia"
            elif "Wh" in unit or "kWh" in unit:
                sensor_type = "Energía"
            elif "lx" in unit:
                sensor_type = "Iluminancia"
            elif "ppm" in unit:
                sensor_type = "CO2"
            else:
                name_lower = entity_id.lower()
                if "temp" in name_lower or "ta_" in name_lower:
                    sensor_type = "Temperatura"
                elif "hum" in name_lower:
                    sensor_type = "Humedad"
                elif "motion" in name_lower or "movimiento" in name_lower:
                    sensor_type = "Movimiento"
                elif "door" in name_lower or "puerta" in name_lower:
                    sensor_type = "Apertura puerta"
                elif "window" in name_lower or "ventana" in name_lower:
                    sensor_type = "Apertura ventana"
                else:
                    sensor_type = "Otro"

        return {
            "entity_id": entity_id,
            "friendly_name": attributes.get("friendly_name", entity_id),
            "type": sensor_type,
            "unit": unit,
            "current_value": state,
            "room": self._extract_room(entity),
        }

    def classify_binary_sensor(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica un sensor binario"""
        entity_id = entity.get("entity_id")
        attributes = entity.get("attributes", {})
        device_class = attributes.get("device_class", "")

        binary_types = {
            "motion": "Movimiento/Presencia",
            "occupancy": "Ocupación",
            "opening": "Apertura (puerta/ventana)",
            "door": "Puerta",
            "window": "Ventana",
            "smoke": "Detector de humo",
            "gas": "Detector de gas",
            "moisture": "Detector de inundación",
            "presence": "Presencia",
            "vibration": "Vibración",
            "sound": "Sonido",
            "battery": "Batería baja",
            "connectivity": "Conectividad",
        }

        sensor_type = binary_types.get(device_class, "")

        if not sensor_type:
            name_lower = entity_id.lower()

            if any(kw in name_lower for kw in ["presencia", "presence", "motion", "movimiento", "deteccion", "detection"]):
                sensor_type = "Movimiento/Presencia"
            elif "pulsador" in name_lower or "puls_" in name_lower or "button" in name_lower:
                sensor_type = "Pulsador/Botón"
            elif "pantalla" in name_lower or "display" in name_lower or "z35" in name_lower:
                sensor_type = "Estado pantalla/display"
            elif "valvula" in name_lower or "valve" in name_lower:
                sensor_type = "Estado válvula"
            elif "inundacion" in name_lower or "flood" in name_lower or "water" in name_lower:
                sensor_type = "Detector de inundación"
            elif "door" in name_lower or "puerta" in name_lower:
                sensor_type = "Apertura puerta"
            elif "window" in name_lower or "ventana" in name_lower:
                sensor_type = "Apertura ventana"
            elif "smoke" in name_lower or "humo" in name_lower:
                sensor_type = "Detector de humo"
            elif "connection" in name_lower or "conectividad" in name_lower or "cloud" in name_lower:
                sensor_type = "Estado conexión"
            elif any(kw in name_lower for kw in ["ipc_", "recording", "relay", "alarm"]):
                sensor_type = "Estado dispositivo"
            elif "overheated" in name_lower or "sobrecalentamiento" in name_lower:
                sensor_type = "Alerta sobrecalentamiento"
            elif any(kw in name_lower for kw in ["kes_", "dalibox", "railquad", "quad_", "siber"]):
                sensor_type = "Estado sistema"
            elif "power" in name_lower or "alimentacion" in name_lower:
                sensor_type = "Estado alimentación"
            elif "remote_ui" in name_lower:
                sensor_type = "Interfaz remota"
            else:
                sensor_type = "Otro"

        return {
            "entity_id": entity_id,
            "friendly_name": attributes.get("friendly_name", entity_id),
            "type": sensor_type,
            "state": entity.get("state"),
            "room": self._extract_room(entity),
        }

    def classify_cover(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica persiana/cortina/estor"""
        entity_id = entity.get("entity_id")
        attributes = entity.get("attributes", {})
        device_class = attributes.get("device_class", "")

        cover_types = {
            "awning": "Toldo",
            "blind": "Persiana",
            "curtain": "Cortina",
            "damper": "Compuerta",
            "door": "Puerta motorizada",
            "garage": "Puerta garaje",
            "gate": "Portón",
            "shade": "Estor",
            "shutter": "Contraventana",
            "window": "Ventana motorizada",
        }

        cover_type = cover_types.get(device_class, "Persiana")

        if device_class == "" or device_class == "None":
            name_lower = entity_id.lower()
            if "estor" in name_lower:
                cover_type = "Estor"
            elif "cortina" in name_lower:
                cover_type = "Cortina"
            elif "toldo" in name_lower:
                cover_type = "Toldo"
            elif "garaje" in name_lower or "garage" in name_lower:
                cover_type = "Puerta garaje"

        return {
            "entity_id": entity_id,
            "friendly_name": attributes.get("friendly_name", entity_id),
            "type": cover_type,
            "room": self._extract_room(entity),
            "position": attributes.get("current_position"),
        }

    def classify_climate(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica sistema de climatización"""
        entity_id = entity.get("entity_id")
        attributes = entity.get("attributes", {})

        return {
            "entity_id": entity_id,
            "friendly_name": attributes.get("friendly_name", entity_id),
            "type": "Climatización",
            "modes": attributes.get("hvac_modes", []),
            "current_temp": attributes.get("current_temperature"),
            "target_temp": attributes.get("temperature"),
            "room": self._extract_room(entity),
        }

    def _extract_room(self, entity: Dict[str, Any]) -> Optional[str]:
        """Extrae la habitación de una entidad"""
        entity_id = entity.get("entity_id", "").lower()
        friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()

        for room in self.rooms:
            if room.lower() in entity_id or room.lower() in friendly_name:
                return room

        return None

    def analyze_all(self) -> Dict[str, Any]:
        """Analiza TODAS las entidades"""
        if not self.entities:
            print("❌ No hay entidades cargadas. Ejecuta fetch_all_entities() primero.")
            return {}

        print("\n🔍 Analizando entidades...")

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_entities": len(self.entities),
            "rooms": [],
            "lights": {
                "switch": [],
                "dimmable": [],
                "rgb": [],
                "tunable_white": [],
            },
            "covers": defaultdict(list),
            "climate": [],
            "sensors": defaultdict(list),
            "binary_sensors": defaultdict(list),
            "switches": [],
            "other": defaultdict(list),
        }

        self.detect_rooms()
        analysis["rooms"] = sorted(list(self.rooms))

        for entity in self.entities:
            entity_id = entity.get("entity_id", "")
            domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

            if domain == "light":
                classified = self.classify_light(entity)
                light_type = classified["type"]
                analysis["lights"][light_type].append(classified)

            elif domain == "sensor":
                classified = self.classify_sensor(entity)
                sensor_type = classified["type"]
                analysis["sensors"][sensor_type].append(classified)

            elif domain == "binary_sensor":
                classified = self.classify_binary_sensor(entity)
                sensor_type = classified["type"]
                analysis["binary_sensors"][sensor_type].append(classified)

            elif domain == "cover":
                classified = self.classify_cover(entity)
                cover_type = classified["type"]
                analysis["covers"][cover_type].append(classified)

            elif domain == "climate":
                classified = self.classify_climate(entity)
                analysis["climate"].append(classified)

            elif domain == "switch":
                analysis["switches"].append({
                    "entity_id": entity_id,
                    "friendly_name": entity.get("attributes", {}).get("friendly_name", entity_id),
                    "room": self._extract_room(entity),
                })

            else:
                analysis["other"][domain].append({
                    "entity_id": entity_id,
                    "friendly_name": entity.get("attributes", {}).get("friendly_name", entity_id),
                })

        self.analysis = analysis
        return analysis

    def print_analysis(self) -> None:
        """Imprime el análisis de forma legible"""
        if not self.analysis:
            print("❌ No hay análisis disponible. Ejecuta analyze_all() primero.")
            return

        print("\n" + "="*70)
        print("📊 ANÁLISIS COMPLETO DE ENTIDADES")
        print("="*70)

        print(f"\n🏠 HABITACIONES DETECTADAS ({len(self.analysis['rooms'])}):")
        for i, room in enumerate(self.analysis['rooms'], 1):
            print(f"  {i}. {room}")

        # Luces
        total_lights = sum(len(lights) for lights in self.analysis['lights'].values())
        print(f"\n💡 LUCES ({total_lights} total):")

        for light_type, lights in self.analysis['lights'].items():
            if lights:
                type_names = {
                    "switch": "Conmutadas (on/off)",
                    "dimmable": "Regulables (brillo)",
                    "rgb": "RGB (color completo)",
                    "tunable_white": "Blanco ajustable",
                }

                print(f"\n  📌 {type_names.get(light_type, light_type)} ({len(lights)}):")
                for light in lights[:10]:
                    room = f" [{light['room']}]" if light['room'] else ""
                    caps = " + ".join(light['capabilities'])
                    print(f"    • {light['friendly_name']}{room} - {caps}")

                if len(lights) > 10:
                    print(f"    ... y {len(lights)-10} más")

        # Persianas/Cortinas
        total_covers = sum(len(covers) for covers in self.analysis['covers'].values())
        if total_covers > 0:
            print(f"\n🪟 PERSIANAS/CORTINAS ({total_covers} total):")
            for cover_type, covers in self.analysis['covers'].items():
                if covers:
                    print(f"\n  📌 {cover_type} ({len(covers)}):")
                    for cover in covers:
                        room = f" [{cover['room']}]" if cover['room'] else ""
                        print(f"    • {cover['friendly_name']}{room}")

        # Climatización
        if self.analysis['climate']:
            print(f"\n🌡️ CLIMATIZACIÓN ({len(self.analysis['climate'])}):")
            for climate in self.analysis['climate']:
                room = f" [{climate['room']}]" if climate['room'] else ""
                modes = ", ".join(climate['modes'])
                temp = f"{climate['current_temp']}°C" if climate['current_temp'] else "N/A"
                print(f"  • {climate['friendly_name']}{room}")
                print(f"    Modos: {modes} | Temp actual: {temp}")

        # Sensores
        total_sensors = sum(len(sensors) for sensors in self.analysis['sensors'].values())
        if total_sensors > 0:
            print(f"\n📡 SENSORES ({total_sensors} total):")
            for sensor_type, sensors in sorted(self.analysis['sensors'].items()):
                if sensors:
                    print(f"\n  📌 {sensor_type} ({len(sensors)}):")
                    for sensor in sensors[:10]:
                        room = f" [{sensor['room']}]" if sensor['room'] else ""
                        value = f"{sensor['current_value']}{sensor['unit']}" if sensor['unit'] else sensor['current_value']
                        print(f"    • {sensor['friendly_name']}{room}: {value}")

                    if len(sensors) > 10:
                        print(f"    ... y {len(sensors)-10} más")

        # Sensores binarios
        total_binary = sum(len(sensors) for sensors in self.analysis['binary_sensors'].values())
        if total_binary > 0:
            print(f"\n🔘 SENSORES BINARIOS ({total_binary} total):")

            for sensor_type, sensors in sorted(self.analysis['binary_sensors'].items()):
                if sensors:
                    print(f"\n  📌 {sensor_type} ({len(sensors)}):")
                    for sensor in sensors[:15]:
                        room = f" [{sensor['room']}]" if sensor['room'] else ""
                        state_icon = "✓" if sensor['state'] in ['on', 'true', 'home'] else "○"
                        print(f"    {state_icon} {sensor['friendly_name']}{room}")

                    if len(sensors) > 15:
                        print(f"    ... y {len(sensors)-15} más")

        # Switches
        if self.analysis['switches']:
            print(f"\n🔌 INTERRUPTORES/ENCHUFES ({len(self.analysis['switches'])}):")
            for switch in self.analysis['switches'][:10]:
                room = f" [{switch['room']}]" if switch['room'] else ""
                print(f"  • {switch['friendly_name']}{room}")

            if len(self.analysis['switches']) > 10:
                print(f"  ... y {len(self.analysis['switches'])-10} más")

        # Otros
        total_other = sum(len(items) for items in self.analysis['other'].values())
        if total_other > 0:
            print(f"\n📦 OTROS DISPOSITIVOS ({total_other}):")
            for domain, items in self.analysis['other'].items():
                print(f"  • {domain}: {len(items)}")

        print("\n" + "="*70)

    def save_analysis(self, filepath: str = "entity_analysis.json") -> bool:
        """Guarda el análisis en un archivo JSON"""
        if not self.analysis:
            print("❌ No hay análisis disponible.")
            return False

        try:
            analysis_copy = json.loads(json.dumps(self.analysis, default=list))

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_copy, f, ensure_ascii=False, indent=2)

            print(f"✓ Análisis guardado en: {filepath}")
            return True

        except Exception as e:
            print(f"❌ Error guardando análisis: {e}")
            return False

    # ⭐ NUEVAS FUNCIONALIDADES: Monitor de Grupo Optimizado

    def list_all_entities_numbered(self) -> List[Dict[str, Any]]:
        """Lista todas las entidades con numeración para selección"""
        if not self.entities:
            print("❌ No hay entidades cargadas.")
            return []

        entity_list = []
        print("\n" + "="*80)
        print("📋 LISTA COMPLETA DE ENTIDADES")
        print("="*80)

        for idx, entity in enumerate(self.entities, 1):
            entity_id = entity.get("entity_id", "")
            domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
            attributes = entity.get("attributes", {})
            friendly_name = attributes.get("friendly_name", entity_id)
            state = entity.get("state", "unknown")

            entity_info = {
                "index": idx,
                "entity_id": entity_id,
                "domain": domain,
                "friendly_name": friendly_name,
                "state": state,
                "attributes": attributes
            }
            entity_list.append(entity_info)

            # Mostrar en consola
            print(f"{idx:4d}. [{domain:15s}] {friendly_name:40s} = {state}")

        print("="*80)
        print(f"Total: {len(entity_list)} entidades\n")

        return entity_list

    def select_entities_interactive(self, entity_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Permite añadir entidades una por una de forma interactiva"""
        print("\n📌 SELECCIÓN INTERACTIVA DE ENTIDADES")
        print("="*80)
        print("Instrucciones:")
        print("  • Escribe 'todos' o 'all' para seleccionar TODAS")
        print("  • Escribe el número de la entidad para añadirla")
        print("  • Escribe rangos: 1-10, 15-20")
        print("  • Presiona Enter (vacío) cuando termines de añadir")
        print("="*80)

        selected_entities = []
        selected_indices = set()

        while True:
            current_count = len(selected_entities)
            prompt = f"\n➤ Entidad #{current_count + 1} (Enter para terminar): "
            selection = input(prompt).strip().lower()

            # Si presiona Enter vacío, terminar
            if not selection:
                if selected_entities:
                    print(f"\n✓ Selección completada: {len(selected_entities)} entidades")
                    break
                else:
                    print("❌ No se seleccionó ninguna entidad")
                    return []

            # Opción: todos
            if selection in ['todos', 'all', '*']:
                print(f"✓ Seleccionadas TODAS las entidades ({len(entity_list)})")
                return entity_list

            # Parsear selección
            try:
                new_indices = set()

                # Permitir múltiples entradas separadas por comas
                parts = selection.split(',')
                for part in parts:
                    part = part.strip()

                    if '-' in part:
                        # Rango
                        range_parts = part.split('-')
                        if len(range_parts) == 2:
                            start = int(range_parts[0].strip())
                            end = int(range_parts[1].strip())
                            new_indices.update(range(start, end + 1))
                    else:
                        # Número individual
                        new_indices.add(int(part))

                # Añadir nuevas entidades
                added = 0
                for idx in new_indices:
                    if idx not in selected_indices and 1 <= idx <= len(entity_list):
                        entity = entity_list[idx - 1]
                        selected_entities.append(entity)
                        selected_indices.add(idx)
                        added += 1
                        print(f"  ✓ Añadida: {entity['friendly_name']}")

                if added == 0:
                    print("  ⚠️  Entidad(es) ya seleccionada(s) o número inválido")

            except ValueError:
                print("  ❌ Formato inválido. Usa números, rangos o 'todos'")

        # Mostrar resumen
        if selected_entities:
            print(f"\n📊 RESUMEN DE SELECCIÓN ({len(selected_entities)} entidades):")
            for i, entity in enumerate(selected_entities[:10], 1):
                print(f"  {i}. {entity['friendly_name']}")
            if len(selected_entities) > 10:
                print(f"  ... y {len(selected_entities) - 10} más")

        return selected_entities

    def get_current_state(self, entity_id: str) -> Dict[str, Any]:
        """Obtiene el estado actual de una entidad"""
        try:
            url = f"{HA_BASE_URL}/api/states/{entity_id}"
            response = requests.get(url, headers=HEADERS, timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def start_group_monitoring(self, selected_entities: List[Dict[str, Any]], csv_filename: str = None):
        """Inicia monitoreo continuo guardando SOLO cuando cambian los valores"""

        if not selected_entities:
            print("❌ No hay entidades seleccionadas para monitorizar")
            return

        # Generar nombre de archivo si no se proporciona
        if csv_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"monitor_group_{timestamp}.csv"

        print("\n" + "="*80)
        print("🎬 INICIANDO MONITOR DE GRUPO (OPTIMIZADO)")
        print("="*80)
        print(f"📄 Archivo CSV: {csv_filename}")
        print(f"📊 Entidades monitorizadas: {len(selected_entities)}")
        print(f"⚡ Modo: SOLO guardar cuando cambian valores")
        print(f"⏱️  Intervalo de comprobación: 0.5 segundos")
        print("\n⚠️  Presiona ENTER para detener el monitoreo")
        print("="*80)

        monitoring = {"active": True}

        # Diccionario para guardar el último estado conocido de cada entidad
        last_states = {}

        try:
            # Determinar columnas
            fieldnames = ['timestamp', 'entity_id', 'friendly_name', 'domain', 'state']
            common_attrs = ['unit_of_measurement', 'device_class']
            for attr in common_attrs:
                fieldnames.append(f"attr_{attr}")

            # Abrir archivo CSV
            file_exists = os.path.exists(csv_filename)
            csvfile = open(csv_filename, 'a', newline='', encoding='utf-8')
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

            if not file_exists:
                writer.writeheader()

            # Inicializar estados previos y escribir estado inicial
            print("\n📝 Guardando estado inicial...")
            for entity in selected_entities:
                entity_id = entity['entity_id']
                current_state = self.get_current_state(entity_id)

                if current_state:
                    state_value = current_state.get('state', 'unknown')
                    last_states[entity_id] = state_value

                    # Guardar estado inicial
                    row = {
                        'timestamp': datetime.now().isoformat(),
                        'entity_id': entity_id,
                        'friendly_name': entity['friendly_name'],
                        'domain': entity['domain'],
                        'state': state_value
                    }

                    attributes = current_state.get('attributes', {})
                    for attr in common_attrs:
                        if attr in attributes:
                            row[f"attr_{attr}"] = str(attributes[attr])

                    writer.writerow(row)

            csvfile.flush()
            print(f"✓ Estado inicial guardado ({len(selected_entities)} registros)")

            # Thread para monitoreo continuo
            def monitor_loop():
                changes_count = 0
                checks_count = 0

                while monitoring["active"]:
                    checks_count += 1
                    timestamp = datetime.now().isoformat()

                    for entity in selected_entities:
                        entity_id = entity['entity_id']

                        # Obtener estado actual
                        current_state = self.get_current_state(entity_id)

                        if current_state:
                            new_state = current_state.get('state', 'unknown')
                            old_state = last_states.get(entity_id)

                            # Solo guardar si cambió el estado
                            if new_state != old_state:
                                changes_count += 1
                                last_states[entity_id] = new_state

                                row = {
                                    'timestamp': timestamp,
                                    'entity_id': entity_id,
                                    'friendly_name': entity['friendly_name'],
                                    'domain': entity['domain'],
                                    'state': new_state
                                }

                                attributes = current_state.get('attributes', {})
                                for attr in common_attrs:
                                    if attr in attributes:
                                        row[f"attr_{attr}"] = str(attributes[attr])

                                writer.writerow(row)
                                csvfile.flush()

                                # Mostrar cambio
                                print(f"🔄 [{timestamp}] {entity['friendly_name']}: {old_state} → {new_state}")

                    # Mostrar estadísticas cada 100 comprobaciones
                    if checks_count % 100 == 0:
                        print(f"📊 Comprobaciones: {checks_count} | Cambios detectados: {changes_count}")

                    # Esperar antes de la siguiente comprobación (0.5 segundos)
                    time.sleep(0.5)

                csvfile.close()
                print(f"\n✓ Monitoreo finalizado")
                print(f"  📈 Total comprobaciones: {checks_count}")
                print(f"  🔄 Total cambios guardados: {changes_count}")
                print(f"  📄 Archivo: {csv_filename}")

            # Iniciar thread de monitoreo
            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()

            # Esperar a que el usuario presione Enter
            input()

            # Detener monitoreo
            monitoring["active"] = False
            monitor_thread.join(timeout=5)

            print("\n" + "="*80)
            print("🛑 Monitoreo detenido por el usuario")
            print("="*80)

        except Exception as e:
            print(f"❌ Error durante el monitoreo: {e}")
            monitoring["active"] = False


def main():
    """Función principal"""
    print("="*70)
    print("🏠 ANALIZADOR INTELIGENTE DE HOME ASSISTANT")
    print("   Optimizado para Raspberry Pi CM5 + Hailo HAT 2+")
    print("="*70)

    while True:
        print("\n📋 MENÚ PRINCIPAL:")
        print("  1. Análisis completo de entidades")
        print("  2. Monitor de grupo (grabación optimizada CSV)")
        print("  3. Salir")

        choice = input("\n➤ Selecciona una opción (1-3): ").strip()

        if choice == "1":
            # Opción original: Análisis completo
            analyzer = EntityAnalyzer()

            if not analyzer.fetch_all_entities():
                continue

            analyzer.analyze_all()
            analyzer.print_analysis()
            analyzer.save_analysis()

            print("\n💾 Análisis completo guardado en: entity_analysis.json")
            print("   Puedes usar este archivo para el sistema adaptativo.")

        elif choice == "2":
            # Nueva opción: Monitor de grupo optimizado
            analyzer = EntityAnalyzer()

            if not analyzer.fetch_all_entities():
                continue

            # Listar todas las entidades con números
            entity_list = analyzer.list_all_entities_numbered()

            # Seleccionar entidades de forma interactiva
            selected = analyzer.select_entities_interactive(entity_list)

            if selected:
                # Preguntar nombre de archivo
                csv_name = input("\n📄 Nombre del archivo CSV (Enter para auto): ").strip()
                csv_name = csv_name if csv_name else None

                # Iniciar monitoreo optimizado
                analyzer.start_group_monitoring(selected, csv_name)

        elif choice == "3":
            print("\n👋 ¡Hasta luego!")
            break

        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    main()

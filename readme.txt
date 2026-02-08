Home Assistant Entity Analyzer
Script en Python para analizar y clasificar todas las entidades de una instancia de Home Assistant y monitorizar en CSV solo los cambios de estado de las seleccionadas.

Características
Descarga automática de todas las entidades vía API REST de Home Assistant.

Clasificación por dominio y tipo (luces, sensores, binarios, clima, covers, etc.).

Detección aproximada de habitaciones a partir de nombres y friendly_name.

Monitor de grupo interactivo:

Listado numerado de todas las entidades.

Selección de una o varias entidades (números, rangos, “todos”).

Grabación en CSV solo cuando cambia el estado (archivo mucho más pequeño).

Pensado para análisis histórico, diagnóstico y tuning de instalaciones de Home Assistant.

Requisitos
Python 3.9 o superior.

Home Assistant accesible por HTTP (LAN o remoto).

Token de acceso de larga duración de Home Assistant.

Configuración
Antes de ejecutar, exporta las variables de entorno:

text
export HA_BASE_URL="http://TU_IP_O_HOST:8123"
export HA_TOKEN="TU_TOKEN_DE_ACCESO"
Ejemplo:

text
export HA_BASE_URL="http://192.168.x.x:8123"
export HA_TOKEN="eyJ0eXAiOiJKV1QiLCJh..."
Uso

Ejecuta el script principal:

text
python3 entity_analyzer_optimized.py
Menú principal que verás:

text
1. Análisis completo de entidades
2. Monitor de grupo (grabación optimizada CSV)
3. Salir
Análisis completo de entidades

Descarga todas las entidades desde Home Assistant.

Clasifica por tipo (luces, sensores, binarios, clima, covers, etc.).

Intenta asignar habitación a cada entidad.

Muestra un resumen legible en consola.

Guarda el resultado completo en un archivo JSON:

entity_analysis.json

Pasos:

En el menú, escribe: 1

Espera a que termine el análisis.

Revisa la salida por consola y el archivo JSON generado.

Monitor de grupo (CSV optimizado)

Sirve para registrar el histórico de ciertas entidades, pero solo cuando cambian de valor, para que el CSV sea mucho más pequeño.

Flujo:

En el menú, escribe: 2

El script lista todas las entidades numeradas, por ejemplo:

text
1. [sensor          ] Temperatura Salón                 = 22.5
2. [light           ] Luz Cocina                        = on
3. [binary_sensor   ] Puerta Principal                  = off
...
Selección interactiva de entidades
Después del listado, verás las instrucciones:

Escribe "todos" o "all" para seleccionar todas.

Escribe un número para añadir una entidad (ejemplo: 5).

Escribe rangos para añadir varias seguidas (ejemplo: 10-15).

Escribe varios números separados por coma (ejemplo: 21,25,30).

Pulsa Enter vacío cuando termines de añadir entidades.

Ejemplo de selección:

text
➤ Entidad #1 (Enter para terminar): 5
  ✓ Añadida: Temperatura Salón

➤ Entidad #2 (Enter para terminar): 10-12
  ✓ Añadida: Luz Cocina
  ✓ Añadida: Luz Dormitorio
  ✓ Añadida: Luz Pasillo

➤ Entidad #3 (Enter para terminar): 21,25
  ✓ Añadida: Puerta Principal
  ✓ Añadida: Ventana Salón

➤ Entidad #4 (Enter para terminar):
En ese momento se cierra la selección y el script muestra un pequeño resumen de cuántas entidades se van a monitorizar.

Elección del archivo CSV
Después de seleccionar las entidades, el script pregunta:

text
Nombre del archivo CSV (Enter para auto):
Opciones:

Escribir un nombre, por ejemplo:

text
monitor_salon.csv
O simplemente pulsar Enter y dejar que genere un nombre automático del tipo:

text
monitor_group_YYYYMMDD_HHMMSS.csv
Funcionamiento del monitor
Una vez configurado:

Guarda un estado inicial de cada entidad seleccionada.

A continuación entra en un bucle:

Cada 0.5 segundos consulta el estado actual de las entidades.

Solo escribe una nueva línea en el CSV cuando el estado CAMBIA.

Muestra por consola los cambios detectados.

Ejemplo de mensajes en consola:

text
📝 Guardando estado inicial...
✓ Estado inicial guardado (3 registros)

🔄 [2026-02-07T21:00:15] Temperatura Salón: 22.5 → 22.6
🔄 [2026-02-07T21:01:02] Puerta Principal: off → on
📊 Comprobaciones: 100 | Cambios detectados: 2
El CSV resultante contiene solo los cambios, más el estado inicial:

text
timestamp,entity_id,friendly_name,domain,state,attr_unit_of_measurement
2026-02-07T21:00:00,sensor.temp_salon,Temperatura Salón,sensor,22.5,°C
2026-02-07T21:05:12,sensor.temp_salon,Temperatura Salón,sensor,22.6,°C
2026-02-07T21:01:02,binary_sensor.door_main,Puerta Principal,binary_sensor,on,
2026-02-07T21:02:10,binary_sensor.door_main,Puerta Principal,binary_sensor,off,
Cómo detener el monitor
Mientras el monitor está activo, verás:

text
⚠️  Presiona ENTER para detener el monitoreo
Para detenerlo:

Colócate en la consola donde se ejecutó el script.

Pulsa Enter (una línea vacía).

El script:

Detiene el hilo de monitorización.

Cierra el archivo CSV.

Muestra un resumen, por ejemplo:

✓ Monitoreo finalizado
📈 Total comprobaciones: 340
🔄 Total cambios guardados: 5
📄 Archivo: monitor_salon.csv
🛑 Monitoreo detenido por el usuario

Ideas de uso
Seguir la evolución de temperatura y humedad en distintas habitaciones.

Registrar cuándo se abren y cierran puertas y ventanas.

Monitorizar cambios de relés, salidas y dispositivos críticos.

Crear datasets compactos para gráficas con Grafana, pandas u otras herramientas.

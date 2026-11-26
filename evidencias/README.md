# Evidencias de funcionamiento

**Estado: pendientes las evidencias con datos reales.** Todavía no se ha ejecutado la
aplicación contra la base de datos del curso. [pruebas_automaticas.txt](pruebas_automaticas.txt)
muestra las validaciones y los endpoints con datos simulados en SQLite; no reemplaza las
evidencias exigidas.

## Cómo generarlas

1. Completar `.env` y verificar con `python -m app.database.connection`.
2. Iniciar `uvicorn app.main:app` y dejarlo recibiendo datos **al menos 20 minutos**.
3. Sin detenerlo, en otra terminal con el entorno activado:

```powershell
python scripts/generar_evidencias.py --codigo GAS-002
```

Se crean tres archivos:

| Archivo | Pruebas | Contenido |
|---|---|---|
| `mensajes_mqtt.md` | 1 a 7 | Líneas del registro y duración de la captura |
| `base_de_datos.md` | 2 a 7 y 17 | Filas almacenadas y comprobación de que los rechazados no se guardaron |
| `consultas_http.md` | 8 a 17 | Solicitud, código HTTP y respuesta |

4. Revisar que no haya casos marcados como pendientes (si el sensor aún no los ha enviado,
   dejar la captura más tiempo y volver a generar) y subir los archivos con un commit.

## Índice de pruebas

| # | Prueba | Archivo y función | Explicación |
|---|---|---|---|
| 1 | Recepción MQTT | `app/mqtt/client.py` → `on_message` | Registra cada mensaje del tópico |
| 2 | Medición válida | `app/mqtt/ingesta.py` → `procesar_mensaje`; `app/crud/medicion.py` → `crear_lote` | Un registro por magnitud en una transacción |
| 3 | Sensor inexistente | `app/mqtt/ingesta.py` → `validar_contra_catalogo` | Busca `sensor_id` en `sensores.codigo` |
| 4 | Unidad incorrecta | `app/mqtt/ingesta.py` → `validar_contra_catalogo` | Compara con la unidad configurada |
| 5 | Tipo de dato incorrecto | `app/schemas/medicion.py` → `MedidaPayload` | Validación estricta de Pydantic |
| 6 | Magnitud incorrecta | `app/mqtt/ingesta.py` → `validar_contra_catalogo` | La magnitud debe pertenecer al sensor |
| 7 | Timestamp inválido | `app/schemas/medicion.py` → `MensajePayload.validar_timestamp` | Exige ISO 8601 en UTC |
| 8 | ID existente | `app/api/medicion.py` → `obtener_medicion` | Responde 200 |
| 9 | ID inexistente | `app/api/medicion.py` → `obtener_medicion` | Responde 404 |
| 10 | Consulta histórica | `app/crud/medicion.py` → `listar_por_sensor` | Orden descendente por fecha |
| 11 | Rango de fechas | `app/crud/medicion.py` → `listar_por_sensor` | Filtros inclusivos en UTC |
| 12 | `desde > hasta` | `app/api/medicion.py` → `listar_mediciones` | Responde 400 |
| 13 | Validación HTTP | `app/api/medicion.py` → `listar_mediciones` | `limit=0` responde 422 |
| 14 | Última medición | `app/api/medicion.py` → `obtener_ultima_medicion` | Registro más reciente |
| 15 | Últimas N | `app/crud/medicion.py` → `listar_por_sensor` | Aplica `limit` tras ordenar |
| 16 | Filtro por magnitud | `app/crud/medicion.py` → `listar_por_sensor` | Filtra por `sensor_magnitudes.magnitud` |
| 17 | Claves foráneas | `app/models/sensor_magnitud.py`, `app/models/medicion.py` | La medición apunta a su magnitud, y esta a su sensor |
| 18 | Separación de responsabilidades | Carpeta `app/` | Capas `schemas`, `models`, `crud`, `api`, `mqtt` y `database` |

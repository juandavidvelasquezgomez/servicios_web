# Evidencias de funcionamiento

**Estado: pendientes.** Todavía no se ha ejecutado la aplicación contra la base de datos del
curso.

## Cómo generarlas

1. Completar `.env` e iniciar `uvicorn app.main:app`.
2. Dejarlo recibiendo datos **al menos 20 minutos**.
3. En otra terminal, con el entorno activado:

```powershell
python scripts/generar_evidencias.py --codigo GAS-002
```

Se crean `consultas_http.md` (pruebas 8 a 17, con solicitud, código y respuesta) y
`mensajes_mqtt.md` (pruebas 1 a 7, con las líneas del registro y la duración de la captura).

4. Para la prueba 2, agregar una captura de la tabla en PostgreSQL:

```sql
SELECT m.id, sm.magnitud, sm.unidad, m.valor, m.timestamp_utc, m.fecha_recepcion
FROM mediciones m
JOIN sensor_magnitudes sm ON sm.id = m.sensor_magnitud_id
JOIN sensores s ON s.id = sm.sensor_id
WHERE s.codigo = 'GAS-002'
ORDER BY m.id DESC
LIMIT 10;
```

Para las pruebas 3 a 7, comprobar con esa consulta que el mensaje rechazado no tiene registros
con su `timestamp`. Si el sensor no envía algún caso, quedará marcado como pendiente.

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

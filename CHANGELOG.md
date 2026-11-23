# Changelog
Todos los cambios notables de este proyecto se documentarán en este archivo.

## [2.0.0] - 2026-11-23
### Añadido
- **Migración a CentOS Stream 10 + MicroShift *upstream*:** Arquitectura 100% abierta, reproducible sin suscripciones cerradas y validada en modo *Airgap* real (sin conectividad externa). *(La versión original de RHEL 9 permanece respaldada en la rama `legacy/rhel9` y en los tags `v1.0.x`).*
- **Nivel 0 (Supervivencia Nativa K8s):** Incorporación de `livenessProbe` (`/health`), `readinessProbe` (`/status/db`) y `HorizontalPodAutoscaler` (1 → 5 réplicas) en `02-backend-fastapi.yml`.
- **ASD-STE100 + JSON Schema (`format`):** Inferencia determinista (`temperature: 0.0`) con `qwen2.5-coder:1.5b` en Ollama bajo lista blanca de acciones (`enum`), eliminando alucinaciones y bloques Markdown libres.
- **Memoria Episódica y RAG 100% Offline (`arthur.py`):** Registro estructurado de incidentes en `episodic_memory.jsonl` (resumen STE-100) y nuevo comando `/rag <pregunta>` con recuperación bilingüe SRE (`disco <-> disk`, `memoria <-> oom`) citando *timestamps* exactos.
- **Mantenimiento bajo demanda (`/marvin`):** Ejecución directa desde Telegram y desde la botonera de escalamiento Nivel 2, reportando uso de disco e inodos antes y después.

### Cambiado
- **`agatha.py` (SysAdmin Autónoma):** Evolución a arquitectura multihilo con `threading.Lock`, separando reflejos deterministas (0% LLM para disco/inodos y servicios `systemd`) del respaldo cognitivo con Multivac.
- **`05-maintenance-marvin.sh` (Airgap-Safe):** Eliminación de `crictl rmi --prune` para proteger imágenes locales etiquetadas; rotación segura de `journalctl --vacuum-size=50M` y truncado de logs en `/var/log/pods` con código de salida real de SSH.
- **`temple.py`:** `/nivel1` y `/resumen` consumen directamente la memoria episódica estructurada; sanitización y fallback a texto plano para prevenir errores 400 de Markdown en Telegram.

### Corregido
- Fix en el handler `/agatha` de `temple.py` que omitía enviar el cuerpo del estado al responder.
- Corrección de la condición de carrera en `.arthur_cursor` para evitar pérdida de eventos durante la inferencia.
- Blindaje de `imagePullPolicy: IfNotPresent` / `Never` en manifiestos de Gaia para sobrevivir arranques sin red.


## [1.0.0] - 2026-09-22
### Añadido
- `05-maintenance-marvin.sh`: Script de recolección de basura para prevenir saturación de disco (DiskPressure) en el nodo Edge.
- `el_mulo_nerfeado.py`: Herramienta de Chaos Engineering configurada para generar tormentas de errores 404 (simulando escaneos hostiles) sin asfixiar la red.
- Plantilla `.env.example` para parametrización dinámica del entorno.

### Cambiado
- Arquitectura de pruebas (`gaia-test`) migrada a topología de producción en 4 capas (`gaia-frontend`, `gaia-backend`, `gaia-db`).
- `agatha.py` y `temple.py`: Desacoplados de variables estáticas. Ahora consumen las variables dinámicas `TARGET_FRONTEND` y `TARGET_BACKEND` desde el archivo `.env`.
- `dashiell.py`: Integración de consulta SSH directa para monitoreo del espacio físico en disco (partición raíz).
- Tiempos de gracia en la IA ajustados para permitir escalamiento a Nivel 2 en caso de ataques sostenidos.

### Corregido
- Eliminación de la ruta estática `/microshift` en el `hostPath` de `01-db-postgres.yml`.

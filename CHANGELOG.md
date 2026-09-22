# Changelog
Todos los cambios notables de este proyecto se documentarán en este archivo.

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

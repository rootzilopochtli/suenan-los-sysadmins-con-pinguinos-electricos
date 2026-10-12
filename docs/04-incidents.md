# Incidents Log: PositronicOps

## 10-Oct-2026. Incidente Crítico: Falla durante Demostración en vivo

- **Componente Afectado:** Plataforma.
- **Descripción del Problema:** En la respuesta del comando `/status`, los pods de `gaia-backend` se quedaron atascados en un estado de `ErrImageNeverPull`. Posteriormente, al ejecutar el comando `/perf`, Dashiell reportó que la métrica del almacenamiento del nodo Positronic estaba en `DISCO: [██████████] 99%`. A la par, Agatha comenzó a interceptar ráfagas de errores `HTTP 502 Bad Gateway` provenientes de `gaia-frontend` intentando comunicarse con la base de datos de Gaia.
- **Root Cause (Causa Raíz):** Este escenario es idéntico a la saturación que enfrentamos durante las pruebas de laboratorio previas. Al llegar al `99%` de capacidad en el disco, el nodo de MicroShift entró en un estado crítico. Para protegerse y recuperar espacio, el motor de contenedores internamente activa su recolector de basura y purga las imágenes que considera prescindibles o huérfanas. Dado que el manifiesto de despliegue de la aplicación está configurado con `imagePullPolicy: Never` para simular un entorno _Airgap_ estricto, Kubernetes fue incapaz de volver a descargar la imagen a través de internet tras la purga local, manteniendo los pods atrapados en `ErrImageNeverPull`. Sin el backend operando, Nginx no tenía a dónde enrutar el tráfico, lo que generó la cascada de errores `502` que Agatha detectó correctamente, disparando la contención de Nivel 1 y la escalada de Nivel 2.
- **Solución Aplicada:** _(Pendiente ejecución de purga con script de mantenimiento)_

## 12-Oct-2026. Incidente Crítico: Eliminación de Imagen Local en Entorno Airgap (ErrImageNeverPull)

- **Componente Afectado:** Script de Mantenimiento (`05-maintenance-marvin.sh`) y Bucle de Pre-vuelo (`agatha.py`).
- **Descripción del Problema:** Durante una purga automática de almacenamiento detonada por saturación en el disco raíz, el recolector de basura de Podman eliminó la imagen local del backend (`localhost/gaia-backend:v1`). Debido a que el entorno simula una red desconectada (*Airgap*) con la política `imagePullPolicy: Never`, Kubernetes no pudo descargar la imagen desde internet, dejando a los pods atrapados en el estado `ErrImageNeverPull` e impidiendo el arranque del servicio.
- **Root Cause (Causa Raíz):** El script de Marvin utilizaba el comando destructivo `podman system prune -a -f`, cuya bandera `-a` ordena destruir cualquier imagen que no esté respaldando activamente a un contenedor en ejecución en ese preciso instante, barriendo con las imágenes locales requeridas por la plataforma.
- **Solución Aplicada:**
  - Se modificó el script de Marvin removiendo la bandera `-a` del comando `podman system prune -f` para limitar la purga exclusivamente a capas colgantes y cachés huérfanos, respetando las imágenes etiquetadas del clúster.
  - Se implementó la validación preventiva de nodos y réplicas en `agatha.py` mediante la función `chequeo_pre_vuelo`, asegurando la estabilidad del almacenamiento y la plataforma antes de iniciar el monitoreo pasivo.
  - Se reestructuró el flujo de inicialización en `temple.py` para separar el control de los hilos de agentes y garantizar la respuesta de los comandos de diagnóstico en ChatOps ante fallos estructurales.

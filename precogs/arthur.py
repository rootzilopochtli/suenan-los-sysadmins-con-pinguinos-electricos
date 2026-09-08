import os
import requests
import logging
from datetime import datetime

MULTIVAC_URL = "http://localhost:11434/api/generate"
LOG_FILE = "precogs_audit.log"
CURSOR_FILE = ".arthur_cursor"

def obtener_timestamp_linea(linea):
    """Extrae el timestamp inicial de una línea de log."""
    try:
        parte_fecha = linea.split(" - ")[0].strip()
        parte_limpia = parte_fecha.split(",")[0].strip()
        return datetime.strptime(parte_limpia, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def analizar_historial():
    """Ejecuta el pipeline RAG filtrando desde la última auditoría registrada."""
    if not os.path.exists(LOG_FILE):
        return "📭 Los registros están vacíos o inaccesibles."

    with open(LOG_FILE, "r") as f:
        lineas = f.readlines()

    if not lineas:
        return "📭 La línea temporal está limpia."

    ahora_actual = datetime.now()

    # Buscamos en el log la última vez que se ejecutó una auditoría o usamos el cursor guardado
    ultimo_timestamp = None
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r") as f:
            contenido = f.read().strip()
            if contenido:
                try:
                    ultimo_timestamp = datetime.strptime(contenido, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ultimo_timestamp = None

    # Si no hay cursor previo, buscamos la última línea de auditoría en el archivo para sincronizar
    if not ultimo_timestamp:
        for linea in reversed(lineas):
            if "Auditoría manual solicitada" in linea:
                ultimo_timestamp = obtener_timestamp_linea(linea)
                break

    # Filtrar estrictamente las líneas posteriores al último timestamp de auditoría
    lineas_nuevas = []
    for linea in lineas:
        ts_linea = obtener_timestamp_linea(linea)
        if ts_linea and ultimo_timestamp:
            if ts_linea > ultimo_timestamp:
                lineas_nuevas.append(linea)
        elif not ultimo_timestamp:
            lineas_nuevas.append(linea)

    if not lineas_nuevas:
        logging.info("⏭️ [Arthur] Sin nuevos registros desde la última auditoría.")
        return "📭 *Sin novedades.*\nLa línea temporal no ha mutado desde tu última auditoría."

    contexto = "".join(lineas_nuevas)
    logging.info(f"🧠 [Arthur] Evaluando {len(lineas_nuevas)} líneas desde la última auditoría...")

    # Filtro determinista
    claves_peligro = ["[WARNING]", "[CRITICAL]", "[ERROR]", "BOFH"]
    if not any(clave in contexto for clave in claves_peligro):
        logging.info("⏭️ [Arthur] El intervalo es pacífico. Ahorrando LLM.")

        # Actualizamos el cursor con el timestamp actual
        with open(CURSOR_FILE, "w") as f:
            f.write(ahora_actual.strftime("%Y-%m-%d %H:%M:%S"))

        return "🟢 *La línea temporal es estable.*\nCero anomalías críticas detectadas desde tu última consulta."

    logging.info("🧠 [Arthur] ¡Caos detectado! Iniciando Multivac...")

    prompt = f"""Genera un resumen SRE de máximo 3 viñetas muy breves.
PROHIBIDO copiar los logs. Sintetiza la crisis ocurrida en este intervalo.
- BOFH: Comando de usuario bloqueado.
- [WARNING]: Anomalía detectada (Nivel 1).
- [CRITICAL]: Ataque sostenido (Nivel 2).

INCREMENTO TEMPORAL DE LOGS:
{contexto}

RESUMEN TÁCTICO:
-"""

    payload = {
        "model": "qwen2.5-coder:1.5b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 250
        }
    }

    try:
        response = requests.post(MULTIVAC_URL, json=payload, timeout=45)
        response.raise_for_status()

        # Actualizamos el cursor con el timestamp actual
        with open(CURSOR_FILE, "w") as f:
            f.write(ahora_actual.strftime("%Y-%m-%d %H:%M:%S"))

        analisis = response.json().get('response', '').strip()
        analisis = analisis.replace('*', '-').replace('_', '').replace('`', '')

        logging.info("✅ [Arthur] Análisis cognitivo completado.")
        return analisis

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ [Arthur] Fallo de conexión con Multivac: {e}")
        return "❌ [Arthur] Interferencia taquiónica en la conexión con Multivac."


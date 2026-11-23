"""
Autor: Alex Callejas (@rootzilopochtli)
Proyecto: PositronicOps
Version 2.0: CentOS release
Descripción: Arthur - Analista Histórico y Motor RAG sobre Memoria Episódica (STE-100)
"""
import json
import logging
import os
import re
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MULTIVAC_URL = os.getenv("MULTIVAC_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")

LOG_FILE = os.path.join(BASE_DIR, "precogs_audit.log")
CURSOR_FILE = os.path.join(BASE_DIR, ".arthur_cursor")
EPISODIC_MEMORY_FILE = os.path.join(BASE_DIR, "episodic_memory.jsonl")

STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "de", "del", "en", "y", "o", "a",
    "que", "por", "para", "con", "sin", "se", "su", "al", "lo", "como", "mas",
    "the", "and", "for", "with", "from", "that", "this", "was", "are", "is",
}

SRE_SYNONYMS = {
    "disco": {"disk", "storage", "filesystem", "inode", "inodes", "marvin"},
    "almacenamiento": {"disk", "storage", "filesystem", "marvin"},
    "espacio": {"disk", "storage", "filesystem"},
    "inodos": {"inode", "inodes", "disk"},
    "memoria": {"mem", "memory", "ram", "oom", "oomkilled"},
    "ram": {"mem", "memory", "oom"},
    "cpu": {"cpu", "load", "scale"},
    "red": {"network", "http", "nginx", "502", "503", "504", "404", "499"},
    "trafico": {"traffic", "http", "nginx", "502", "503", "504", "499"},
    "servicio": {"service", "systemd", "microshift", "crio"},
    "servicios": {"service", "systemd", "microshift", "crio"},
    "caida": {"down", "crash", "crashloopbackoff", "failed", "restart"},
    "reinicio": {"restart", "rollout"},
    "base": {"db", "postgres", "postgresql"},
}


def _tokenizar(texto):
    """Extrae tokens normalizados y expande sinónimos SRE ES<->EN."""
    tokens = re.findall(r"[a-z0-9_.-]+", texto.lower())
    base = {t for t in tokens if len(t) > 2 and t not in STOPWORDS}
    expandidos = set(base)
    for t in base:
        if t in SRE_SYNONYMS:
            expandidos.update(SRE_SYNONYMS[t])
    return expandidos


def sanitizar_markdown(texto):
    """Evita errores 400 del parser Markdown clásico de Telegram y dobles viñetas."""
    limpio = str(texto).replace("*", "").replace("_", " ").replace("`", "'").strip()
    return limpio.lstrip("-• ").strip()


def obtener_timestamp_linea(linea):
    """Extrae el timestamp inicial de una línea de precogs_audit.log."""
    try:
        parte_fecha = linea.split(" - ")[0].strip()
        parte_limpia = parte_fecha.split(",")[0].strip()
        return datetime.strptime(parte_limpia, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def parsear_timestamp(ts_str):
    """Convierte una cadena YYYY-MM-DD HH:MM:SS a datetime."""
    try:
        return datetime.strptime(ts_str.strip(), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def obtener_cursor():
    """Lee la marca de tiempo de la última auditoría confirmada."""
    if not os.path.exists(CURSOR_FILE):
        return None
    try:
        with open(CURSOR_FILE, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            return parsear_timestamp(contenido) if contenido else None
    except OSError as e:
        logging.error(f"❌ [Arthur] Error leyendo cursor: {e}")
        return None


def guardar_cursor(timestamp):
    """Persiste el último timestamp procesado en .arthur_cursor."""
    try:
        with open(CURSOR_FILE, "w", encoding="utf-8") as f:
            f.write(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    except OSError as e:
        logging.error(f"❌ [Arthur] Error escribiendo cursor: {e}")


def cargar_memoria_episodica():
    """Carga todos los incidentes estructurados desde episodic_memory.jsonl."""
    if not os.path.exists(EPISODIC_MEMORY_FILE):
        return []

    episodios = []
    with open(EPISODIC_MEMORY_FILE, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                episodios.append(json.loads(linea))
            except json.JSONDecodeError:
                continue
    return episodios


def obtener_resumen_episodico(ultimos=5):
    """
    Helper determinista para temple.py (/nivel1 y /resumen).
    Retorna estadísticas agregadas y los últimos N episodios.
    """
    episodios = cargar_memoria_episodica()
    resueltos = sum(1 for e in episodios if e.get("outcome") == "RESOLVED")
    escalados = sum(1 for e in episodios if e.get("outcome") == "ESCALATED")
    fallidos = sum(1 for e in episodios if e.get("outcome") == "FAILED")
    return {
        "total": len(episodios),
        "resueltos": resueltos,
        "escalados": escalados,
        "fallidos": fallidos,
        "recientes": episodios[-ultimos:],
    }


def recuperar_episodios_relevantes(consulta, top_k=5):
    """
    Pipeline de recuperación determinista sobre episodic_memory.jsonl.
    Puntúa coincidencia de términos sobre trigger, acción, resultado y resumen STE-100.
    """
    episodios = cargar_memoria_episodica()
    if not episodios:
        return []

    tokens_consulta = _tokenizar(consulta)
    if not tokens_consulta:
        return episodios[-top_k:]

    puntuados = []
    for idx, ep in enumerate(episodios):
        cuerpo = " ".join([
            str(ep.get("trigger", "")),
            str(ep.get("action", "")),
            str(ep.get("reason", "")),
            str(ep.get("outcome", "")),
            str(ep.get("ste_summary", "")),
        ])
        tokens_ep = _tokenizar(cuerpo)
        coincidencias = len(tokens_consulta & tokens_ep)
        if coincidencias > 0:
            puntuados.append((coincidencias, idx, ep))

    puntuados.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [ep for _, _, ep in puntuados[:top_k]]


def _invocar_multivac_json(prompt, schema, num_predict=260):
    """Wrapper común hacia Ollama con temperatura 0.0 y salida JSON estricta."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": num_predict,
        },
        "format": schema,
    }
    response = requests.post(MULTIVAC_URL, json=payload, timeout=45)
    response.raise_for_status()
    raw = response.json().get("response", "").strip()
    return json.loads(raw)


def analizar_historial():
    """
    Ejecuta la auditoría incremental (/auditoria) combinando memoria episódica
    y eventos críticos nuevos en precogs_audit.log desde .arthur_cursor.
    """
    ultimo_cursor = obtener_cursor()
    episodios = cargar_memoria_episodica()

    episodios_nuevos = []
    ultimo_ts = ultimo_cursor

    for ep in episodios:
        ts_ep = parsear_timestamp(ep.get("timestamp", ""))
        if not ts_ep:
            continue
        if ultimo_cursor is None or ts_ep > ultimo_cursor:
            episodios_nuevos.append(ep)
            if ultimo_ts is None or ts_ep > ultimo_ts:
                ultimo_ts = ts_ep

    lineas_nuevas = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for linea in f:
                if "Auditoría manual solicitada" in linea:
                    continue
                ts_linea = obtener_timestamp_linea(linea)
                if not ts_linea:
                    continue
                if ultimo_cursor is None or ts_linea > ultimo_cursor:
                    lineas_nuevas.append(linea.strip())
                    if ultimo_ts is None or ts_linea > ultimo_ts:
                        ultimo_ts = ts_linea

    if not episodios_nuevos and not lineas_nuevas:
        logging.info("⏭️ [Arthur] Sin nuevos registros desde la última auditoría.")
        return "📭 *Sin novedades.*\nLa línea temporal no ha mutado desde tu última auditoría."

    # Filtro determinista: ahorrar inferencia si el intervalo fue pacífico
    claves_peligro = ("[WARNING]", "[CRITICAL]", "[ERROR]", "BOFH")
    logs_criticos = [l for l in lineas_nuevas if any(c in l for c in claves_peligro)]

    if not episodios_nuevos and not logs_criticos:
        logging.info("⏭️ [Arthur] El intervalo es pacífico. Ahorrando LLM.")
        if ultimo_ts:
            guardar_cursor(ultimo_ts)
        return (
            "🟢 *La línea temporal es estable.*\n"
            "Cero incidentes ni anomalías críticas desde tu última consulta."
        )

    resumen_episodios = "\n".join(
        f"- [{e.get('timestamp')}] trigger={e.get('trigger')} action={e.get('action')} "
        f"outcome={e.get('outcome')} | {e.get('ste_summary')}"
        for e in episodios_nuevos[-10:]
    ) or "None"

    resumen_logs = "\n".join(logs_criticos[-15:]) or "None"

    logging.info(
        f"🧠 [Arthur] Auditando {len(episodios_nuevos)} episodios y "
        f"{len(logs_criticos)} líneas críticas con Multivac..."
    )

    prompt = f"""Role: Linux Edge SRE incident auditor.
Domain glossary:
- Marvin: automated disk cleanup script (never a disk or server).
- Agatha: autonomous SRE monitoring agent.

Rules (ASD-STE100 style):
- Use only facts present in the provided episodes and logs.
- Severity rules:
  - LOW: all incidents are RESOLVED.
  - MEDIUM: only BOFH blocks or warnings without outage.
  - HIGH: repeated failures or degraded pods.
  - CRITICAL: outcome is FAILED or ESCALATED.
- Do not prefix findings with dashes or bullets.
- Provide 1 to 2 distinct short findings (no duplicates) and 1 short recommendation.
- Write findings and recommendation in technical Spanish (example: "Disco raiz alcanzo 92% y el script Marvin redujo el uso a 62%.").

EPISODIC MEMORY (STE-100):
{resumen_episodios}

CRITICAL AUDIT LOGS:
{resumen_logs}
"""

    schema = {
        "type": "object",
        "properties": {
            "severity": {
                "type": "string",
                "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            },
            "findings": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 3,
            },
            "recommendation": {"type": "string"},
        },
        "required": ["severity", "findings", "recommendation"],
    }

    try:
        resultado = _invocar_multivac_json(prompt, schema)
        if ultimo_ts:
            guardar_cursor(ultimo_ts)

        sev = resultado.get("severity", "MEDIUM")
        iconos = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
        icono = iconos.get(sev, "🟡")

        hallazgos = resultado.get("findings", [])[:3]
        vinetas = "\n".join(f"• {sanitizar_markdown(h)}" for h in hallazgos if h)
        rec = sanitizar_markdown(resultado.get("recommendation", "Mantener vigilancia activa."))

        logging.info(f"✅ [Arthur] Auditoría completada (Severidad: {sev}).")
        return (
            f"{icono} *Severidad:* `{sev}`\n\n"
            f"*Hallazgos:*\n{vinetas}\n\n"
            f"🛠️ *Recomendación:* {rec}"
        )
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logging.error(f"❌ [Arthur] Fallo de inferencia con Multivac: {e}")
        return "❌ [Arthur] Interferencia taquiónica en la conexión con Multivac."


def consultar_memoria(pregunta):
    """
    RAG interactivo (/rag <pregunta>): recupera episodios similares desde
    episodic_memory.jsonl y responde citando únicamente evidencia real.
    """
    pregunta = pregunta.strip()
    if not pregunta:
        return "ℹ️ Uso: `/rag <pregunta>` (ej. `/rag disco` o `/rag 502`)."

    relevantes = recuperar_episodios_relevantes(pregunta, top_k=5)
    if not relevantes:
        return "📭 No encontré incidentes previos en la memoria episódica relacionados con esa consulta."

    contexto = "\n".join(
        f"[{e.get('timestamp')}] trigger={e.get('trigger')} action={e.get('action')} "
        f"outcome={e.get('outcome')} | summary={e.get('ste_summary')}"
        for e in relevantes
    )

    prompt = f"""Role: Linux Edge SRE RAG assistant.
Domain glossary:
- Marvin: automated disk cleanup script (never a disk or server).
- Agatha: autonomous SRE monitoring agent.

Rules (ASD-STE100 style):
- Answer using ONLY the retrieved episodic incidents below.
- If evidence is insufficient, state it directly.
- Write answer and suggested_action in concise technical Spanish.
- Cite matching timestamps from the retrieved incidents.

USER QUESTION:
{pregunta}

RETRIEVED EPISODIC MEMORY:
{contexto}
"""

    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "cited_timestamps": {
                "type": "array",
                "items": {"type": "string"},
            },
            "suggested_action": {"type": "string"},
        },
        "required": ["answer", "cited_timestamps", "suggested_action"],
    }

    try:
        res = _invocar_multivac_json(prompt, schema, num_predict=220)
        resp = sanitizar_markdown(res.get("answer", ""))
        accion = sanitizar_markdown(res.get("suggested_action", "Ninguna."))
        citas = ", ".join(f"`{sanitizar_markdown(c)}`" for c in res.get("cited_timestamps", [])[:5]) or "`N/A`"

        return (
            f"🧠 *Respuesta RAG (Arthur):*\n{resp}\n\n"
            f"🛠️ *Acción sugerida:* {accion}\n"
            f"📎 *Evidencia:* {citas}"
        )
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logging.error(f"❌ [Arthur-RAG] Fallo consultando a Multivac: {e}")
        return "❌ [Arthur] No se pudo completar la consulta RAG con Multivac."

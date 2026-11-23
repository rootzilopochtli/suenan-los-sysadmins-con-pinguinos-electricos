"""
Autor: Alex Callejas (@rootzilopochtli)
Proyecto: PositronicOps
Version 2.0: CentOS release
Descripción: Agatha - SysAdmin Autónoma (Vigilancia de Infraestructura + Tráfico + Memoria Episódica)
"""
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "precogs_audit.log")
EPISODIC_MEMORY_FILE = os.path.join(BASE_DIR, "episodic_memory.jsonl")
MARVIN_SCRIPT = os.path.join(BASE_DIR, "..", "magrathea", "scripts", "05-maintenance-marvin.sh")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

# --- VARIABLES DE ENTORNO DINÁMICAS ---
MULTIVAC_URL = os.getenv("MULTIVAC_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
TARGET_FRONTEND = os.getenv("TARGET_FRONTEND", "deployment/gaia-frontend")
TARGET_BACKEND = os.getenv("TARGET_BACKEND", "deployment/gaia-backend")
TARGET_NAMESPACE = os.getenv("TARGET_NAMESPACE", "default")
KUBECONFIG_PATH = os.path.expanduser(os.getenv("KUBECONFIG_PATH", ""))
NODE_IP = os.getenv("NODE_IP", "192.168.122.32")
SSH_KEY_PATH = os.path.expanduser(
    os.getenv("SSH_KEY_PATH", os.path.join(BASE_DIR, "..", "magrathea", "labkey"))
)

# --- UMBRALES DE SYSADMIN (Ajustables desde .env) ---
DISK_THRESHOLD = int(os.getenv("DISK_THRESHOLD", "90"))
INODE_THRESHOLD = int(os.getenv("INODE_THRESHOLD", "90"))
CPU_THRESHOLD = int(os.getenv("CPU_THRESHOLD", "85"))
MEM_THRESHOLD = int(os.getenv("MEM_THRESHOLD", "85"))
SYSADMIN_POLL_INTERVAL = int(os.getenv("SYSADMIN_POLL_INTERVAL", "60"))

ALLOWED_SERVICES = {"microshift", "crio"}

# Estado global compartido con ChatOps (temple.py)
estado_actual = {
    "nivel_amenaza": 0,
    "status": "Iniciando diagnóstico...",
    "ultima_telemetria": {},
}

# Lock para evitar que el loop de SysAdmin y el de Nginx actúen al mismo tiempo
remediacion_lock = threading.Lock()


def consultar_estado():
    """Retorna el estado operativo actual formateado para ChatOps."""
    amenaza = estado_actual["nivel_amenaza"]
    status = estado_actual["status"]
    tel = estado_actual.get("ultima_telemetria", {})

    if amenaza == 0:
        icono = "🟢"
    elif amenaza == 1:
        icono = "🟡"
    else:
        icono = "🔴"

    resumen_tel = ""
    if tel:
        resumen_tel = (
            f"\n*Último pulso:* CPU `{tel.get('cpu', '?')}%` | "
            f"RAM `{tel.get('mem', '?')}%` | Disco `{tel.get('disk', '?')}%` "
            f"(Inodos `{tel.get('inodes', '?')}%`)"
        )

    return (
        f"{icono} *Visión Precognitiva (Agatha)*\n\n"
        f"*Nivel de Amenaza:* {amenaza}\n"
        f"*Estado:* {status}{resumen_tel}"
    )


# =====================================================================
# CAPA DE MEMORIA EPISÓDICA (Base STE-100 para el futuro RAG de Arthur)
# =====================================================================

def registrar_memoria_episodica(trigger, telemetry, action, reason, outcome, ste_summary):
    """Guarda un registro estructurado JSONL en estilo STE-100 para el RAG de Arthur."""
    entrada = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "node_ip": NODE_IP,
        "trigger": trigger,
        "telemetry": telemetry,
        "action": action,
        "reason": reason,
        "outcome": outcome,
        "ste_summary": ste_summary,
    }
    try:
        with open(EPISODIC_MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except OSError as e:
        logging.error(f"❌ [Agatha] No se pudo escribir en memoria episódica: {e}")


# =====================================================================
# CAPA DE UTILIDADES SSH / OC (Recolección de Telemetría SysAdmin)
# =====================================================================

def ejecutar_ssh(comando_remoto, timeout=15):
    """Ejecuta un comando SSH no interactivo (nunca se bloquea pidiendo password)."""
    if not NODE_IP:
        return False, "NODE_IP no definida en .env"

    cmd = [
        "ssh",
        "-i", SSH_KEY_PATH,
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        "-o", "StrictHostKeyChecking=no",
        "-o", "GSSAPIAuthentication=no",
        f"positronic-user@{NODE_IP}",
        comando_remoto,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
        return True, res.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout ejecutando comando SSH"
    except subprocess.CalledProcessError as e:
        return False, (e.stderr or e.stdout).strip()


def obtener_logs_microshift_ssh(lineas=8):
    """Extrae las últimas líneas del journal de microshift para diagnóstico."""
    ok, out = ejecutar_ssh(f"sudo journalctl -u microshift.service -n {lineas} --no-pager")
    return out if ok else f"Error extrayendo logs SSH: {out}"


def verificar_espacio_disco():
    """Retorna (peligro_bool, uso_disco_pct, uso_inodos_pct)."""
    cmd = (
        "df -P / | awk 'NR==2 {gsub(\"%\",\"\"); print $5}'; "
        "df -Pi / | awk 'NR==2 {gsub(\"%\",\"\"); print $5}'"
    )
    ok, out = ejecutar_ssh(cmd)
    if not ok:
        return False, "N/A", "N/A"

    lineas = [l.strip() for l in out.splitlines() if l.strip()]
    try:
        disk_pct = int(lineas[0])
        inode_pct = int(lineas[1]) if len(lineas) > 1 else 0
        en_peligro = (disk_pct >= DISK_THRESHOLD) or (inode_pct >= INODE_THRESHOLD)
        return en_peligro, disk_pct, inode_pct
    except (ValueError, IndexError):
        return False, "N/A", "N/A"


def recolectar_telemetria_sysadmin():
    """
    Recolecta CPU, RAM, Disco, Inodos, servicios systemd y top procesos
    en una sola conexión SSH, más el estado de pods vía oc.
    """
    script_remoto = (
        "echo DISK=$(df -P / | awk 'NR==2 {gsub(\"%\",\"\"); print $5}'); "
        "echo INODES=$(df -Pi / | awk 'NR==2 {gsub(\"%\",\"\"); print $5}'); "
        "echo MEM=$(free | awk '/Mem:/ {printf \"%d\", ($3/$2)*100}'); "
        "read _ u1 n1 s1 i1 _ < /proc/stat; sleep 1; read _ u2 n2 s2 i2 _ < /proc/stat; "
        "dt=$(( (u2+n2+s2+i2)-(u1+n1+s1+i1) )); "
        "du=$(( (u2+n2+s2)-(u1+n1+s1) )); "
        "echo CPU=$(( dt > 0 ? du * 100 / dt : 0 )); "
        "echo SVC_MICROSHIFT=$(systemctl is-active microshift 2>/dev/null || true); "
        "echo SVC_CRIO=$(systemctl is-active crio 2>/dev/null || true); "
        "echo '---PROCS---'; "
        "ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n 6"
    )

    ok, out = ejecutar_ssh(script_remoto, timeout=15)
    if not ok:
        return None, out

    datos = {
        "disk": 0,
        "inodes": 0,
        "mem": 0,
        "cpu": 0,
        "services": {},
        "top_procs": "",
        "unhealthy_pods": [],
    }

    partes = out.split("---PROCS---")
    cabecera = partes[0].strip().splitlines()
    datos["top_procs"] = partes[1].strip() if len(partes) > 1 else ""

    for linea in cabecera:
        if "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        v = v.strip()
        if k in ("DISK", "INODES", "MEM", "CPU"):
            try:
                datos[k.lower()] = int(v)
            except ValueError:
                datos[k.lower()] = 0
        elif k == "SVC_MICROSHIFT":
            datos["services"]["microshift"] = v
        elif k == "SVC_CRIO":
            datos["services"]["crio"] = v

    # Revisar pods con estado anómalo en el namespace objetivo
    try:
        res_pods = subprocess.run(
            ["oc", "--kubeconfig", KUBECONFIG_PATH, "get", "pods", "-n", TARGET_NAMESPACE, "--no-headers"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        for linea in res_pods.stdout.strip().splitlines():
            cols = linea.split()
            if len(cols) >= 3:
                nombre, ready, status = cols[0], cols[1], cols[2]
                r_cur, _, r_tot = ready.partition("/")
                if status != "Running" or r_cur != r_tot:
                    datos["unhealthy_pods"].append(f"{nombre} ({status}, ready={ready})")
    except Exception as e:
        datos["unhealthy_pods"].append(f"oc_error: {e}")

    estado_actual["ultima_telemetria"] = {
        "cpu": datos["cpu"],
        "mem": datos["mem"],
        "disk": datos["disk"],
        "inodes": datos["inodes"],
    }
    return datos, None


# =====================================================================
# ACCIONES DE REMEDIACIÓN (Lista Blanca + Verificación)
# =====================================================================

def invocar_marvin():
    """Invoca el script de mantenimiento de Marvin heredando NODE_IP y SSH_KEY_PATH."""
    env = os.environ.copy()
    env["NODE_IP"] = NODE_IP
    env["SSH_KEY_PATH"] = SSH_KEY_PATH
    try:
        res = subprocess.run(
            ["bash", MARVIN_SCRIPT],
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        logging.info(f"🧹 [Marvin] Código de salida: {res.returncode}")
        return res.returncode == 0
    except Exception as e:
        logging.error(f"❌ [Agatha] Error invocando a Marvin: {e}")
        return False


def reiniciar_servicio_systemd(nombre_servicio):
    """Reinicia únicamente servicios dentro de la lista blanca y verifica su estado."""
    if nombre_servicio not in ALLOWED_SERVICES:
        logging.warning(f"🛡️ [Guardrail] Servicio no autorizado para reinicio: {nombre_servicio}")
        return False

    ok, _ = ejecutar_ssh(f"sudo systemctl restart {nombre_servicio}", timeout=30)
    if not ok:
        return False
    time.sleep(5)
    ok_check, status = ejecutar_ssh(f"systemctl is-active {nombre_servicio}")
    return ok_check and status == "active"


def ejecutar_accion_remediatoria(decision, callback_notificacion):
    """
    Python dispone: traduce la decisión JSON de Multivac en una acción segura y verificada.
    Retorna True si la acción fue ejecutada con éxito, False si se debe escalar a Nivel 2.
    """
    action = decision.get("action", "escalate")
    target = decision.get("target", "")
    reason = decision.get("reason", "No reason provided.")

    if action == "escalate":
        return False

    if action == "run_marvin":
        cmd_log = f"bash {MARVIN_SCRIPT}"
        logging.info(f"🤖 [Multivac] Solución propuesta:\n{cmd_log}")
        callback_notificacion(f"⚡ *Auto-Remediación (Marvin)*\nMotivo: _{reason}_")
        return invocar_marvin()

    if action == "restart_backend":
        cmd = ["oc", "--kubeconfig", KUBECONFIG_PATH, "rollout", "restart", TARGET_BACKEND, "-n", TARGET_NAMESPACE]
        cmd_log = f"oc rollout restart {TARGET_BACKEND} -n {TARGET_NAMESPACE}"
        logging.info(f"🤖 [Multivac] Solución propuesta:\n{cmd_log}")
        callback_notificacion(f"⚡ *Auto-Remediación*\nMotivo: _{reason}_\nEjecutando: `{cmd_log}`")
        try:
            subprocess.run(cmd, check=True, timeout=30)
            return True
        except Exception as e:
            logging.error(f"❌ Fallo en rollout restart: {e}")
            return False

    if action == "scale_backend":
        cmd = ["oc", "--kubeconfig", KUBECONFIG_PATH, "scale", TARGET_BACKEND, "--replicas=3", "-n", TARGET_NAMESPACE]
        cmd_log = f"oc scale {TARGET_BACKEND} --replicas=3 -n {TARGET_NAMESPACE}"
        logging.info(f"🤖 [Multivac] Solución propuesta:\n{cmd_log}")
        callback_notificacion(f"⚡ *Auto-Remediación*\nMotivo: _{reason}_\nEjecutando: `{cmd_log}`")
        try:
            subprocess.run(cmd, check=True, timeout=30)
            return True
        except Exception as e:
            logging.error(f"❌ Fallo en oc scale: {e}")
            return False

    if action == "restart_service":
        svc = target if target in ALLOWED_SERVICES else "microshift"
        cmd_log = f"systemctl restart {svc}"
        logging.info(f"🤖 [Multivac] Solución propuesta:\n{cmd_log}")
        callback_notificacion(f"⚡ *Auto-Remediación*\nMotivo: _{reason}_\nEjecutando: `{cmd_log}`")
        return reiniciar_servicio_systemd(svc)

    return False


# =====================================================================
# ## 2. Inferencia Local: La Sinapsis (STE-100 + JSON Schema estricto)
# Agatha consulta a Multivac (Ollama) localmente. Cero nube pública.
# =====================================================================

# [DEMO1] La Sinapsis (STE-100 + JSON Schema en localhost)
def solicitar_remediacion_multivac(trigger, telemetry, contexto_logs):
    """
    Envía telemetría y logs a Multivac usando instrucciones estilo ASD-STE100
    y salida estructurada (JSON Schema) con temperatura 0.0 para cero divagación.
    """
    logging.info(f"🧠 [Agatha] Contactando a Multivac (Trigger: {trigger})...")

    prompt = f"""Role: Linux Edge SRE diagnostic engine.
Rules (ASD-STE100 style):
- Use short, direct sentences.
- Do not add explanations outside the JSON object.
- Select exactly one action from the allowed list.

Allowed actions:
- "run_marvin": Select if disk usage or inode usage is 90 percent or higher.
- "restart_backend": Select if backend pods fail, crash, or return HTTP 502, 503, or 504 errors.
- "scale_backend": Select if HTTP traffic errors or high CPU saturate the single backend replica.
- "restart_service": Select if microshift or crio service is inactive. Set target to "microshift" or "crio".
- "escalate": Select if root cause is unclear, memory exhaustion persists, or manual intervention is required.

System state:
- Trigger: {trigger}
- Deployment: {TARGET_BACKEND} (Namespace: {TARGET_NAMESPACE})
- Telemetry: {json.dumps(telemetry, ensure_ascii=False)}
- Recent logs:
{contexto_logs}

Return JSON with:
- action: selected action from the allowed list.
- target: service or deployment name.
- reason: one short sentence (max 15 words) explaining the decision.
- ste_summary: one short technical sentence in Simplified Technical English describing symptom and action for future RAG retrieval.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 180,
        },
        "format": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "run_marvin",
                        "restart_backend",
                        "scale_backend",
                        "restart_service",
                        "escalate",
                    ],
                },
                "target": {"type": "string"},
                "reason": {"type": "string"},
                "ste_summary": {"type": "string"},
            },
            "required": ["action", "target", "reason", "ste_summary"],
        },
    }

    try:
        response = requests.post(MULTIVAC_URL, json=payload, timeout=35)
        response.raise_for_status()
        raw_text = response.json().get("response", "").strip()
        decision = json.loads(raw_text)
        logging.info(f"🤖 [Multivac] Decisión estructurada: {decision}")
        return decision
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logging.error(f"❌ [Error] Fallo de inferencia con Multivac: {e}")
        return None


# =====================================================================
# INICIO DE FUNCIONES DE PRE-VUELO
# =====================================================================

def verificar_estado_plataforma():
    """Revisa si el nodo está Ready y si el despliegue tiene réplicas listas."""
    cmd_nodo = [
        "oc", "--kubeconfig", KUBECONFIG_PATH, "get", "nodes",
        "-o", "jsonpath='{.items[0].status.conditions[?(@.type==\"Ready\")].status}'",
    ]
    try:
        res_nodo = subprocess.run(cmd_nodo, capture_output=True, text=True, timeout=10, check=True)
        nodo_ready = res_nodo.stdout.strip().replace("'", "")
        if nodo_ready != "True":
            return False, "NodeNotReady"
    except Exception:
        return False, "ErrorNodo"

    cmd_deploy = [
        "oc", "--kubeconfig", KUBECONFIG_PATH, "get", TARGET_BACKEND,
        "-n", TARGET_NAMESPACE, "-o", "jsonpath='{.status.readyReplicas}'",
    ]
    try:
        res_deploy = subprocess.run(cmd_deploy, capture_output=True, text=True, timeout=10, check=True)
        replicas = res_deploy.stdout.strip().replace("'", "")
        if replicas and int(replicas) > 0:
            return True, "OK"
        return False, "ReplicasZero"
    except Exception:
        return False, "ErrorDeploy"


def chequeo_pre_vuelo(callback_notificacion, callback_escalamiento_critico):
    """Valida nodo, almacenamiento y réplicas antes de abrir el monitoreo continuo."""
    estado_actual["status"] = "Verificando estado de la plataforma..."
    logging.info("🛫 [Agatha] Iniciando pre-vuelo...")

    max_intentos = 10
    intento_actual = 1
    razon_falla = "Unknown"

    while intento_actual <= max_intentos:
        plataforma_lista, razon_falla = verificar_estado_plataforma()
        if plataforma_lista:
            logging.info("✅ Pre-vuelo exitoso. Plataforma estable.")
            estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
            return True

        if razon_falla == "NodeNotReady" and intento_actual < max_intentos:
            logging.warning(
                f"⏳ [Agatha] El nodo no está listo (Intento {intento_actual}/{max_intentos}). Esperando estabilización CNI..."
            )
            estado_actual["status"] = f"Esperando estabilización de red ({intento_actual}/{max_intentos})..."
            time.sleep(30)
            intento_actual += 1
            continue
        break

    logging.warning(f"⚠️ [Agatha] Falla confirmada en arranque: {razon_falla}")

    # 1. Reflejo determinista de disco/inodos
    disco_lleno, disk_pct, inode_pct = verificar_espacio_disco()
    if disco_lleno:
        msg = f"🚨 *[Agatha] Alerta de Almacenamiento (Disco {disk_pct}%, Inodos {inode_pct}%):* Invocando a Marvin..."
        logging.info(msg)
        callback_notificacion(msg)
        invocar_marvin()
        time.sleep(15)

        plataforma_lista, razon_falla = verificar_estado_plataforma()
        if plataforma_lista:
            registrar_memoria_episodica(
                "preflight_disk_pressure",
                {"disk": disk_pct, "inodes": inode_pct},
                "run_marvin",
                "Root filesystem exceeded threshold during pre-flight.",
                "RESOLVED",
                f"Root disk reached {disk_pct} percent during boot; Marvin cleaned caches and restored cluster.",
            )
            callback_notificacion("🟢 *Remediación exitosa:* Marvin estabilizó el almacenamiento y la plataforma levantó.")
            estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
            return True

    # 2. Reflejo determinista de desincronización de réplicas
    if razon_falla == "ReplicasZero":
        callback_notificacion("🔄 *[Agatha] Desincronización detectada:* Reiniciando backend para reenganchar con DB...")
        try:
            subprocess.run(
                ["oc", "--kubeconfig", KUBECONFIG_PATH, "rollout", "restart", TARGET_BACKEND, "-n", TARGET_NAMESPACE],
                check=True, timeout=30,
            )
            time.sleep(20)
            plataforma_lista, _ = verificar_estado_plataforma()
            if plataforma_lista:
                registrar_memoria_episodica(
                    "preflight_replicas_zero",
                    {},
                    "restart_backend",
                    "Backend had zero ready replicas during pre-flight.",
                    "RESOLVED",
                    "Backend deployment reported zero ready replicas; rollout restart restored service.",
                )
                callback_notificacion("🟢 *Remediación exitosa:* El backend fue reiniciado y la plataforma está estable.")
                estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
                return True
        except Exception as e:
            logging.error(f"Fallo al intentar auto-remediar el rollout: {e}")

    # 3. Escalamiento crítico al SRE con evidencia real
    estado_actual["status"] = "Falla crítica detectada en el arranque."
    evidencia = obtener_logs_microshift_ssh(lineas=5)
    contexto = f"Falla de arranque ({razon_falla}). Últimos logs:\n{evidencia}"
    registrar_memoria_episodica(
        f"preflight_{razon_falla}",
        {"disk": disk_pct, "inodes": inode_pct},
        "escalate",
        "Automated pre-flight remediation failed.",
        "ESCALATED",
        f"Pre-flight failed with {razon_falla}; automated recovery failed and escalated to SRE.",
    )
    callback_escalamiento_critico(contexto)
    return False


# =====================================================================
# BUCLE SYSADMIN PROACTIVO (CPU, RAM, Disco/Inodos, Servicios, Pods)
# =====================================================================

def bucle_sysadmin(callback_notificacion, callback_escalamiento):
    """
    Hilo paralelo de vigilancia de infraestructura Linux + MicroShift.
    Actúa determinísticamente en fallos conocidos y consulta a Multivac en casos ambiguos.
    """
    logging.info(f"🛠️ [Agatha-SysAdmin] Guardia activa cada {SYSADMIN_POLL_INTERVAL}s.")

    while True:
        time.sleep(SYSADMIN_POLL_INTERVAL)

        if not remediacion_lock.acquire(blocking=False):
            continue

        try:
            tel, err = recolectar_telemetria_sysadmin()
            if err or not tel:
                logging.warning(f"⚠️ [Agatha-SysAdmin] No se pudo recolectar telemetría: {err}")
                continue

            # 1. ACCIÓN DETERMINISTA: Presión de Disco o Inodos -> Marvin
            if tel["disk"] >= DISK_THRESHOLD or tel["inodes"] >= INODE_THRESHOLD:
                logging.warning(
                    f"⚠️ [Agatha-SysAdmin] Presión de almacenamiento: Disco {tel['disk']}%, Inodos {tel['inodes']}%"
                )
                callback_notificacion(
                    f"🧹 *[Agatha-SysAdmin] Alerta de Disco ({tel['disk']}%, Inodos {tel['inodes']}%):* "
                    "Ejecutando purga automática con Marvin..."
                )
                invocar_marvin()
                time.sleep(10)
                _, post_disk, post_inodes = verificar_espacio_disco()

                if isinstance(post_disk, int) and post_disk < DISK_THRESHOLD:
                    registrar_memoria_episodica(
                        "disk_pressure",
                        tel,
                        "run_marvin",
                        "Disk exceeded threshold.",
                        "RESOLVED",
                        f"Root disk reached {tel['disk']} percent; Marvin reduced usage to {post_disk} percent.",
                    )
                    callback_notificacion(f"🟢 *[Agatha-SysAdmin] Disco saneado:* Uso actual `{post_disk}%`.")
                else:
                    registrar_memoria_episodica(
                        "disk_pressure",
                        tel,
                        "run_marvin",
                        "Disk remained critical after Marvin cleanup.",
                        "ESCALATED",
                        f"Root disk stayed at {post_disk} percent after Marvin run; escalated to SRE.",
                    )
                    callback_escalamiento(
                        "🔥 *[Agatha-SysAdmin] Disco crítico persistente:* Marvin no liberó suficiente espacio.",
                        f"Disco: {post_disk}% | Inodos: {post_inodes}%",
                    )
                continue

            # 2. ACCIÓN DETERMINISTA: Servicios críticos detenidos -> systemctl restart
            servicios_caidos = [s for s, st in tel["services"].items() if st != "active"]
            if servicios_caidos:
                for svc in servicios_caidos:
                    logging.warning(f"⚠️ [Agatha-SysAdmin] Servicio {svc} en estado {tel['services'][svc]}")
                    callback_notificacion(f"🔄 *[Agatha-SysAdmin] Servicio `{svc}` caído:* Intentando recuperación...")
                    recuperado = reiniciar_servicio_systemd(svc)
                    if recuperado:
                        registrar_memoria_episodica(
                            f"service_down_{svc}",
                            tel,
                            f"restart_service:{svc}",
                            f"Service {svc} was inactive.",
                            "RESOLVED",
                            f"Service {svc} stopped; systemd restart restored active status.",
                        )
                        callback_notificacion(f"🟢 *[Agatha-SysAdmin] Servicio `{svc}` recuperado.*")
                    else:
                        logs_svc = obtener_logs_microshift_ssh(lineas=8)
                        registrar_memoria_episodica(
                            f"service_down_{svc}",
                            tel,
                            f"restart_service:{svc}",
                            f"Service {svc} failed to restart.",
                            "ESCALATED",
                            f"Service {svc} failed restart recovery; escalated to SRE with journal logs.",
                        )
                        callback_escalamiento(
                            f"🔥 *[Agatha-SysAdmin] Fallo crítico en servicio `{svc}`:* No logró arrancar.",
                            logs_svc,
                        )
                continue

            # 3. RESPALDO COGNITIVO (Multivac): CPU alta, RAM alta o Pods degradados
            anomalia_recursos = (tel["cpu"] >= CPU_THRESHOLD) or (tel["mem"] >= MEM_THRESHOLD)
            anomalia_pods = len(tel["unhealthy_pods"]) > 0

            if anomalia_recursos or anomalia_pods:
                trigger = "resource_pressure" if anomalia_recursos else "unhealthy_pods"
                logging.warning(
                    f"⚠️ [Agatha-SysAdmin] Anomalía compleja ({trigger}): "
                    f"CPU={tel['cpu']}% RAM={tel['mem']}% Pods={tel['unhealthy_pods']}"
                )
                contexto = (
                    f"Top processes:\n{tel['top_procs']}\n"
                    f"Unhealthy pods: {tel['unhealthy_pods']}"
                )
                decision = solicitar_remediacion_multivac(trigger, tel, contexto)

                if not decision or decision.get("action") == "escalate":
                    razon = decision.get("reason", "Multivac no disponible o causa raíz incierta.") if decision else "Multivac no responde."
                    ste_sum = decision.get("ste_summary", f"Complex anomaly ({trigger}) escalated to SRE.") if decision else f"LLM offline during {trigger}; escalated to SRE."
                    registrar_memoria_episodica(trigger, tel, "escalate", razon, "ESCALATED", ste_sum)
                    callback_escalamiento(
                        f"🔥 *[Agatha-SysAdmin] Anomalía detectada ({trigger}):*\n_{razon}_",
                        contexto,
                    )
                else:
                    exito = ejecutar_accion_remediatoria(decision, callback_notificacion)
                    outcome = "RESOLVED" if exito else "FAILED"
                    registrar_memoria_episodica(
                        trigger, tel, decision["action"], decision["reason"], outcome, decision["ste_summary"]
                    )
                    if not exito:
                        callback_escalamiento(
                            f"🔥 *[Agatha-SysAdmin] Falló la auto-remediación `{decision['action']}`:*",
                            contexto,
                        )
        finally:
            remediacion_lock.release()


# =====================================================================
# ## 1. Observabilidad: Sentido Arácnido (Stream de Nginx + Orquestación)
# =====================================================================

# [DEMO2] Observabilidad y Concurrencia (SysAdmin + Stream Nginx)
def vision_precognitiva(callback_notificacion, callback_escalamiento, callback_escalamiento_critico):
    if not chequeo_pre_vuelo(callback_notificacion, callback_escalamiento_critico):
        logging.critical("🛑 [Agatha] Falla de Pre-vuelo. Entrando en modo de hibernación. ChatOps permanece activo.")
        estado_actual["status"] = "Hibernando por falla crítica en arranque."
        while True:
            time.sleep(60)

    # Arrancamos el hilo de SysAdmin proactivo en paralelo
    hilo_sysadmin = threading.Thread(
        target=bucle_sysadmin,
        args=(callback_notificacion, callback_escalamiento),
        daemon=True,
    )
    hilo_sysadmin.start()

    cmd = ["oc", "--kubeconfig", KUBECONFIG_PATH, "logs", TARGET_FRONTEND, "-f", "--tail=0"]
    ultimo_error = time.time()

    while True:
        estado_actual["status"] = "Sumergida en el tanque. Monitoreo activo (Red + SysAdmin)."
        logging.info(f"🔮 [Agatha] Sumergida en el tanque. Nivel de amenaza actual: {estado_actual['nivel_amenaza']}")

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            time.sleep(2)
        except FileNotFoundError:
            sys.exit(1)

        error_count = 0
        threshold = 3
        historial_errores = []

        try:
            for line in iter(process.stdout.readline, ""):
                if not line or "favicon.ico" in line:
                    continue

                # Enfriamiento limpio (resetea errores huérfanos incluso en nivel 0)
                if time.time() - ultimo_error > 60:
                    if estado_actual["nivel_amenaza"] > 0:
                        logging.info("📉 [Agatha] Clúster estable. Reduciendo nivel de amenaza a 0.")
                        estado_actual["nivel_amenaza"] = 0
                        estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
                    error_count = 0
                    historial_errores.clear()

                if re.search(r" (404|499|50[234]) ", line):
                    ultimo_error = time.time()
                    error_count += 1
                    historial_errores.append(line.strip())

                    logging.warning(f"⚠️ [Agatha] Visión de anomalía detectada ({error_count}/{threshold}): {line.strip()}")

                    if error_count >= threshold:
                        with remediacion_lock:
                            estado_actual["nivel_amenaza"] += 1
                            estado_actual["status"] = "Anomalía detectada. Analizando patrones hostiles."

                            if estado_actual["nivel_amenaza"] == 1:
                                estado_actual["status"] = "Auto-Remediación en curso (Multivac)."
                                callback_notificacion(
                                    "🚨 *¡PRE-CRIMEN DETECTADO (Nivel 1)!*\n"
                                    "Anomalía de red sostenida. Consultando telemetría y a Multivac..."
                                )
                                tel, _ = recolectar_telemetria_sysadmin()
                                contexto = "\n".join(historial_errores[-5:])
                                decision = solicitar_remediacion_multivac("http_error_burst", tel or {}, contexto)

                                if decision and decision.get("action") != "escalate":
                                    exito = ejecutar_accion_remediatoria(decision, callback_notificacion)
                                    outcome = "RESOLVED" if exito else "FAILED"
                                    registrar_memoria_episodica(
                                        "http_error_burst",
                                        tel or {},
                                        decision["action"],
                                        decision["reason"],
                                        outcome,
                                        decision["ste_summary"],
                                    )
                                    if not exito:
                                        callback_notificacion("❌ Fallo al aplicar la remediación propuesta.")
                                else:
                                    razon = decision.get("reason", "Multivac no respondió.") if decision else "Multivac offline."
                                    registrar_memoria_episodica(
                                        "http_error_burst",
                                        tel or {},
                                        "escalate",
                                        razon,
                                        "ESCALATED",
                                        "HTTP error burst exceeded safe automated actions; escalated to SRE.",
                                    )
                                    callback_escalamiento(
                                        f"🔥 *Escalamiento inmediato (Nivel 2):* _{razon}_",
                                        contexto,
                                    )

                                logging.info("⏳ [Agatha] Periodo de gracia (30s)...")
                                estado_actual["status"] = "Periodo de gracia tras remediación (30s)."
                                process.kill()
                                process.wait()
                                time.sleep(30)
                                break

# ## 3. Guardrails: El Freno de Emergencia.
# Límite ético de la IA: Si el fuego no cede tras la remediación,
# pausa la automatización y cede el control al humano (Nivel 2).

                            # [DEMO3] Guardrails y Memoria Episódica (Nivel 2)
                            else:
                                estado_actual["status"] = "Ataque sostenido. Control cedido al usuario (Nivel 2)."
                                contexto_ataque = "\n".join(historial_errores[-3:])
                                registrar_memoria_episodica(
                                    "sustained_attack_level2",
                                    estado_actual.get("ultima_telemetria", {}),
                                    "escalate",
                                    "Anomaly persisted after Level 1 grace period.",
                                    "ESCALATED",
                                    "Sustained HTTP errors survived Level 1 remediation; control transferred to SRE.",
                                )
                                callback_escalamiento(
                                    "🔥 *¡ATAQUE EXPONENCIAL (Nivel 2)!*\n"
                                    "La anomalía persiste tras la auto-remediación. La IA se detiene para evitar daños. "
                                    "¡Se requiere Segunda Fundación!",
                                    contexto_ataque,
                                )
                                logging.critical("🛑 [Agatha] Ataque sostenido. Cediendo control al usuario. Pausa táctica de 60s...")
                                process.kill()
                                process.wait()
                                time.sleep(60)
                                break

        except KeyboardInterrupt:
            process.kill()
            sys.exit(0)

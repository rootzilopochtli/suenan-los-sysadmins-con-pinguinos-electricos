"""
Autor: Alex Callejas (@rootzilopochtli)
Proyecto: PositronicOps
Descripción: Agatha - Visión Precognitiva y Auto-Remediación
"""
import subprocess
import time
import re
import sys
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler("precogs_audit.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

MULTIVAC_URL = "http://localhost:11434/api/generate"

estado_actual = {
    "nivel_amenaza": 0,
    "status": "Iniciando diagnóstico..."
}

TARGET_BACKEND = os.getenv("TARGET_BACKEND", "deployment/gaia-backend")
TARGET_NAMESPACE = os.getenv("TARGET_NAMESPACE", "default")
KUBECONFIG_PATH = os.path.expanduser(os.getenv("KUBECONFIG_PATH", ""))

def consultar_estado():
    amenaza = estado_actual["nivel_amenaza"]
    status = estado_actual["status"]

    if amenaza == 0:
        icono = "🟢"
    elif amenaza == 1:
        icono = "🟡"
    else:
        icono = "🔴"

    return f"{icono} *Visión Precognitiva (Agatha)*\n\n*Nivel de Amenaza:* {amenaza}\n*Estado:* {status}"

def solicitar_remediacion_multivac(contexto_errores):
    logging.info("🧠 [Agatha] Contactando a Multivac...")
    prompt = f"""
    Eres Multivac, un agente de infraestructura. El sistema está bajo ataque.
    Analiza estos errores: {contexto_errores}.
    Responde ÚNICAMENTE con el comando 'oc scale' necesario para escalar {TARGET_BACKEND} a 3 réplicas en el namespace '{TARGET_NAMESPACE}'.
    No escribas explicaciones, no saludes, no des consejos. Solo el comando.
    """
    payload = {
        "model": "qwen2.5-coder:1.5b",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(MULTIVAC_URL, json=payload, timeout=30)
        response.raise_for_status()
        comando = response.json().get('response', '').strip()
        logging.info(f"🤖 [Multivac] Solución propuesta: {comando}")
        return comando
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ [Error] Multivac no responde: {e}")
        return None

def obtener_logs_microshift_ssh():
    NODE_IP = os.getenv("NODE_IP")
    if not NODE_IP:
        return "Error: NODE_IP no definida en el entorno."

    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_llave = os.path.join(ruta_base, "..", "magrathea", "labkey")

    cmd_ssh = [
        "ssh", "-i", ruta_llave, "-o", "StrictHostKeyChecking=no",
        f"positronic-user@{NODE_IP}",
        "sudo journalctl -u microshift.service -n 5 --no-pager"
    ]
    try:
        resultado = subprocess.run(cmd_ssh, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error extrayendo logs SSH: {e.stderr}"

def verificar_estado_plataforma():
    cmd_nodo = ["oc", "--kubeconfig", KUBECONFIG_PATH, "get", "nodes", "-o", "jsonpath='{.items[0].status.conditions[?(@.type==\"Ready\")].status}'"]
    try:
        res_nodo = subprocess.run(cmd_nodo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        nodo_ready = res_nodo.stdout.strip().replace("'", "")
        if nodo_ready != "True":
            return False, "NodeNotReady"
    except Exception:
         return False, "Error validando nodo"

    cmd_deploy = [
        "oc", "--kubeconfig", KUBECONFIG_PATH,
        "get", TARGET_BACKEND,
        "-n", TARGET_NAMESPACE,
        "-o", "jsonpath='{.status.readyReplicas}'"
    ]
    try:
        res_deploy = subprocess.run(cmd_deploy, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        replicas = res_deploy.stdout.strip().replace("'", "")
        if replicas and int(replicas) > 0:
            return True, "OK"
        else:
            return False, "ReplicasZero"
    except Exception:
        return False, "ErrorDeploy"

def verificar_espacio_disco():
    NODE_IP = os.getenv("NODE_IP")
    if not NODE_IP:
        return False, "N/A"

    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_llave = os.path.join(ruta_base, "..", "magrathea", "labkey")

    cmd_df = [
        "ssh", "-i", ruta_llave, "-o", "StrictHostKeyChecking=no",
        f"positronic-user@{NODE_IP}",
        "df -h / | tail -1 | awk '{print $5}' | sed 's/%//'"
    ]
    try:
        resultado = subprocess.run(cmd_df, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        uso_porcentaje = int(resultado.stdout.strip())
        return (uso_porcentaje >= 95), uso_porcentaje
    except Exception:
        return False, "N/A"

def chequeo_pre_vuelo(callback_notificacion, callback_escalamiento_critico):
    estado_actual["status"] = "Verificando estado de la plataforma..."
    logging.info("🛫 [Agatha] Iniciando pre-vuelo...")

    max_intentos = 10
    intento_actual = 1

    while intento_actual <= max_intentos:
        plataforma_lista, razon_falla = verificar_estado_plataforma()

        if plataforma_lista:
             logging.info("✅ Pre-vuelo exitoso. Plataforma estable.")
             estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
             return True

        if razon_falla == "NodeNotReady" and intento_actual < max_intentos:
             logging.warning(f"⏳ [Agatha] El nodo no está listo (Intento {intento_actual}/{max_intentos}). Esperando estabilización CNI...")
             estado_actual["status"] = f"Esperando estabilización de red ({intento_actual}/{max_intentos})..."
             time.sleep(30)
             intento_actual += 1
             continue
        break

    logging.warning(f"⚠️ [Agatha] Falla confirmada en arranque: {razon_falla}")

    disco_lleno, porcentaje = verificar_espacio_disco()

    if disco_lleno:
        msg_marvin = f"🚨 *[Agatha] Alerta de Almacenamiento ({porcentaje}%):* Invocando a Marvin para purga de emergencia..."
        logging.info(msg_marvin)
        callback_notificacion(msg_marvin)

        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_marvin = os.path.join(ruta_base, "..", "magrathea", "scripts", "05-maintenance-marvin.sh")
        try:
            subprocess.run(["bash", ruta_marvin], check=False)
        except Exception as e:
            logging.error(f"Error invocando a Marvin: {e}")

        time.sleep(15)

        plataforma_lista, razon_falla = verificar_estado_plataforma()
        if plataforma_lista:
             msg_ok = "🟢 *Remediación exitosa:* Marvin estabilizó el almacenamiento y la plataforma levantó."
             logging.info(msg_ok)
             callback_notificacion(msg_ok)
             estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
             return True

    if razon_falla == "ReplicasZero":
        msg_restart = "🔄 *[Agatha] Desincronización detectada:* Forzando reinicio del backend para reenganchar con la base de datos..."
        logging.info(msg_restart)
        callback_notificacion(msg_restart)

        try:
            subprocess.run(["oc", "--kubeconfig", KUBECONFIG_PATH, "rollout", "restart", TARGET_BACKEND, "-n", TARGET_NAMESPACE], check=True)
            time.sleep(20)

            plataforma_lista, _ = verificar_estado_plataforma()
            if plataforma_lista:
                msg_ok = "🟢 *Remediación exitosa:* El backend fue reiniciado y la plataforma está estable."
                logging.info(msg_ok)
                callback_notificacion(msg_ok)
                estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
                return True
        except Exception as e:
            logging.error(f"Fallo al intentar auto-remediar el rollout: {e}")

    estado_actual["status"] = "Falla crítica detectada en el arranque."

    contexto = ""
    if razon_falla == "NodeNotReady":
        contexto = "El nodo de MicroShift reporta estado NotReady tras 5 minutos. Falla crítica en inicialización de red."
    elif razon_falla == "ReplicasZero":
        contexto = f"El despliegue `{TARGET_BACKEND}` no cuenta con réplicas operativas tras intentar un reinicio automático."
    else:
        contexto = "Falla indeterminada en la inicialización."

    callback_escalamiento_critico(contexto)
    return False

def vision_precognitiva(callback_notificacion, callback_escalamiento, callback_escalamiento_critico):
    if not chequeo_pre_vuelo(callback_notificacion, callback_escalamiento_critico):
        logging.critical("🛑 [Agatha] Falla de Pre-vuelo. Entrando en modo de hibernación. ChatOps permanece activo para diagnóstico.")
        estado_actual["status"] = "Hibernando por falla crítica en arranque."
        while True:
            time.sleep(60)

    target_frontend = os.getenv("TARGET_FRONTEND", "deployment/gaia-frontend")
    cmd = ["oc", "--kubeconfig", KUBECONFIG_PATH, "logs", target_frontend, "-f", "--tail=0"]
    ultimo_error = time.time()

    while True:
        estado_actual["status"] = "Sumergida en el tanque. Monitoreo pasivo."
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
            for line in iter(process.stdout.readline, ''):
                if not line:
                    continue

                if "favicon.ico" in line:
                    continue

                if time.time() - ultimo_error > 60 and estado_actual["nivel_amenaza"] > 0:
                    logging.info("📉 [Agatha] El clúster se ha mantenido estable. Reduciendo nivel de amenaza a 0.")
                    estado_actual["nivel_amenaza"] = 0
                    estado_actual["status"] = "Sumergida en el tanque. Clúster estable."
                    error_count = 0

                if re.search(r' (404|499|50[234]) ', line):
                    ultimo_error = time.time()
                    error_count += 1
                    historial_errores.append(line.strip())

                    logging.warning(f"⚠️ [Agatha] Visión de anomalía detectada ({error_count}/{threshold}): {line.strip()}")

                    if error_count >= threshold:
                        estado_actual["nivel_amenaza"] += 1
                        estado_actual["status"] = "Anomalía detectada. Analizando patrones hostiles."

                        if estado_actual["nivel_amenaza"] == 1:
                            estado_actual["status"] = "Auto-Remediación en curso (Multivac)."
                            callback_notificacion("🚨 *¡PRE-CRIMEN DETECTADO (Nivel 1)!*\nFalla inicial detectada. Multivac asume el control temporal...")
                            contexto = "\n".join(historial_errores)
                            comando = solicitar_remediacion_multivac(contexto)

                            if comando:
                                comando_limpio = comando.replace("```bash", "").replace("```sh", "").replace("```", "").replace("`", "").strip()
                                for linea_cmd in comando_limpio.split('\n'):
                                    if linea_cmd.strip().startswith('oc'):
                                        comando_limpio = linea_cmd.strip()
                                        break

                                callback_notificacion(f"⚡ *Auto-Remediación*\nEjecutando: `{comando_limpio}`")
                                try:
                                    comando_final = comando_limpio.split()
                                    comando_final.insert(1, "--kubeconfig")
                                    comando_final.insert(2, KUBECONFIG_PATH)
                                    subprocess.run(comando_final, check=True)
                                except subprocess.CalledProcessError:
                                    callback_notificacion("❌ Fallo al aplicar comando.")

                            logging.info("⏳ [Agatha] Periodo de gracia (30s)...")
                            estado_actual["status"] = "Periodo de gracia tras remediación (30s)."
                            process.kill()
                            process.wait()
                            time.sleep(30)
                            break

                        else:
                            estado_actual["status"] = "Ataque sostenido. Control cedido al usuario (Nivel 2)."
                            contexto_ataque = "\n".join(historial_errores[-3:])
                            callback_escalamiento("🔥 *¡ATAQUE EXPONENCIAL (Nivel 2)!*\nLa anomalía persiste tras la auto-remediación. La IA se detiene para evitar daños. ¡Se requiere Segunda Fundación!", contexto_ataque)

                            logging.critical("🛑 [Agatha] Ataque sostenido. Cediendo control al usuario. Pausa táctica de 60s...")
                            process.kill()
                            process.wait()
                            time.sleep(60)
                            break

        except KeyboardInterrupt:
            process.kill()
            sys.exit(0)

import subprocess
import time
import re
import sys
import os
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler("precogs_audit.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

MULTIVAC_URL = "http://localhost:11434/api/generate"

def solicitar_remediacion_multivac(contexto_errores):
    logging.info("🧠 [Agatha] Contactando a Multivac...")
    prompt = f"""
    Eres Multivac, un agente de infraestructura. El sistema está bajo ataque.
    Analiza estos errores: {contexto_errores}.
    Responde ÚNICAMENTE con el comando 'oc scale' necesario para escalar el despliegue 'gaia-test' a 3 réplicas en el namespace 'default'.
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

def vision_precognitiva(callback_notificacion, callback_escalamiento):
    kubeconfig = os.path.expanduser(os.getenv("KUBECONFIG_PATH", ""))
    cmd = ["oc", "--kubeconfig", kubeconfig, "logs", "deployment/gaia-test", "-f", "--tail=0"]

    nivel_amenaza = 0
    ultimo_error = time.time()

    while True:
        logging.info(f"🔮 [Agatha] Sumergida en el tanque. Nivel de amenaza actual: {nivel_amenaza}")

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        except FileNotFoundError:
            sys.exit(1)

        error_count = 0
        threshold = 3
        historial_errores = []

        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    continue

                if time.time() - ultimo_error > 60 and nivel_amenaza > 0:
                    logging.info("📉 [Agatha] El clúster se ha mantenido estable. Reduciendo nivel de amenaza a 0.")
                    nivel_amenaza = 0
                    error_count = 0

                if re.search(r' (404|499|50[234]) ', line):
                    ultimo_error = time.time()
                    error_count += 1
                    historial_errores.append(line.strip())

                    logging.warning(f"⚠️ [Agatha] Visión de anomalía detectada ({error_count}/{threshold}): {line.strip()}")

                    if error_count >= threshold:
                        nivel_amenaza += 1

                        if nivel_amenaza == 1:
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
                                    comando_final.insert(2, kubeconfig)
                                    subprocess.run(comando_final, check=True)
                                except subprocess.CalledProcessError:
                                    callback_notificacion("❌ Fallo al aplicar comando.")

                            logging.info("⏳ [Agatha] Periodo de gracia (30s)...")
                            process.kill()
                            process.wait()
                            time.sleep(30)
                            break

                        else:
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


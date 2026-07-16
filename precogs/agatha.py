import subprocess
import time
import re
import sys
import os
import requests
import json

# URL local donde Multivac (Ollama) está escuchando
MULTIVAC_URL = "http://localhost:11434/api/generate"
# El modelo que pre-cargamos en el aprovisionamiento
MULTIVAC_MODEL = "llama3"

def solicitar_remediacion_multivac(contexto_errores):
    print("🧠 [Agatha] Contactando a Multivac...")

    # Usaremos el endpoint estándar de Ollama /api/generate
    url = "http://localhost:11434/api/generate"

        # Prompt diseñado para obtener una instrucción técnica directa
    prompt = f"""
    Eres Multivac, un agente de infraestructura. El sistema está bajo ataque.
    Analiza estos errores: {contexto_errores}.
    Responde ÚNICAMENTE con el comando 'oc scale' necesario para escalar el despliegue 'gaia-backend' a 5 réplicas en el namespace 'default'.
    No escribas explicaciones, no saludes, no des consejos. Solo el comando.
    """

    payload = {
        "model": "qwen2.5-coder:1.5b",  # <-- EL MODELO CORRECTO QUE VIMOS EN TAGS
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        resultado = response.json()
        # En /api/generate, la respuesta viene en ['response']
        comando = resultado.get('response', '').strip()
        print(f"🤖 [Multivac] Solución propuesta: {comando}")
        return comando
    except requests.exceptions.RequestException as e:
        print(f"❌ [Error] Multivac no responde o configuración incorrecta: {e}")
        return None

def vision_precognitiva():
    DEBUG = False
    print("🔮 [Agatha] Sumergida en el tanque. Iniciando visión precognitiva en la Capa 2 (Gaia Frontend)...")

    if "KUBECONFIG" not in os.environ:
        print("⚠️ [ADVERTENCIA] KUBECONFIG no detectado en las variables de entorno.")

    cmd = ["oc", "logs", "deployment/gaia-frontend", "-f", "--tail=10"]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except FileNotFoundError:
        print("❌ [Error] Comando 'oc' no encontrado.")
        sys.exit(1)

    error_count = 0
    threshold = 5
    historial_errores = [] # Almacenamos las líneas para dárselas de contexto a Multivac

    try:
        print("🟢 [Agatha] Tubería abierta. Esperando primeras líneas del Ingress...")

        while True:
            line = process.stdout.readline()
            if not line:
                print("💀 [Agatha] El flujo de logs se ha cerrado de forma inesperada.")
                break

            if re.search(r' (499|50[234]) ', line):
                error_count += 1
                historial_errores.append(line.strip())
                print(f"⚠️ [Visión] Fragmento de anomalía detectado ({error_count}/{threshold})")

                if error_count >= threshold:
                    print("\n🚨 [CRÍTICO] ¡PRE-CRIMEN DETECTADO! Agatha predice un colapso inminente en el Ingress.")

                    # Convertimos la lista de errores en un string para el prompt
                    contexto = "\n".join(historial_errores)
                    comando = solicitar_remediacion_multivac(contexto)

                    if comando:
                        # Limpiamos el ruido de Markdown
                        comando_limpio = comando.replace("```bash", "").replace("```", "").strip()

                        print(f"⚡ [Auto-Remediación] Ejecutando: {comando_limpio}")
                        try:
                            # Ejecutamos solo la parte limpia
                            subprocess.run(comando_limpio.split(), check=True)
                            print("✅ [Remediación] Escalado aplicado exitosamente.")
                        except subprocess.CalledProcessError as e:
                            print(f"❌ [Error] La remediación falló: {e}")

                    print("\n🔮 [Agatha] Enfriando sistema y reanudando visión...")
                    error_count = 0
                    historial_errores = [] # Limpiamos el historial
                    time.sleep(10) # Damos tiempo a que la remediación surta efecto

            elif DEBUG:
                continue

    except KeyboardInterrupt:
        print("\n🛑 [Agatha] Desconectando de la piscina de pre-crimen. Terminando visión.")
        process.kill()

if __name__ == "__main__":
    vision_precognitiva()

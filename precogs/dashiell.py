import subprocess
import os
from dotenv import load_dotenv

load_dotenv()
KUBECONFIG = os.path.expanduser(os.getenv("KUBECONFIG_PATH", ""))
NODE_IP = os.getenv("NODE_IP", "192.168.122.155")
SSH_KEY = os.path.expanduser(os.getenv("SSH_KEY_PATH", "../magrathea/labkey"))

def generar_barra(porcentaje, longitud=10):
    try:
        p = int(porcentaje.replace('%', ''))
        llenos = int((p / 100) * longitud)
        vacios = longitud - llenos
        return f"[{'█' * llenos}{'░' * vacios}] {p}%"
    except ValueError:
        return f"[❓] {porcentaje}"

def obtener_disco():
    """Consulta vía SSH el porcentaje de uso de la partición raíz del nodo Edge."""
    if not NODE_IP:
        return "[❓] N/A"
    try:
        cmd = [
            "ssh", "-q", "-n", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
            "-o", "GSSAPIAuthentication=no", "-o", "ConnectTimeout=5",
            f"positronic-user@{NODE_IP}", "df -h /"
        ]
        # Ejecuta el comando crudo y separa la salida por líneas
        resultado = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip().split('\n')

        # Aísla la última línea y extrae la columna que contiene el símbolo '%'
        porcentaje = [item for item in resultado[-1].split() if '%' in item][0]

        return generar_barra(porcentaje)
    except Exception as e:
        # Mostramos el error real en Telegram en lugar de un "Err" genérico
        return f"[❓] Err: {e}"

def obtener_rendimiento():
    reporte = "📈 *Rendimiento del Clúster (MicroShift)*\n\n*Infraestructura Base:*\n"

    # Extraemos el disco primero para que no dependa de las métricas de K8s
    disco_bar = obtener_disco()

    # Bloque aislado para CPU/RAM de los nodos
    try:
        out_nodos = subprocess.run(
            ["oc", "--kubeconfig", KUBECONFIG, "adm", "top", "nodes", "--no-headers"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split('\n')

        for linea in out_nodos:
            if not linea: continue
            partes = linea.split()
            nombre = partes[0]
            cpu_bar = generar_barra(partes[2])
            mem_bar = generar_barra(partes[4])
            reporte += f"🖥️ `{nombre}`\n  🧠 CPU:   `{cpu_bar}`\n  💾 RAM:   `{mem_bar}`\n  💽 DISCO: `{disco_bar}`\n\n"

    except subprocess.CalledProcessError as e:
        reporte += f"🖥️ `{NODE_IP}`\n  🧠 CPU:   `[❓] N/A`\n  💾 RAM:   `[❓] N/A`\n  💽 DISCO: `{disco_bar}`\n"
        reporte += f"⚠️ _Métricas de CPU/RAM aún no disponibles: {e.stderr.strip()}_ \n\n"

    # Bloque aislado para CPU/RAM de los pods
    reporte += "*Despliegues (Namespace: default):*\n"
    try:
        out_pods = subprocess.run(
            ["oc", "--kubeconfig", KUBECONFIG, "adm", "top", "pods", "-n", "default", "--no-headers"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split('\n')

        for linea in out_pods:
            if not linea: continue
            partes = linea.split()
            nombre = partes[0]
            cpu = partes[1]
            mem = partes[2]
            reporte += f"📦 `{nombre}`\n  ⚙️ CPU: `{cpu}` | 🗄️ RAM: `{mem}`\n\n"

    except subprocess.CalledProcessError as e:
        reporte += f"⚠️ _Métricas de Pods no disponibles: {e.stderr.strip()}_\n"

    return reporte.strip()

def obtener_estado_pods():
    """Extrae y formatea el estado de los pods (Gaia) con semáforos visuales."""
    try:
        out_pods = subprocess.run(
            ["oc", "--kubeconfig", KUBECONFIG, "get", "pods", "-n", "default", "--no-headers"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split('\n')

        if not out_pods or out_pods == ['']:
            return "📭 No hay despliegues activos en el namespace default."

        reporte = "📊 *Estado Actual de Despliegues (Gaia)*\n\n"
        for linea in out_pods:
            if not linea: continue
            partes = linea.split()
            nombre = partes[0]
            ready = partes[1]
            status = partes[2]
            restarts = partes[3]
            age = partes[4]

            icono = "🟢" if status == "Running" else "🟡" if status in ["Pending", "ContainerCreating"] else "🔴"

            reporte += f"📦 `{nombre}`\n"
            reporte += f"  {icono} *Estado:* `{status}` | 🔄 *Restarts:* `{restarts}`\n"
            reporte += f"  ⏱️ *Uptime:* `{age}` | 🚦 *Ready:* `{ready}`\n\n"

        return reporte.strip()

    except subprocess.CalledProcessError as e:
        return f"❌ [Dashiell] Falla al consultar el clúster:\n```text\n{e.stderr}\n```"
    except FileNotFoundError:
        return "❌ [Dashiell] Comando 'oc' no encontrado."

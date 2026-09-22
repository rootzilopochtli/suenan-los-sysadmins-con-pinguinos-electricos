import subprocess
import os
from dotenv import load_dotenv

load_dotenv()
KUBECONFIG = os.path.expanduser(os.getenv("KUBECONFIG_PATH", ""))
NODE_IP = os.getenv("NODE_IP", "")
SSH_KEY = os.path.expanduser(os.getenv("SSH_KEY_PATH", "../magrathea/labkey"))

def generar_barra(porcentaje, longitud=10):
    try:
        p = int(porcentaje.replace('%', ''))
        llenos = int((p / 100) * longitud)
        vacios = longitud - llenos
        return f"[{'█' * llenos}{'░' * vacios}] {p}%"
    except ValueError:
        return "[❓] N/A"

def obtener_disco():
    """Consulta vía SSH el porcentaje de uso de la partición raíz del nodo Edge."""
    if not NODE_IP:
        return "[❓] N/A"
    try:
        cmd = [
            "ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
            f"positronic-user@{NODE_IP}", "df -h / | awk 'NR==2 {print $5}'"
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
        return generar_barra(out)
    except Exception:
        return "[❓] Err"

def obtener_rendimiento():
    try:
        out_nodos = subprocess.run(
            ["oc", "--kubeconfig", KUBECONFIG, "adm", "top", "nodes", "--no-headers"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split('\n')

        reporte = "📈 *Rendimiento del Clúster (MicroShift)*\n\n*Infraestructura Base:*\n"
        for linea in out_nodos:
            if not linea: continue
            partes = linea.split()
            nombre = partes[0]  # FQDN completo preservado
            cpu_bar = generar_barra(partes[2])
            mem_bar = generar_barra(partes[4])
            disco_bar = obtener_disco()

            reporte += f"🖥️ `{nombre}`\n  🧠 CPU:   `{cpu_bar}`\n  💾 RAM:   `{mem_bar}`\n  💽 DISCO: `{disco_bar}`\n\n"

        out_pods = subprocess.run(
            ["oc", "--kubeconfig", KUBECONFIG, "adm", "top", "pods", "-n", "default", "--no-headers"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split('\n')

        reporte += "*Despliegues (Namespace: default):*\n"
        for linea in out_pods:
            if not linea: continue
            partes = linea.split()
            nombre = partes[0]
            cpu = partes[1]
            mem = partes[2]
            reporte += f"📦 `{nombre}`\n  ⚙️ CPU: `{cpu}` | 🗄️ RAM: `{mem}`\n\n"

        return reporte.strip()
    except Exception as e:
        return f"❌ [Dashiell] Interferencia en la telemetría: {e}"

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

            # Inyección de observabilidad visual
            icono = "🟢" if status == "Running" else "🟡" if status in ["Pending", "ContainerCreating"] else "🔴"

            reporte += f"📦 `{nombre}`\n"
            reporte += f"  {icono} *Estado:* `{status}` | 🔄 *Restarts:* `{restarts}`\n"
            reporte += f"  ⏱️ *Uptime:* `{age}` | 🚦 *Ready:* `{ready}`\n\n"

        return reporte.strip()

    except subprocess.CalledProcessError as e:
        return f"❌ [Dashiell] Falla al consultar el clúster:\n```text\n{e.stderr}\n```"
    except FileNotFoundError:
        return "❌ [Dashiell] Comando 'oc' no encontrado."


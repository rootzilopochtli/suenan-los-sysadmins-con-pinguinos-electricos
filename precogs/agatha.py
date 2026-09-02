import os
import time
import threading
import telebot
from telebot import types
import subprocess
import smtplib
from email.mime.text import MIMEText
import random
import logging
from dotenv import load_dotenv
import agatha as agatha

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
KUBECONFIG = os.path.expanduser(os.getenv("KUBECONFIG_PATH", ""))

# Credenciales SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

bot = telebot.TeleBot(TOKEN)
estado_incidentes = {}

def enviar_alerta(mensaje):
    bot.send_message(ADMIN_CHAT_ID, mensaje, parse_mode="Markdown")

def enviar_reporte_ejecutivo(accion, contexto, downtime):
    if not SMTP_PASSWORD:
        return

    asunto = "🟢 REPORTE DE INCIDENTE: MicroShift Edge (Resuelto)"
    cuerpo = f"""Estimados,

Se informa que se detectó y contuvo exitosamente un incidente crítico (Nivel 2) en el clúster Positronic-node.

Detalles de la Afectación:
- Objetivo: gaia-test
- Tiempo total de degradación (Nivel 2): {downtime:.2f} segundos
- Evidencia del log: {contexto}

Acciones Correctivas:
El ataque superó las capacidades de remediación autónoma (Multivac). El Site Reliability Engineer en turno tomó el control de la infraestructura y aplicó la siguiente directiva manual: {accion}.

El sistema opera actualmente con normalidad. No se requiere acción adicional.

Saludos,
PositronicOps AIOps Team
"""
    msg = MIMEText(cuerpo, 'plain')
    msg['From'] = SMTP_USER
    msg['To'] = ADMIN_EMAIL
    msg['Subject'] = asunto

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logging.info("📧 [Temple] Reporte ejecutivo despachado por correo.")
    except Exception as e:
        logging.error(f"❌ [Temple] Fallo al enviar el correo: {e}")

def escalar_humano(mensaje, contexto):
    estado_incidentes[ADMIN_CHAT_ID] = {"inicio": time.time(), "contexto": contexto}
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_ip = types.InlineKeyboardButton("🚫 Bloquear IP (NetworkPolicy)", callback_data="bloquear_ip")
    btn_pod = types.InlineKeyboardButton("🔄 Reiniciar gaia-test", callback_data="reiniciar_pod")
    btn_abortar = types.InlineKeyboardButton("❌ Ignorar", callback_data="abortar")
    markup.add(btn_ip, btn_pod, btn_abortar)
    bot.send_message(ADMIN_CHAT_ID, f"{mensaje}\n\n*Últimos registros:*\n`{contexto}`", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def manejar_emergencia(call):
    if str(call.message.chat.id) == ADMIN_CHAT_ID:
        incidente = estado_incidentes.get(ADMIN_CHAT_ID, {"inicio": time.time(), "contexto": "N/A"})
        downtime = time.time() - incidente["inicio"]

        if call.data == "bloquear_ip":
            bot.answer_callback_query(call.id, "Aplicando NetworkPolicy...")
            bot.edit_message_text("🛡️ *Contención Activada:*\nSe simuló el bloqueo de la IP agresora.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
            enviar_reporte_ejecutivo("Aislamiento de red mediante NetworkPolicy", incidente["contexto"], downtime)
        elif call.data == "reiniciar_pod":
            bot.answer_callback_query(call.id, "Reiniciando pods...")
            try:
                subprocess.run(["oc", "--kubeconfig", KUBECONFIG, "rollout", "restart", "deployment/gaia-test", "-n", "default"], check=True)
                bot.edit_message_text("🔄 *Contención Activada:*\nDespliegue `gaia-test` reiniciado exitosamente.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
                enviar_reporte_ejecutivo("Reinicio en caliente del despliegue (Rollout Restart)", incidente["contexto"], downtime)
            except Exception:
                bot.send_message(ADMIN_CHAT_ID, "❌ Fallo al reiniciar el servicio.")
        elif call.data == "abortar":
            bot.answer_callback_query(call.id, "Operación ignorada.")
            bot.edit_message_text("👀 *Alerta Ignorada:*\nEl clúster seguirá monitoreando en segundo plano.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['ping'])
def send_ping(message):
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "¡Pong! 🏓 Sistemas en línea.")

@bot.message_handler(commands=['perf'])
def cmd_perf(message):
    if str(message.chat.id) == ADMIN_CHAT_ID:
        msg_temp = bot.reply_to(message, "⚙️ [Arthur] Extrayendo telemetría de MicroShift...")
        try:
            nodos = subprocess.run(["oc", "--kubeconfig", KUBECONFIG, "adm", "top", "nodes"], capture_output=True, text=True, check=True).stdout
            pods = subprocess.run(["oc", "--kubeconfig", KUBECONFIG, "adm", "top", "pods", "-n", "default"], capture_output=True, text=True, check=True).stdout
            bot.edit_message_text(f"📈 *Rendimiento del Clúster:*\n\n*Nodos:*\n```text\n{nodos}```\n*Pods (default):*\n```text\n{pods}```", chat_id=message.chat.id, message_id=msg_temp.message_id, parse_mode="Markdown")
        except Exception:
            bot.edit_message_text("❌ [Arthur] Falla al extraer métricas. ¿Está desplegado el metrics-server?", chat_id=message.chat.id, message_id=msg_temp.message_id)

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Arthur: Consulta el estado en vivo de los pods del clúster."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        msg_temp = bot.reply_to(message, "🔍 [Arthur] Analizando la línea temporal del clúster...")
        try:
            resultado = subprocess.run(["oc", "--kubeconfig", KUBECONFIG, "get", "pods", "-n", "default"], capture_output=True, text=True, check=True)
            bot.edit_message_text(f"📊 *Estado Actual (Gaia):*\n```text\n{resultado.stdout}\n```", chat_id=message.chat.id, message_id=msg_temp.message_id, parse_mode="Markdown")
        except subprocess.CalledProcessError as e:
            bot.edit_message_text(f"❌ [Arthur] Falla al consultar el clúster:\n```text\n{e.stderr}\n```", chat_id=message.chat.id, message_id=msg_temp.message_id, parse_mode="Markdown")
        except FileNotFoundError:
            bot.edit_message_text("❌ [Arthur] Comando 'oc' no encontrado. ¿Estoy ejecutándome en el nodo correcto?", chat_id=message.chat.id, message_id=msg_temp.message_id)

@bot.message_handler(commands=['bofh'])
def cmd_bofh(message):
    """Easter Egg explícito."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        excusa = "Falla catastrófica por interferencia de taquiones en el buffer de Nginx. Manda un correo a soporte y encomiéndate a los dioses del kernel."
        bot.reply_to(message, f"☠️ *[BOFH]*\n{excusa}\n\n_RTFM._", parse_mode="Markdown")

@bot.message_handler(commands=['reboot', 'reset', 'poweroff', 'halt', 'shutdown'])
def cmd_troll_system(message):
    """Atrapa intentos de apagar el sistema y se burla del usuario."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "🤡 ¡Jajaja! No lo creo mai.")

@bot.message_handler(func=lambda message: True)
def bofh_catch_all(message):
    """Atrapa cualquier comando o texto no reconocido con actitud BOFH."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        respuestas_bofh = [
            "🛑 Exceso de baneados.",
            "🫩 Negativo. El bot está apagado.",
            "⚠️  Te van a banear...",
            "🛡️ Exceso de dictadura.",
            f"¿`{message.text}`? Mis registros indican un problema en la Capa 8.",
            f"Comando `{message.text}` no reconocido. Redirigiendo petición a `/dev/null`.",
            f"¿`{message.text}`? Interesante intento. Mis registros indican que tienes un error de Capa 8.",
            "Negativo. Multivac se está riendo de tu sintaxis en binario 😅",
            "Ese comando no existe en esta línea temporal. Intenta de nuevo o *RTFM*."
        ]
        logging.warning(f"Intento de comando BOFH interceptado: {message.text}")
        bot.reply_to(message, random.choice(respuestas_bofh), parse_mode="Markdown")

if __name__ == "__main__":
    logging.info("🏛️ [Temple] Energizando núcleo. Iniciando ecosistema...")

    hilo_agatha = threading.Thread(target=agatha.vision_precognitiva, args=(enviar_alerta, escalar_humano), daemon=True)
    hilo_agatha.start()

    logging.info("🤖 [Andrew/Arthur] Modulando frecuencias. A la espera de directivas...")
    bot.infinity_polling()


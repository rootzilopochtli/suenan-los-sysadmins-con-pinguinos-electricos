import logging
import os
import random
import smtplib
import subprocess
import threading
import time
from collections import Counter
from email.mime.text import MIMEText

import telebot
from dotenv import load_dotenv
from telebot import types

import agatha
import arthur
import dashiell

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
        msg_temp = bot.reply_to(message, "⚙️ [Dashiell] Extrayendo telemetría de MicroShift...")
        rendimiento = dashiell.obtener_rendimiento()
        bot.edit_message_text(
            rendimiento,
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Consulta el estado en vivo de los pods del clúster."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        msg_temp = bot.reply_to(message, "🔍 [Dashiell] Analizando la línea temporal del clúster...")
        estado = dashiell.obtener_estado_pods()
        bot.edit_message_text(
            estado,
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['auditoria'])
def cmd_auditoria(message):
    """Arthur: Inferencia histórica de logs vía RAG."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        # Registramos formalmente el evento en la bitácora para sincronizar el timestamp del cursor
        logging.info("🧠 [Arthur] Auditoría manual solicitada por el Administrador.")

        msg_temp = bot.reply_to(message, "🧠 [Arthur] Consultando la memoria histórica y procesando inferencia...")

        analisis = arthur.analizar_historial()

        bot.edit_message_text(
            f"📜 *Reporte Cognitivo (Arthur):*\n\n{analisis}",
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['agatha'])
def cmd_agatha(message):
    """Consulta el nivel de amenaza actual y estado operativo."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        estado = agatha.consultar_estado()
        bot.reply_to(message, estado, parse_mode="Markdown")

@bot.message_handler(commands=['toalla', 'towel'])
def cmd_hitchhiker(message):
    """Easter Egg: El sentido de la vida, el universo y todo lo demás."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "🌌 *42*\n\n_(Y no olvides tu toalla)_", parse_mode="Markdown")

@bot.message_handler(commands=['?', 'help', 'ayuda'])
def cmd_help(message):
    """Despliega la lista de comandos válidos."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        menu = (
            "🤖 *Directivas del Sistema PositronicOps*\n\n"
            "📊 *Observabilidad (Dashiell)*\n"
            "• `/status` - Estado en vivo de contenedores (Gaia)\n"
            "• `/perf` - Telemetría de consumo (CPU/RAM)\n\n"
            "🧠 *Cognición (Arthur & Agatha)*\n"
            "• `/agatha` - Nivel de amenaza (Pre-crimen)\n"
            "• `/auditoria` - Análisis RAG de la línea temporal\n\n"
            "🛡️ *Bitácoras de Seguridad*\n"
            "• `/resumen` - Dashboard ejecutivo de defensas\n"
            "• `/nivel1` - Registro de auto-remediaciones\n"
            "• `/baneados` - Muro de la Vergüenza (BOFH)\n\n"
            "⚙️ *Sistema*\n"
            "• `/ping` - Verificación de enlace\n"
            "• `/?` - Muestra este manual de operaciones"
        )
        bot.reply_to(message, menu, parse_mode="Markdown")

@bot.message_handler(commands=['nivel1'])
def cmd_nivel1(message):
    """Bitácora de Auto-remediación: Eventos de Nivel 1 contenidos con Traductor Táctico."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        log_file = "precogs_audit.log"

        if not os.path.exists(log_file):
            bot.reply_to(message, "📭 La bitácora está vacía. Cero anomalías detectadas.")
            return

        def traducir_accion(comando):
            """Mapea comandos crudos a explicaciones ejecutivas."""
            cmd = comando.lower()
            if "scale deployment" in cmd:
                return "Escalamiento automático de réplicas para absorber pico de tráfico."
            elif "networkpolicy" in cmd or "deny" in cmd:
                return "Aislamiento de red activado (Bloqueo de origen sospechoso)."
            elif "rollout restart" in cmd:
                return "Reinicio preventivo de pods para purgar conexiones colgadas."
            return "Contención táctica genérica aplicada."

        incidentes = []
        with open(log_file, "r") as f:
            lineas = f.readlines()

        for i, linea in enumerate(lineas):
            if "Solución propuesta:" in linea:
                try:
                    timestamp = linea.split(" - ")[0].split(",")[0].strip()

                    if i + 1 < len(lineas):
                        accion = lineas[i+1].strip()
                        accion = accion.replace("'", "").replace('"', "").replace('`', '').replace('*', '').replace('_', '')

                        # Generamos la "carnita"
                        explicacion = traducir_accion(accion)

                        incidentes.append((timestamp, accion, explicacion))
                except Exception:
                    continue

        if not incidentes:
            bot.reply_to(message, "✅ Clúster pacífico. No se han registrado auto-remediaciones de Nivel 1.")
            return

        total_incidentes = len(incidentes)
        ultimos_incidentes = incidentes[-5:]

        reporte = (
            f"⚡ *Bitácora de Auto-Remediación (Nivel 1)*\n"
            f"📊 *Total histórico:* `{total_incidentes}` contenciones\n"
            f"_Mostrando los 5 eventos más recientes:_\n\n"
        )

        for ts, accion, explicacion in ultimos_incidentes:
            reporte += (
                f"• 🕒 `{ts}`\n"
                f"  🧠 *Contexto:* {explicacion}\n"
                f"  🛠️ *Comando:* `{accion}`\n\n"
            )

        bot.reply_to(message, reporte.strip(), parse_mode="Markdown")

@bot.message_handler(commands=['baneados'])
def cmd_muro_vergüenza(message):
    """Muro de la Vergüenza: Conteo de comandos inválidos interceptados (Determinista)."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        log_file = "precogs_audit.log"

        if not os.path.exists(log_file):
            bot.reply_to(message, "📭 La bitácora está vacía. Cero intentos de sabotaje.")
            return

        comandos_interceptados = []
        with open(log_file, "r") as f:
            for linea in f:
                if "Intento de comando BOFH interceptado:" in linea:
                    comando = linea.split("interceptado: ")[-1].strip()
                    comandos_interceptados.append(comando)

        if not comandos_interceptados:
            bot.reply_to(message, "🛡️ Sistema invicto. No se han registrado comandos BOFH.")
            return

        conteo = Counter(comandos_interceptados)

        reporte = "🛡️ *Muro de la Vergüenza*\n_Comandos no autorizados interceptados_\n\n"
        for cmd, freq in conteo.most_common(10):
            reporte += f"• `{cmd}` : {freq} intento(s)\n"

        bot.reply_to(message, reporte, parse_mode="Markdown")

@bot.message_handler(commands=['resumen'])
def cmd_resumen(message):
    """Dashboard Ejecutivo: Resumen global de operaciones y seguridad (Determinista)."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        log_file = "precogs_audit.log"

        if not os.path.exists(log_file):
            bot.reply_to(message, "📭 Infraestructura en blanco. No hay datos de telemetría registrados.")
            return

        bofh_count = 0
        nivel1_count = 0

        with open(log_file, "r") as f:
            for linea in f:
                if "Intento de comando BOFH interceptado:" in linea:
                    bofh_count += 1
                elif "Solución propuesta:" in linea:
                    nivel1_count += 1

        reporte = (
            "📊 *Dashboard Ejecutivo de PositronicOps*\n"
            "_Estado global de defensas automatizadas_\n\n"
            f"🛡️ *Escudos BOFH:* `{bofh_count}` bloqueos de usuario\n"
            f"⚡ *Pre-crímenes Nivel 1:* `{nivel1_count}` auto-remediaciones aplicadas\n\n"
            "🟢 El clúster opera dentro de los parámetros esperados."
        )

        bot.reply_to(message, reporte, parse_mode="Markdown")

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

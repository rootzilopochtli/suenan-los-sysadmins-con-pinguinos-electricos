"""
Autor: Alex Callejas (@rootzilopochtli)
Proyecto: PositronicOps
Version 2.0: CentOS release
Descripción: Temple - Orquestador Central y API Gateway de Telegram
"""
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "precogs_audit.log")

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
KUBECONFIG = os.path.expanduser(os.getenv("KUBECONFIG_PATH", ""))

# --- VARIABLES DE ENTORNO DINÁMICAS ---
TARGET_BACKEND = os.getenv("TARGET_BACKEND", "deployment/gaia-backend")
TARGET_NAMESPACE = os.getenv("TARGET_NAMESPACE", "default")
NODE_IP = os.getenv("NODE_IP", "192.168.122.32")

# Credenciales SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

bot = telebot.TeleBot(TOKEN)
estado_incidentes = {}


def limpiar_bloque_codigo(texto, max_len=900):
    """Sanitiza texto crudo para evitar errores 400 en bloques Markdown de Telegram."""
    limpio = str(texto).replace("`", "'").strip()
    if len(limpio) > max_len:
        limpio = limpio[:max_len] + "\n... [truncado]"
    return limpio


def enviar_alerta(mensaje):
    """Envía notificaciones asíncronas de Agatha con fallback a texto plano."""
    try:
        bot.send_message(ADMIN_CHAT_ID, mensaje, parse_mode="Markdown")
    except Exception as e:
        logging.warning(f"⚠️ [Temple] Fallback a texto plano en alerta: {e}")
        bot.send_message(ADMIN_CHAT_ID, mensaje)


def enviar_reporte_ejecutivo(accion, contexto, downtime):
    if not SMTP_PASSWORD:
        return

    asunto = "🟢 REPORTE DE INCIDENTE: MicroShift Edge (Resuelto)"
    cuerpo = f"""Estimados,

Se informa que se detectó y contuvo exitosamente un incidente crítico (Nivel 2) en el clúster Positronic-node ({NODE_IP}).

Detalles de la Afectación:
- Objetivo: {TARGET_BACKEND} (Namespace: {TARGET_NAMESPACE})
- Tiempo total de degradación (Nivel 2): {downtime:.2f} segundos
- Evidencia del log:
{contexto}

Acciones Correctivas:
El incidente superó las capacidades de remediación autónoma (Nivel 0/1). El Site Reliability Engineer en turno tomó el control de la infraestructura y aplicó la siguiente directiva manual: {accion}.

El sistema opera actualmente con normalidad. No se requiere acción adicional.

Saludos,
PositronicOps AIOps Team
"""
    msg = MIMEText(cuerpo, "plain")
    msg["From"] = SMTP_USER
    msg["To"] = ADMIN_EMAIL
    msg["Subject"] = asunto

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logging.info("📧 [Temple] Reporte ejecutivo despachado por correo.")
    except Exception as e:
        logging.error(f"❌ [Temple] Fallo al enviar el correo: {e}")


def enviar_correo_emergencia(contexto):
    """Despacha un correo de Nivel Crítico cuando el clúster no arranca."""
    if not SMTP_PASSWORD:
        return

    asunto = "🔴 ALERTA CRÍTICA: Fallo de Arranque en MicroShift"
    cuerpo = f"""Estimados,

Se informa de un fallo estructural crítico durante la inicialización del clúster Positronic-node ({NODE_IP}).

Detalles de la Afectación:
- Objetivo: {TARGET_BACKEND} (Namespace: {TARGET_NAMESPACE})
- Estado: PRE-VUELO FALLIDO
- Evidencia del diagnóstico:
{contexto}

Acciones Requeridas:
La plataforma no logró inicializarse o recuperarse autónomamente tras las rutinas de pre-vuelo. Se requiere intervención manual e inmediata del SRE en turno mediante acceso SSH o consola.

Saludos,
PositronicOps AIOps Team
"""
    msg = MIMEText(cuerpo, "plain")
    msg["From"] = SMTP_USER
    msg["To"] = ADMIN_EMAIL
    msg["Subject"] = asunto

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logging.info("📧 [Temple] Alerta de emergencia despachada por correo.")
    except Exception as e:
        logging.error(f"❌ [Temple] Fallo al enviar el correo de emergencia: {e}")


def escalar_humano(mensaje, contexto):
    estado_incidentes[ADMIN_CHAT_ID] = {"inicio": time.time(), "contexto": contexto}
    markup = types.InlineKeyboardMarkup(row_width=1)
    nombre_pod = TARGET_BACKEND.split("/")[-1]
    btn_pod = types.InlineKeyboardButton(f"🔄 Reiniciar {nombre_pod}", callback_data="reiniciar_pod")
    btn_marvin = types.InlineKeyboardButton("🧹 Purgar Disco (Marvin)", callback_data="invocar_marvin")
    btn_ip = types.InlineKeyboardButton("🚫 Bloquear IP (NetworkPolicy)", callback_data="bloquear_ip")
    btn_abortar = types.InlineKeyboardButton("❌ Ignorar", callback_data="abortar")
    markup.add(btn_pod, btn_marvin, btn_ip, btn_abortar)

    ctx_seguro = limpiar_bloque_codigo(contexto)
    cuerpo = f"{mensaje}\n\n*Evidencia:*\n```\n{ctx_seguro}\n```"
    try:
        bot.send_message(ADMIN_CHAT_ID, cuerpo, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        logging.warning(f"⚠️ [Temple] Fallback a texto plano en escalamiento: {e}")
        bot.send_message(ADMIN_CHAT_ID, f"{mensaje}\n\nEvidencia:\n{ctx_seguro}", reply_markup=markup)


def escalar_humano_critico(contexto):
    """Notifica fallos estructurales críticos de pre-vuelo sin botonera."""
    ctx_seguro = limpiar_bloque_codigo(contexto)
    alerta_limpia = (
        "🛑 *ERROR CRÍTICO (Pre-vuelo):* La infraestructura base no logró inicializarse.\n\n"
        f"*Diagnóstico Rápido:*\n```\n{ctx_seguro}\n```\n\n"
        "_ChatOps permanece activo (`/status`, `/perf`, `/marvin`). "
        "Se requiere intervención del SRE si el fallo persiste._"
    )
    try:
        bot.send_message(ADMIN_CHAT_ID, alerta_limpia, parse_mode="Markdown")
    except Exception:
        bot.send_message(ADMIN_CHAT_ID, f"ERROR CRITICO (Pre-vuelo):\n{ctx_seguro}")

    enviar_correo_emergencia(contexto)


@bot.callback_query_handler(func=lambda call: True)
def manejar_emergencia(call):
    if str(call.message.chat.id) != ADMIN_CHAT_ID:
        return

    incidente = estado_incidentes.get(ADMIN_CHAT_ID, {"inicio": time.time(), "contexto": "N/A"})
    downtime = time.time() - incidente["inicio"]

    if call.data == "bloquear_ip":
        bot.answer_callback_query(call.id, "Aplicando NetworkPolicy...")
        bot.edit_message_text(
            "🛡️ *Contención Activada:*\nSe aplicó aislamiento de red contra el origen agresor.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
        )
        agatha.registrar_memoria_episodica(
            "level2_human_intervention",
            agatha.estado_actual.get("ultima_telemetria", {}),
            "apply_network_policy",
            "SRE activated NetworkPolicy containment from Telegram.",
            "RESOLVED",
            "SRE mitigated sustained Level 2 incident using NetworkPolicy isolation.",
        )
        enviar_reporte_ejecutivo("Aislamiento de red mediante NetworkPolicy", incidente["contexto"], downtime)

    elif call.data == "reiniciar_pod":
        bot.answer_callback_query(call.id, "Reiniciando despliegue...")
        try:
            subprocess.run(
                ["oc", "--kubeconfig", KUBECONFIG, "rollout", "restart", TARGET_BACKEND, "-n", TARGET_NAMESPACE],
                check=True,
                timeout=30,
            )
            bot.edit_message_text(
                f"🔄 *Contención Activada:*\nDespliegue `{TARGET_BACKEND}` reiniciado exitosamente.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
            )
            agatha.registrar_memoria_episodica(
                "level2_human_intervention",
                agatha.estado_actual.get("ultima_telemetria", {}),
                "restart_backend",
                "SRE triggered rollout restart from Telegram.",
                "RESOLVED",
                f"SRE restarted {TARGET_BACKEND} in namespace {TARGET_NAMESPACE} to resolve Level 2 incident.",
            )
            enviar_reporte_ejecutivo("Reinicio en caliente del despliegue (Rollout Restart)", incidente["contexto"], downtime)
        except Exception as e:
            logging.error(f"❌ [Temple] Fallo al reiniciar servicio: {e}")
            bot.send_message(ADMIN_CHAT_ID, "❌ Fallo al reiniciar el servicio.")

    elif call.data == "invocar_marvin":
        bot.answer_callback_query(call.id, "Ejecutando a Marvin...")
        bot.edit_message_text(
            "🧹 *Contención en curso:*\nInvocando a Marvin para purga de almacenamiento...",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
        )
        _, disk_antes, _ = agatha.verificar_espacio_disco()
        exito = agatha.invocar_marvin()
        _, disk_despues, inodes_despues = agatha.verificar_espacio_disco()

        outcome = "RESOLVED" if exito else "FAILED"
        agatha.registrar_memoria_episodica(
            "level2_human_marvin",
            {"disk_before": disk_antes, "disk_after": disk_despues, "inodes": inodes_despues},
            "run_marvin",
            "SRE triggered Marvin cleanup from Level 2 escalation.",
            outcome,
            f"SRE executed Marvin from Telegram; root disk changed from {disk_antes} percent to {disk_despues} percent.",
        )
        icono = "🟢" if exito else "⚠️"
        bot.edit_message_text(
            f"{icono} *Mantenimiento de Marvin finalizado:*\n"
            f"Disco: `{disk_antes}%` → `{disk_despues}%` | Inodos: `{inodes_despues}%`",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
        )
        if exito:
            enviar_reporte_ejecutivo("Purga de almacenamiento con Marvin", incidente["contexto"], downtime)

    elif call.data == "abortar":
        bot.answer_callback_query(call.id, "Operación ignorada.")
        bot.edit_message_text(
            "👀 *Alerta Ignorada:*\nEl clúster seguirá monitoreando en segundo plano.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["ping"])
def send_ping(message):
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "¡Pong! 🏓 Sistemas en línea.")


@bot.message_handler(commands=["perf"])
def cmd_perf(message):
    if str(message.chat.id) == ADMIN_CHAT_ID:
        msg_temp = bot.reply_to(message, "⚙️ [Dashiell] Extrayendo telemetría de MicroShift...")
        rendimiento = dashiell.obtener_rendimiento()
        bot.edit_message_text(
            rendimiento,
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["status"])
def cmd_status(message):
    """Consulta el estado en vivo de los pods del clúster."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        msg_temp = bot.reply_to(message, "🔍 [Dashiell] Analizando la línea temporal del clúster...")
        estado = dashiell.obtener_estado_pods()
        bot.edit_message_text(
            estado,
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["agatha"])
def cmd_agatha(message):
    """Consulta el nivel de amenaza actual, estado operativo y último pulso."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        estado = agatha.consultar_estado()
        bot.reply_to(message, estado, parse_mode="Markdown")


@bot.message_handler(commands=["auditoria"])
def cmd_auditoria(message):
    """Arthur: Auditoría incremental sobre memoria episódica y logs."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        logging.info("🧠 [Arthur] Auditoría manual solicitada por el Administrador.")
        msg_temp = bot.reply_to(message, "🧠 [Arthur] Consultando memoria episódica y procesando inferencia...")
        analisis = arthur.analizar_historial()
        bot.edit_message_text(
            f"📜 *Reporte Cognitivo (Arthur):*\n\n{analisis}",
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["rag"])
def cmd_rag(message):
    """Arthur: Consulta RAG interactiva sobre la memoria episódica STE-100."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        partes = message.text.split(maxsplit=1)
        pregunta = partes[1].strip() if len(partes) > 1 else ""
        if not pregunta:
            bot.reply_to(
                message,
                "ℹ️ Uso: `/rag <pregunta>`\nEjemplo: `/rag que paso con el disco?`",
                parse_mode="Markdown",
            )
            return

        msg_temp = bot.reply_to(message, "🧠 [Arthur] Buscando incidentes previos en memoria episódica...")
        respuesta = arthur.consultar_memoria(pregunta)
        bot.edit_message_text(
            respuesta,
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["marvin"])
def cmd_marvin(message):
    """Ejecuta bajo demanda el script de limpieza segura de Marvin."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        msg_temp = bot.reply_to(message, "🧹 [Marvin] Ejecutando protocolo de mantenimiento en el nodo Edge...")
        _, disk_antes, inodes_antes = agatha.verificar_espacio_disco()
        exito = agatha.invocar_marvin()
        _, disk_despues, inodes_despues = agatha.verificar_espacio_disco()

        outcome = "RESOLVED" if exito else "FAILED"
        agatha.registrar_memoria_episodica(
            "manual_marvin_maintenance",
            {"disk_before": disk_antes, "disk_after": disk_despues, "inodes_after": inodes_despues},
            "run_marvin",
            "SRE triggered Marvin manually from Telegram.",
            outcome,
            f"SRE executed Marvin manually; root disk moved from {disk_antes} percent to {disk_despues} percent.",
        )

        if exito:
            texto = (
                "🟢 *Mantenimiento de Marvin completado*\n\n"
                f"• 💽 *Disco:* `{disk_antes}%` → `{disk_despues}%`\n"
                f"• 🗂️ *Inodos:* `{inodes_antes}%` → `{inodes_despues}%`"
            )
        else:
            texto = (
                "⚠️ *Marvin terminó con advertencias*\n\n"
                f"• 💽 *Disco actual:* `{disk_despues}%` | *Inodos:* `{inodes_despues}%`\n"
                "_Revisa precogs_audit.log para más detalle._"
            )

        bot.edit_message_text(
            texto,
            chat_id=message.chat.id,
            message_id=msg_temp.message_id,
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["nivel1"])
def cmd_nivel1(message):
    """Bitácora de incidentes y auto-remediaciones leída desde memoria episódica."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        resumen = arthur.obtener_resumen_episodico(ultimos=5)

        if resumen["total"] == 0:
            bot.reply_to(message, "✅ Clúster pacífico. No se han registrado incidentes en la memoria episódica.")
            return

        reporte = (
            "⚡ *Bitácora de Remediación (Memoria Episódica)*\n"
            f"📊 *Total histórico:* `{resumen['total']}` "
            f"(🟢 `{resumen['resueltos']}` | 🟠 `{resumen['escalados']}` | 🔴 `{resumen['fallidos']}`)\n"
            "_Mostrando los 5 eventos más recientes:_\n\n"
        )

        for ep in resumen["recientes"]:
            ts = arthur.sanitizar_markdown(ep.get("timestamp", "N/A"))
            trigger = arthur.sanitizar_markdown(ep.get("trigger", "N/A"))
            action = arthur.sanitizar_markdown(ep.get("action", "N/A"))
            outcome = arthur.sanitizar_markdown(ep.get("outcome", "N/A"))
            summary = arthur.sanitizar_markdown(ep.get("ste_summary", ""))
            icono = "🟢" if outcome == "RESOLVED" else "🟠" if outcome == "ESCALATED" else "🔴"

            reporte += (
                f"• {icono} `{ts}` | `{trigger}`\n"
                f"  🛠️ *Acción:* `{action}` (`{outcome}`)\n"
                f"  🧠 *STE-100:* {summary}\n\n"
            )

        bot.reply_to(message, reporte.strip(), parse_mode="Markdown")


@bot.message_handler(commands=["baneados"])
def cmd_muro_verguenza(message):
    """Muro de la Vergüenza: Conteo de comandos inválidos interceptados (Determinista)."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        if not os.path.exists(LOG_FILE):
            bot.reply_to(message, "📭 La bitácora está vacía. Cero intentos de sabotaje.")
            return

        comandos_interceptados = []
        with open(LOG_FILE, "r", encoding="utf-8") as f:
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
            reporte += f"• `{arthur.sanitizar_markdown(cmd)}` : {freq} intento(s)\n"

        bot.reply_to(message, reporte, parse_mode="Markdown")


@bot.message_handler(commands=["resumen"])
def cmd_resumen(message):
    """Dashboard Ejecutivo: Resumen global de operaciones y seguridad (Determinista)."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bofh_count = 0
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                for linea in f:
                    if "Intento de comando BOFH interceptado:" in linea:
                        bofh_count += 1

        ep = arthur.obtener_resumen_episodico()
        amenaza = agatha.estado_actual["nivel_amenaza"]
        semaforo = "🟢" if amenaza == 0 else "🟡" if amenaza == 1 else "🔴"

        reporte = (
            "📊 *Dashboard Ejecutivo de PositronicOps*\n"
            f"_Nodo Edge:_ `{NODE_IP}`\n\n"
            f"🛡️ *Escudos BOFH:* `{bofh_count}` bloqueos de usuario\n"
            f"⚡ *Episodios registrados:* `{ep['total']}`\n"
            f"  • Resueltos: `{ep['resueltos']}` | Escalados: `{ep['escalados']}` | Fallidos: `{ep['fallidos']}`\n\n"
            f"{semaforo} *Estado actual:* {agatha.estado_actual['status']}"
        )

        bot.reply_to(message, reporte, parse_mode="Markdown")


@bot.message_handler(commands=["?", "help", "ayuda"])
def cmd_help(message):
    """Despliega la lista de comandos válidos."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        menu = (
            "🤖 *Directivas del Sistema PositronicOps*\n\n"
            "📊 *Observabilidad (Dashiell)*\n"
            "• `/status` - Estado en vivo de contenedores (Gaia)\n"
            "• `/perf` - Telemetría de consumo (CPU/RAM/Disco)\n\n"
            "🧠 *Cognición (Agatha & Arthur)*\n"
            "• `/agatha` - Pulso SysAdmin y nivel de amenaza\n"
            "• `/auditoria` - Auditoría incremental (STE-100)\n"
            "• `/rag <pregunta>` - Consulta RAG sobre memoria episódica\n\n"
            "🛠️ *Operaciones & Bitácoras*\n"
            "• `/marvin` - Limpieza segura de almacenamiento\n"
            "• `/resumen` - Dashboard ejecutivo de defensas\n"
            "• `/nivel1` - Bitácora de remediaciones episódicas\n"
            "• `/baneados` - Muro de la Vergüenza (BOFH)\n\n"
            "⚙️ *Sistema*\n"
            "• `/ping` - Verificación de enlace\n"
            "• `/?` - Muestra este manual de operaciones"
        )
        bot.reply_to(message, menu, parse_mode="Markdown")


@bot.message_handler(commands=["toalla", "towel"])
def cmd_hitchhiker(message):
    """Easter Egg: El sentido de la vida, el universo y todo lo demás."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "🌌 *42*\n\n_(Y no olvides tu toalla)_", parse_mode="Markdown")


@bot.message_handler(commands=["bofh"])
def cmd_bofh(message):
    """Easter Egg explícito."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        excusa = (
            "Falla catastrófica por interferencia de taquiones en el buffer de Nginx. "
            "Manda un correo a soporte y encomiéndate a los dioses del kernel."
        )
        bot.reply_to(message, f"☠️ *[BOFH]*\n{excusa}\n\n_RTFM._", parse_mode="Markdown")


@bot.message_handler(commands=["reboot", "reset", "poweroff", "halt", "shutdown"])
def cmd_troll_system(message):
    """Atrapa intentos de apagar el sistema y se burla del usuario."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "🤡 ¡Jajaja! No lo creo mai.")


@bot.message_handler(func=lambda message: True)
def bofh_catch_all(message):
    """Atrapa cualquier comando o texto no reconocido con actitud BOFH."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        texto_limpio = arthur.sanitizar_markdown(message.text)
        respuestas_bofh = [
            "🛑 Exceso de baneados.",
            "🫩 Negativo. El bot está apagado.",
            "⚠️ Te van a banear...",
            "🛡️ Exceso de dictadura.",
            f"¿`{texto_limpio}`? Mis registros indican un problema en la Capa 8.",
            f"Comando `{texto_limpio}` no reconocido. Redirigiendo petición a `/dev/null`.",
            "Negativo. Multivac se está riendo de tu sintaxis en binario 😅",
            "Ese comando no existe en esta línea temporal. Intenta de nuevo o *RTFM*.",
        ]
        logging.warning(f"Intento de comando BOFH interceptado: {message.text}")
        bot.reply_to(message, random.choice(respuestas_bofh), parse_mode="Markdown")


if __name__ == "__main__":
    logging.info("🏛️ [Temple] Energizando núcleo. Iniciando ecosistema...")

    hilo_agatha = threading.Thread(
        target=agatha.vision_precognitiva,
        args=(enviar_alerta, escalar_humano, escalar_humano_critico),
        daemon=True,
    )
    hilo_agatha.start()

    logging.info("🤖 [Andrew/Arthur] Modulando frecuencias. A la espera de directivas...")
    bot.infinity_polling()

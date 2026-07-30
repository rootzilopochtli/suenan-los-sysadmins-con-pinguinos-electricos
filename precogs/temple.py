import os
import threading
import time
import telebot
import random
import subprocess
from dotenv import load_dotenv


# ==========================================
# 1. CONFIGURACIÓN DEL TEMPLO Y CREDENCIALES
# ==========================================
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not ADMIN_CHAT_ID:
    print("❌ [Temple] Fallo estructural: No se encontraron credenciales en el archivo .env")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# ==========================================
# 2. LOS PRECOGS (Hilos de Background)
# ==========================================
def agatha_vision():
    """
    La Precog Principal: Monitoreo continuo de Nginx.
    Este proceso corre en paralelo al bot de Telegram.
    """
    print("🔮 [Agatha] Sumergida en el tanque de estasis. Vigilando el Ingress...")
    while True:
        # TODO: Aquí migraremos la lógica de lectura de logs y llamadas a Multivac
        # Simulamos que Agatha está trabajando sin bloquear el script
        time.sleep(10)

# ==========================================
# 3. INTERACCIONES (Comandos de Telegram)
# ==========================================

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    """Comando de salud del sistema."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "¡Pong! 🏓 Todos los Precogs en línea y respirando.")

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

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Arthur: Consulta el estado en vivo de los pods del clúster."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        msg_temp = bot.reply_to(message, "🔍 [Arthur] Analizando la línea temporal del clúster...")

        # Obtenemos la ruta del kubeconfig desde el .env
        kubeconfig = os.getenv("KUBECONFIG_PATH")

        try:
            # Le pasamos la bandera explícita al comando oc
            resultado = subprocess.run(
                ["oc", "--kubeconfig", kubeconfig, "get", "pods", "-n", "default"],
                capture_output=True,
                text=True,
                check=True
            )
            salida = resultado.stdout

            bot.edit_message_text(
                f"📊 *Estado Actual (Gaia):*\n```text\n{salida}\n```",
                chat_id=message.chat.id,
                message_id=msg_temp.message_id,
                parse_mode="Markdown"
            )

        except subprocess.CalledProcessError as e:
            bot.edit_message_text(
                f"❌ [Arthur] Falla al consultar el clúster:\n```text\n{e.stderr}\n```",
                chat_id=message.chat.id,
                message_id=msg_temp.message_id,
                parse_mode="Markdown"
            )

        except FileNotFoundError:
            bot.edit_message_text(
                "❌ [Arthur] Comando 'oc' no encontrado. ¿Estoy ejecutándome en el nodo correcto?",
                chat_id=message.chat.id,
                message_id=msg_temp.message_id
            )

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
            f"Comando `{message.text}` no reconocido. Redirigiendo petición a `/dev/null`."
            f"¿`{message.text}`? Interesante intento. Mis registros indican que tienes un error de Capa 8.",
            f"Negativo. Multivac se está riendo de tu sintaxis en binario 😅",
            f"Ese comando no existe en esta línea temporal. Intenta de nuevo o *RTFM*."
        ]
        bot.reply_to(message, random.choice(respuestas_bofh), parse_mode="Markdown")

# ==========================================
# 4. EL GRAN ORQUESTADOR (Main)
# ==========================================
if __name__ == "__main__":
    print("🏛️ [Temple] Energizando núcleo. Iniciando ecosistema PositronicOps...")

    # 1. Despertamos a Agatha en su propio hilo (daemon=True asegura que muera si apagamos el script)
    hilo_agatha = threading.Thread(target=agatha_vision, daemon=True)
    hilo_agatha.start()

    # 2. Despertamos a Andrew/Arthur en el hilo principal
    print("🤖 [Andrew/Arthur] Modulando frecuencias. A la espera de directivas tácticas...")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n🛑 [Temple] Apagado manual de los sistemas. Precogs desconectados.")


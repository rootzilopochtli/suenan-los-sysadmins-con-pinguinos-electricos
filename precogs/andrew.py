import telebot

# Credenciales de acceso (El Alma de Andrew)
TOKEN = "8510896714:AAHGU9_ugP5z8K5G3QdNSrBWWj5JugFwIec"
ADMIN_CHAT_ID = "19320644"

bot = telebot.TeleBot(TOKEN)

def notificar(mensaje):
    """Función que Agatha llamará para gritar por ayuda."""
    try:
        # Usamos parse_mode="Markdown" para que los mensajes se vean atractivos
        bot.send_message(ADMIN_CHAT_ID, mensaje, parse_mode="Markdown")
        print("🤖 [Andrew] Notificación despachada a tu Telegram.")
    except Exception as e:
        print(f"❌ [Andrew] Fallo en enlace de comunicaciones: {e}")

# --- PROTOCOLOS DE INTERACCIÓN DIRECTA ---

@bot.message_handler(commands=['ping'])
def send_ping(message):
    """Responde a un comando /ping validando que seas tú."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        bot.reply_to(message, "¡Pong! 🏓 Sistemas de comunicación en línea. En espera de anomalías.")
    else:
        # Las Leyes de la Robótica aplicadas a la seguridad
        bot.reply_to(message, "Acceso denegado. 'Un robot debe proteger su propia existencia...'")

if __name__ == "__main__":
    print("🤖 [Andrew] Iniciando protocolos de enlace. Escuchando frecuencias de Telegram...")
    bot.infinity_polling()

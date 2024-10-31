import requests
import os
import time
import schedule
from threading import Thread

# Cargar configuraciones desde variables de entorno
# Cargar configuraciones desde variables de entorno
domains = set(os.getenv("HEALTH_CHECK_DOMAINS", "").split(",")) if os.getenv("HEALTH_CHECK_DOMAINS") else set()
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
check_interval = int(os.getenv("CHECK_INTERVAL", 60))  # Default: 60 segundos
status_report_interval = int(os.getenv("STATUS_REPORT_INTERVAL", 3600))  # Default: 3600 segundos

# Variable para controlar el modo de eliminación
removal_in_progress = False

# Función para enviar mensajes de Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        response = requests.post(url, json=payload, verify=False)
        response.raise_for_status()
        print(f"Mensaje enviado a Telegram: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje de Telegram: {e}")

# Función para verificar la salud de un dominio
def check_health(domain):
    try:
        print(f"Haciendo PING a {domain}")
        response = requests.get(domain, timeout=5, verify=False)
        return (domain, response.status_code == 200)
    except requests.exceptions.RequestException as e:
        return (domain, False, str(e))

# Función para ejecutar las verificaciones de salud
def health_check():
    for domain in domains:
        if domain:
            result = check_health(domain)
            # Solo enviar mensaje en caso de error
            if not result[1]:  # Si el chequeo falla
                if len(result) == 3:
                    send_telegram_message(f"❌ Error: No se pudo conectar a {result[0]}. \n{result[2]}")
                else:
                    send_telegram_message(f"❌ {result[0]} falló con estado: {result[1]}")

# Función para reportar el estado de todos los dominios
def status_report():
    report = "Estado de dominios:\n"
    for domain in domains:
        result = check_health(domain)
        if result[1]:  # Si está activo
            report += f"✅ {result[0]} está activo.\n"
        else:
            if len(result) == 3:
                report += f"❌ {result[0]} falló: {result[2]}\n"
            else:
                report += f"❌ {result[0]} falló con estado: {result[1]}\n"
    send_telegram_message(report)

# Función para manejar comandos de Telegram
def handle_command(command, user_id):
    global check_interval, status_report_interval, removal_in_progress
    parts = command.split()
    
    if len(parts) == 0:
        send_telegram_message("⚠️ Comando no reconocido. Usa: /help para ver los comandos disponibles\n")
        return

    if parts[0] == "/set_check_interval":
        if len(parts) < 2:
            send_telegram_message("⚠️ Por favor, proporciona un número válido para el intervalo de verificación.")
            return
        try:
            check_interval = int(parts[1])
            schedule.clear('check')
            schedule.every(check_interval).seconds.do(health_check).tag('check')
            send_telegram_message(f"🕒 Intervalo de verificación de salud ajustado a {check_interval} segundos.")
        except ValueError:
            send_telegram_message("⚠️ Por favor, proporciona un número válido para el intervalo.")
        return  # Detener la ejecución aquí

    elif parts[0] == "/set_report_interval":
        if len(parts) < 2:
            send_telegram_message("⚠️ Por favor, proporciona un número válido para el intervalo de reporte.")
            return
        try:
            status_report_interval = int(parts[1])
            schedule.clear('report')
            schedule.every(status_report_interval).seconds.do(status_report).tag('report')
            send_telegram_message(f"🕒 Intervalo de reporte ajustado a {status_report_interval} segundos.")
        except ValueError:
            send_telegram_message("⚠️ Por favor, proporciona un número válido para el intervalo.")
        return  # Detener la ejecución aquí

    elif parts[0] == "/add_domain":
        if len(parts) < 2:
            send_telegram_message("⚠️ Por favor, proporciona un dominio para agregar.")
            return
        domain = parts[1]
        domains.add(domain)
        send_telegram_message(f"✅ Dominio agregado: {domain}")
        return  # Detener la ejecución aquí

    elif parts[0] == "/remove_domain":
        if not domains:
            send_telegram_message("⚠️ No hay dominios para eliminar.")
            return
        domains_list = "\n".join([f"{i + 1}. {domain}" for i, domain in enumerate(domains)])
        send_telegram_message(f"🗑️ Selecciona un dominio para eliminar:\n{domains_list}\nPor favor, escribe el número correspondiente.")
        removal_in_progress = True  # Inicia el proceso de eliminación
        return  # Solicitar el número de dominio para eliminar

    elif parts[0] == "/status":
        send_telegram_message("🔄 Generando reporte de estado de los dominios...")
        status_report()
        return  # Detener la ejecución aquí

    elif parts[0] == "/config":
        config_message = (
            f"🛠️ Configuración actual:\n"
            f"Intervalo de verificación: {check_interval} segundos\n"
            f"Intervalo de reporte: {status_report_interval} segundos\n\n"
            f"Dominios a revisar:\n" + "\n".join(domains)
        )
        send_telegram_message(config_message)
        return  # Detener la ejecución aquí

    elif parts[0] == "/help":
        help_message = (
            "ℹ️ **Comandos disponibles:**\n"
            "/set_check_interval <segundos> - Establece el intervalo de verificación de salud.\n"
            "/set_report_interval <segundos> - Establece el intervalo para el reporte de estado.\n"
            "/add_domain <dominio> - Agrega un dominio a la lista de chequeo.\n"
            "/remove_domain - Elimina un dominio de la lista de chequeo. Responde con el número correspondiente.\n"
            "/config - Muestra la configuración actual y la lista de dominios.\n"
            "/status - Genera un reporte del estado actual de todos los dominios.\n"
            "/help - Muestra esta lista de comandos y su descripción."
        )
        send_telegram_message(help_message)
        return  # Detener la ejecución aquí

    # Si el comando no se reconoce, enviamos el mensaje de error
    send_telegram_message("⚠️ No te he entendido. Usa: /help para ver los comandos disponibles\n")

# Función para verificar mensajes entrantes
def listen_for_commands():
    global removal_in_progress
    offset = None
    while True:
        url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"
        params = {"timeout": 100, "offset": offset}
        try:
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status()
            data = response.json()
            for result in data["result"]:
                offset = result["update_id"] + 1
                if "text" in result["message"]:
                    user_id = result["message"]["from"]["id"]  # Identifica al usuario
                    if removal_in_progress:
                        try:
                            domain_index = int(result["message"]["text"]) - 1
                            domain_to_remove = list(domains)[domain_index]
                            domains.remove(domain_to_remove)
                            send_telegram_message(f"✅ Dominio eliminado: {domain_to_remove}")
                            removal_in_progress = False  # Finaliza el proceso de eliminación
                        except (ValueError, IndexError):
                            send_telegram_message("⚠️ Selección no válida. Por favor, elige un número de la lista.")
                    else:
                        handle_command(result["message"]["text"], user_id)
        except requests.exceptions.RequestException as e:
            print(f"Error al recibir comandos de Telegram: {e}")
        time.sleep(1)

# Configurar las tareas de Schedule
schedule.every(check_interval).seconds.do(health_check).tag('check')
schedule.every(status_report_interval).seconds.do(status_report).tag('report')

# Mensaje de bienvenida y reporte inicial

if len(domains) > 0:
    domains_list = "\n".join(f" - {domain}" for domain in domains)
    welcome_message = (f"👋 ¡Bienvenido al HealthBot! Comenzando chequeo de dominios...\n\n"
                       f"🔍 Este bot verifica la salud de los siguientes dominios:\n{domains_list}\n\n"
                       f"🕒 Intervalo de verificación actual: {check_interval} segundos.\n"
                       f"🕒 Intervalo de reporte actual: {status_report_interval} segundos.")
else:
    welcome_message = (f"👋 ¡Bienvenido al HealthBot! Comenzando chequeo de dominios...\n\n"
                       f"🔍 Este bot verifica la salud de los dominios configurados y te notifica sobre su estado.\n"
                       f"⚠️ Actualmente no hay dominios configurados para revisar. Usa el comando /add_domain para agregar dominios.\n"
                       f"🕒 Intervalo de verificación actual: {check_interval} segundos.\n"
                       f"🕒 Intervalo de reporte actual: {status_report_interval} segundos.")

send_telegram_message(welcome_message)

# Iniciar la escucha de comandos
thread = Thread(target=listen_for_commands)
thread.start()

# Iniciar el loop de schedule
while True:
    schedule.run_pending()
    time.sleep(1)

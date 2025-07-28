import requests
import os
import time
import schedule
from threading import Thread

# Load configurations from environment variables
domains = set(os.getenv("HEALTH_CHECK_DOMAINS", "").split(",")) if os.getenv("HEALTH_CHECK_DOMAINS") else set()
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
check_interval = int(os.getenv("CHECK_INTERVAL", 60))  # Default: 60 seconds
status_report_interval = int(os.getenv("STATUS_REPORT_INTERVAL", 3600))  # Default: 3600 seconds

# Variable to control removal mode
removal_in_progress = False

# Function to send Telegram messages
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    try:
        response = requests.post(url, json=payload, verify=False)
        response.raise_for_status()
        print(f"Message sent to Telegram: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

# Function to check the health of a domain
def check_health(domain):
    try:
        print(f"Pinging {domain}")
        response = requests.get(domain, timeout=5, verify=False)
        return (domain, response.status_code == 200)
    except requests.exceptions.RequestException as e:
        return (domain, False, str(e))

# Function to run health checks
def health_check():
    for domain in domains:
        if domain:
            result = check_health(domain)
            # Only send a message in case of error
            if not result[1]:  # If the check fails
                if len(result) == 3:
                    send_telegram_message(f"❌ Error: Could not connect to {result[0]}.\n{result[2]}")
                else:
                    send_telegram_message(f"❌ {result[0]} failed with status: {result[1]}")

# Function to report the status of all domains
def status_report():
    report = "Domain status:\n"
    for domain in domains:
        result = check_health(domain)
        if result[1]:  # If it's active
            report += f"✅ {result[0]} is up.\n"
        else:
            if len(result) == 3:
                report += f"❌ {result[0]} failed: {result[2]}\n"
            else:
                report += f"❌ {result[0]} failed with status: {result[1]}\n"
    send_telegram_message(report)

# Function to handle Telegram commands
def handle_command(command, user_id):
    global check_interval, status_report_interval, removal_in_progress
    parts = command.split()
    
    if len(parts) == 0:
        send_telegram_message("⚠️ Unrecognized command. Use /help to see the available commands.\n")
        return

    if parts[0] == "/set_check_interval":
        if len(parts) < 2:
            send_telegram_message("⚠️ Please provide a valid number for the health check interval.")
            return
        try:
            check_interval = int(parts[1])
            schedule.clear('check')
            schedule.every(check_interval).seconds.do(health_check).tag('check')
            send_telegram_message(f"🕒 Health check interval set to {check_interval} seconds.")
        except ValueError:
            send_telegram_message("⚠️ Please provide a valid number for the interval.")
        return  # Stop execution here

    elif parts[0] == "/set_report_interval":
        if len(parts) < 2:
            send_telegram_message("⚠️ Please provide a valid number for the report interval.")
            return
        try:
            status_report_interval = int(parts[1])
            schedule.clear('report')
            schedule.every(status_report_interval).seconds.do(status_report).tag('report')
            send_telegram_message(f"🕒 Report interval set to {status_report_interval} seconds.")
        except ValueError:
            send_telegram_message("⚠️ Please provide a valid number for the interval.")
        return  # Stop execution here

    elif parts[0] == "/add_domain":
        if len(parts) < 2:
            send_telegram_message("⚠️ Please provide a domain to add.")
            return
        domain = parts[1]
        domains.add(domain)
        send_telegram_message(f"✅ Domain added: {domain}")
        return  # Stop execution here

    elif parts[0] == "/remove_domain":
        if not domains:
            send_telegram_message("⚠️ There are no domains to remove.")
            return
        domains_list = "\n".join([f"{i + 1}. {domain}" for i, domain in enumerate(domains)])
        send_telegram_message(f"🗑️ Select a domain to remove:\n{domains_list}\nPlease type the corresponding number.")
        removal_in_progress = True  # Start the removal process
        return  # Await number to remove domain

    elif parts[0] == "/status":
        send_telegram_message("🔄 Generating status report of the domains...")
        status_report()
        return  # Stop execution here

    elif parts[0] == "/config":
        config_message = (
            f"🛠️ Current configuration:\n"
            f"Health check interval: {check_interval} seconds\n"
            f"Report interval: {status_report_interval} seconds\n\n"
            f"Domains to monitor:\n" + "\n".join(domains)
        )
        send_telegram_message(config_message)
        return  # Stop execution here

    elif parts[0] == "/help":
        help_message = (
            "ℹ️ **Available commands:**\n"
            "/set_check_interval <seconds> - Set the health check interval.\n"
            "/set_report_interval <seconds> - Set the interval for status reports.\n"
            "/add_domain <domain> - Add a domain to the check list.\n"
            "/remove_domain - Remove a domain from the check list. Reply with the corresponding number.\n"
            "/config - Show the current configuration and domain list.\n"
            "/status - Generate the current status report for all domains.\n"
            "/help - Show this list of commands and their descriptions."
        )
        send_telegram_message(help_message)
        return  # Stop execution here

    # If the command is not recognized, send an error message
    send_telegram_message("⚠️ I didn't understand you. Use: /help to see the available commands.\n")

# Function to check incoming messages
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
                    user_id = result["message"]["from"]["id"]  # Identify the user
                    if removal_in_progress:
                        try:
                            domain_index = int(result["message"]["text"]) - 1
                            domain_to_remove = list(domains)[domain_index]
                            domains.remove(domain_to_remove)
                            send_telegram_message(f"✅ Domain removed: {domain_to_remove}")
                            removal_in_progress = False  # End removal process
                        except (ValueError, IndexError):
                            send_telegram_message("⚠️ Invalid selection. Please choose a number from the list.")
                    else:
                        handle_command(result["message"]["text"], user_id)
        except requests.exceptions.RequestException as e:
            print(f"Error receiving commands from Telegram: {e}")
        time.sleep(1)

# Set up scheduled tasks
schedule.every(check_interval).seconds.do(health_check).tag('check')
schedule.every(status_report_interval).seconds.do(status_report).tag('report')

# Welcome message and initial report
if len(domains) > 0:
    domains_list = "\n".join(f" - {domain}" for domain in domains)
    welcome_message = (f"👋 Welcome to HealthBot! Starting domain check...\n\n"
                       f"🔍 This bot monitors the health of the following domains:\n{domains_list}\n\n"
                       f"🕒 Current health check interval: {check_interval} seconds.\n"
                       f"🕒 Current report interval: {status_report_interval} seconds.")
else:
    welcome_message = (f"👋 Welcome to HealthBot! Starting domain check...\n\n"
                       f"🔍 This bot monitors the health of configured domains and notifies you of their status.\n"
                       f"⚠️ There are currently no domains configured for checking. Use the /add_domain command to add domains.\n"
                       f"🕒 Current health check interval: {check_interval} seconds.\n"
                       f"🕒 Current report interval: {status_report_interval} seconds.")

send_telegram_message(welcome_message)

# Start listening for commands
thread = Thread(target=listen_for_commands)
thread.start()

# Start the schedule loop
while True:
    schedule.run_pending()
    time.sleep(1)

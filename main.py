import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os
import requests
from scraperHelpers import check_stock_zara

# Config dosyasını oku
with open("config.json", "r") as config_file:
    config = json.load(config_file)

urls_to_check = config["urls"]
sleep_min_seconds = config["sleep_min_seconds"]
sleep_max_seconds = config["sleep_max_seconds"]

# Bot message fetch variables:
load_dotenv()
BOT_API = os.getenv("BOT_API")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_API or not CHAT_ID:
    print("BOT_API or CHAT_ID not found in .env file. Telegram messages will be disabled.")
    TELEGRAM_ENABLED = False
else:
    TELEGRAM_ENABLED = True

def send_telegram_message(message):
    if not TELEGRAM_ENABLED:
        print("⚠️ Telegram message skipped (missing BOT_API or CHAT_ID).")
        return

    chat_ids = [chat_id.strip() for chat_id in CHAT_ID.split(",")]
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{BOT_API}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            print(f"Telegram message sent to {chat_id}.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Telegram message to {chat_id}: {e}")


# --- DRIVER'ı döngü dışında bir kez açıyoruz ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
chrome_options.binary_location = "/usr/bin/chromium"  # Railway için zorunlu

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    while True:
        for item in urls_to_check:
            try:
                url = item.get("url")
                store = item.get("store")
                sizes = item.get("sizes_to_check", None)  # Her ürünün kendi beden(leri)
                driver.get(url)
                print("--------------------------------")
                print(f"Url {url} için: ")
                if store == "zara":
                    if sizes:
                        size_in_stock = check_stock_zara(driver, sizes)
                        if size_in_stock:
                            message = f"🛍️{size_in_stock} beden stokta!!!!\nLink: {url}"
                            print(f"ALERT: {message}")
                            send_telegram_message(message)
                        else:
                            print(f"Checked {url} - no stock found for sizes {', '.join(sizes)}.")
                    else:
                        size_in_stock = check_stock_zara(driver, [])
                        if size_in_stock is not None:
                            message = f"🛍️ Ürün stokta!\nLink: {url}"
                            print(f"ALERT: {message}")
                            send_telegram_message(message)
                        else:
                            print(f"Checked {url} - no stock found (no size specified).")
                else:
                    print("URL not found")
            except Exception as e:
                print(f"An error occurred with URL {url}: {e}")

        sleep_time = random.randint(sleep_min_seconds, sleep_max_seconds)
        print(f"Sleeping for {sleep_time // 60} minutes and {sleep_time % 60} seconds...")
        time.sleep(sleep_time)
finally:
    print("Closing the browser...")
    driver.quit()

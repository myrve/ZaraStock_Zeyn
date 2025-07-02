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

cart_status = {item["url"]: False for item in urls_to_check}

# Bot message fetch variables:
load_dotenv()
BOT_API = os.getenv("BOT_API")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_API or not CHAT_ID:
    print("BOT_API or CHAT_ID not found in .env file. Telegram messages will be disabled.")
    TELEGRAM_ENABLED = False
else:
    TELEGRAM_ENABLED = True

# play_sound fonksiyonunu tamamen kaldırıyoruz veya boş bırakıyoruz
def play_sound(sound_file):
    # Railway'de ses çalmak mümkün değil, bu fonksiyonu boş bırakıyoruz.
    pass

def send_telegram_message(message):
    if not TELEGRAM_ENABLED:
        print("⚠️ Telegram message skipped (missing BOT_API or CHAT_ID).")
        return

    url = f"https://api.telegram.org/bot{BOT_API}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print("Telegram message sent.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

while True:
    # Railway için Selenium ayarları (Chrome ve ChromeDriver path'leri sabit)
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

    # Webdriver'ı başlat (Railway'de webdriver_manager kullanma!)
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        for item in urls_to_check:
            try:
                if cart_status[item["url"]]:
                    print("Item already in cart, skipping...")
                    continue
                else:
                    url = item.get("url")
                    store = item.get("store")
                    sizes = item.get("sizes_to_check", None)  # Her ürünün kendi beden(leri)
                    driver.get(url)
                    print("--------------------------------")
                    print(f"Url {url} için: ")
                    if store == "zara":
                        if sizes:  # Eğer beden belirtilmişse
                            size_in_stock = check_stock_zara(driver, sizes)
                            if size_in_stock:
                                message = f"🛍️{size_in_stock} beden stokta!!!!\nLink: {url}"
                                print(f"ALERT: {message}")
                                play_sound('Crystal.mp3')  # Artık bir şey yapmaz
                                send_telegram_message(message)
                                cart_status[item["url"]] = True
                            else:
                                print(f"Checked {url} - no stock found for sizes {', '.join(sizes)}.")
                        else:  # Beden yoksa, stok kontrolünü beden olmadan yapabilirsin
                            size_in_stock = check_stock_zara(driver, [])
                            if size_in_stock is not None:
                                message = f"🛍️ Ürün stokta!\nLink: {url}"
                                print(f"ALERT: {message}")
                                play_sound('Crystal.mp3')  # Artık bir şey yapmaz
                                send_telegram_message(message)
                                cart_status[item["url"]] = True
                            else:
                                print(f"Checked {url} - no stock found (no size specified).")
                    else:
                        print("URL not found")
            except Exception as e:
                print(f"An error occurred with URL {url}: {e}")
    finally:
        print("Closing the browser...")
        driver.quit()

        sleep_time = random.randint(sleep_min_seconds, sleep_max_seconds)
        print(f"Sleeping for {sleep_time // 60} minutes and {sleep_time % 60} seconds...")
        time.sleep(sleep_time)

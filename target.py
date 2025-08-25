import os
import sys

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
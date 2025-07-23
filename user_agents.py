import random

def generate_user_agent():
    platforms = [
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win64; arm64",
        "Windows NT 10.0; WOW64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 12_5",
        "X11; Linux x86_64",
        "Linux; Android 14; Pixel 7",
        "Linux; Android 13; SM-G991B",
        "Linux; Android 12; Redmi Note 10",
        "iPhone; CPU iPhone OS 17_4 like Mac OS X",
        "iPhone; CPU iPhone OS 16_6 like Mac OS X",
        "iPad; CPU OS 17_4 like Mac OS X",
    ]

    browsers = [
        ("Chrome", [118, 119, 120, 121, 122, 123, 124]),
        ("Firefox", [118, 119, 120, 121, 122, 123, 124]),
        ("Safari", [15, 16, 17]),
        ("Edg", [118, 119, 120, 121, 122, 123, 124]),
        ("OPR", [90, 95, 100, 105, 110]),
    ]

    platform = random.choice(platforms)
    browser, versions = random.choice(browsers)
    version = random.choice(versions)

    if "Linux; Android" in platform:
        template = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Mobile Safari/537.36"
    elif "iPhone" in platform or "iPad" in platform:
        template = f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version}.0 Mobile/15E148 Safari/604.1"
    elif browser == "Firefox":
        template = f"Mozilla/5.0 ({platform}; rv:{version}.0) Gecko/20100101 Firefox/{version}.0"
    elif browser == "Safari":
        template = f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version}.0 Safari/605.1.15"
    elif browser == "Edg":
        template = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36 Edg/{version}.0.0.0"
    elif browser == "OPR":
        template = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36 OPR/{version}.0.0.0"
    else:
        template = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"

    return template

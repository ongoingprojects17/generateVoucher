# config.py
import threading
from queue import Queue

TARGET_URL = ""
TIMEOUT = 5
MAX_THREADS = 20

tried_vouchers = set()
lock = threading.Lock()
working_proxies = []
voucher_queue = Queue()
stop_event = threading.Event()
proxy_lock = threading.Lock()
tried_vouchers = {}  # contoh: {"7": set(), "12": set()}
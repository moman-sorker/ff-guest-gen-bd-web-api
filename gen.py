import os
import sys
import time
import json
import base64
import random
import string
import codecs
import hmac
import hashlib
import threading
import re
import subprocess
import secrets
import signal
import uuid
import csv
import shutil
import asyncio
from datetime import datetime, timezone
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from typing import Dict, Optional, List, Any, Tuple

# ══════════════════════════════════════════════════════════════════════════
#  BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════
class _Bootstrapper:
    @staticmethod
    def install() -> None:
        required = ['requests', 'pycryptodome', 'colorama', 'aiohttp', 'blackboxprotobuf']
        for pkg in required:
            try:
                if pkg == 'pycryptodome':
                    import Crypto
                elif pkg == 'requests':
                    import requests
                elif pkg == 'colorama':
                    from colorama import Fore, Style, init
                elif pkg == 'aiohttp':
                    import aiohttp
                elif pkg == 'blackboxprotobuf':
                    import blackboxprotobuf
            except ImportError:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg, '-q'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
        try:
            from colorama import init
            init(autoreset=True)
        except Exception:
            pass


_Bootstrapper.install()

import requests
import urllib3
import aiohttp
import blackboxprotobuf
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from colorama import Fore, Style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        os.system("chcp 65001 > nul 2>&1")
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════
#  CREDIT — SARKER
# ══════════════════════════════════════════════════════════════════════════
_OWNER_NAME    = "M. SARKER"
_OWNER_TAG     = "SARKER"
_OWNER_VER     = " "
_OWNER_SIG     = "SARKER"
_OWNER_TG      = " "
_OWNER_COUNTRY = "BANGLADESH"


def _verify_credit() -> bool:
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            content = f.read()
        required = [_OWNER_NAME, _OWNER_TAG, _OWNER_VER, _OWNER_SIG]
        for s in required:
            if s not in content:
                return False
        return True
    except Exception:
        return True


def _show_violation():
    os.system("cls" if os.name == "nt" else "clear")
    print()
    print("  \033[1;91m" + "╔" + "═" * 62 + "╗\033[0m")
    print("  \033[1;91m║\033[0m      \033[1;97m⚠️  SARKER CREDIT VIOLATION  ⚠️\033[0m            \033[1;91m║\033[0m")
    print("  \033[1;91m╚" + "═" * 62 + "╝\033[0m")
    print()
    print(f"  \033[38;5;222mOwner  : \033[97m{_OWNER_NAME}\033[0m")
    print(f"  \033[38;5;222mTG     : \033[97m{_OWNER_TG}\033[0m")
    print(f"  \033[38;5;222mVersion: \033[97m{_OWNER_VER}\033[0m")
    print()
    try:
        input("  \033[38;5;240mPress Enter to exit...\033[0m")
    except Exception:
        pass
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════
#  COLORS — SARKER NEON PALETTE
# ══════════════════════════════════════════════════════════════════════════
class PALETTE:
    # Sakura family
    SAKURA       = '\033[38;5;218m'
    SAKURA_DEEP  = '\033[38;5;211m'
    SAKURA_LIGHT = '\033[38;5;224m'
    BLOSSOM      = '\033[38;5;225m'
    PETAL        = '\033[38;5;219m'

    # Neon JP family
    NEON_PURPLE  = '\033[38;5;171m'
    NEON_VIOLET  = '\033[38;5;135m'
    NEON_INDIGO  = '\033[38;5;105m'
    NEON_CYAN    = '\033[38;5;123m'
    NEON_MINT    = '\033[38;5;121m'

    # BD glow
    BD_GREEN     = '\033[38;5;40m'
    BD_EMERALD   = '\033[38;5;48m'
    BD_RED       = '\033[38;5;203m'
    BD_CRIMSON   = '\033[38;5;197m'
    BD_GOLD      = '\033[38;5;222m'

    # Neutrals
    FOG          = '\033[38;5;246m'
    MIST         = '\033[38;5;250m'
    CLOUD        = '\033[38;5;253m'
    PURE         = '\033[38;5;231m'
    SHADOW       = '\033[38;5;238m'
    ABYSS        = '\033[38;5;234m'

    # Extra
    AURORA       = '\033[38;5;120m'
    CORAL_JP     = '\033[38;5;210m'
    SUNSET       = '\033[38;5;215m'
    LAVENDER_JP  = '\033[38;5;189m'
    MINT_JP      = '\033[38;5;158m'

    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    ITALIC = '\033[3m'
    UNDER  = '\033[4m'
    BLINK  = '\033[5m'
    RESET  = '\033[0m'

    # Gradient palettes
    SAKURA_FLOW = [SAKURA, SAKURA_DEEP, PETAL, BLOSSOM, SAKURA_LIGHT, SAKURA, PETAL]
    JP_NEON     = [NEON_PURPLE, NEON_VIOLET, NEON_INDIGO, NEON_CYAN, NEON_MINT, NEON_PURPLE]
    BD_SPIRIT   = [BD_GREEN, BD_EMERALD, AURORA, BD_GOLD, BD_RED, BD_CRIMSON, BD_GREEN]
    AURORA_FLOW = [AURORA, MINT_JP, NEON_MINT, NEON_CYAN, LAVENDER_JP, NEON_VIOLET, AURORA]
    SUNSET_JP   = [SUNSET, CORAL_JP, SAKURA_DEEP, PETAL, BLOSSOM, SUNSET]
    SARKER  = [BD_GOLD, SUNSET, SAKURA_DEEP, NEON_PURPLE, NEON_CYAN, BD_GREEN, BD_GOLD]


# ══════════════════════════════════════════════════════════════════════════
#  CONFIG — SARKER BD
# ══════════════════════════════════════════════════════════════════════════
CURRENT_DIR   = os.path.dirname(os.path.abspath(__file__))
RESULT_FOLDER = os.path.join(CURRENT_DIR, "Guest")
LOGS_FOLDER   = os.path.join(RESULT_FOLDER, "logs")

os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)


class Config:
    ACCOUNTS_FILE           = os.path.join(RESULT_FOLDER, "accounts.json")
    ACTIVATED_FILE          = os.path.join(RESULT_FOLDER, "activated_accounts.json")
    ACTIVATION_RESULTS_FILE = os.path.join(RESULT_FOLDER, "activation_results.csv")
    STATS_FILE              = os.path.join(RESULT_FOLDER, "stats.json")
    ERROR_LOG_FILE          = os.path.join(LOGS_FOLDER, "errors.log")

    API_HEX_KEY    = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
    API_SECRET_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

    AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

    CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
    APP_ID        = 100067
    RELEASE_VER   = "OB55"
    GAME_VERSION  = "2.132.4"

    URL_GUEST_REGISTER = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
    URL_TOKEN_GRANT    = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    URL_MAJOR_LOGIN    = "https://loginbp.ppmainecoonghj.com/MajorLogin"
    URL_MAJOR_REGISTER = "https://loginbp.ppmainecoonghj.com/MajorRegister"
    URL_NEWBIE_CHOICE  = "https://loginbp.ppmainecoonghj.com/ChooseNewbieChoice"
    URL_GETLOGIN_IND   = "https://client.ind.freefiremobile.com/GetLoginData"

    ACTIVATION_API     = "https://ff-jwt-web-api-iota.vercel.app/token"
    ACTIVATION_TIMEOUT = 8

    REGION_LANG = {
        "BD": "bn", "IND": "hi", "PK": "ur", "SG": "en", "ID": "id",
        "ME": "ar", "CIS": "ru", "TH": "th", "EU": "en", "US": "en",
        "SAC": "es", "LK": "en"
    }

    TURBO_THREADS        = 16
    MAX_THREADS          = 200
    MIN_THREADS          = 1
    ACTIVATION_COOLDOWN  = 0.4
    BATCH_COOLDOWN       = 30.0
    MODE_LABEL           = "HYPER"

    DEFAULT_WORKERS      = 16
    MIN_WORKERS          = 1
    MAX_WORKERS          = 200
    HTTP_POOL_LIMIT      = 500
    HTTP_POOL_PER_HOST   = 200
    BATCH_SAVE_SIZE      = 20
    BATCH_SAVE_INTERVAL  = 3.0
    PACE_PER_PROXY       = 0.4
    HTTP_TIMEOUT         = (5, 10)

    BRAND            = "SARKER"
    BRAND_LONG       = "SARKER"
    BRAND_TAG        = "SARKER"
    CREDIT           = "M. SARKER"
    PASSWORD_PREFIX  = "MM388401"
    NICK_PREFIX      = "SARKER"
    DEFAULT_REGION   = "BD"


# ══════════════════════════════════════════════════════════════════════════
#  BANGLADESH IPs
# ══════════════════════════════════════════════════════════════════════════
BANGLADESH_IPS = [
    "103.4.146.10",  "103.4.146.22",  "103.4.147.15",  "103.4.147.30",
    "103.230.104.10","103.230.104.22","103.230.105.15","103.230.105.30",
    "103.108.148.10","103.108.148.22","103.108.149.15","103.108.149.30",
    "103.87.202.10", "103.87.202.25", "103.87.203.14", "103.87.203.30",
    "103.48.16.10",  "103.48.16.22",  "103.48.17.15",  "103.48.17.30",
    "103.100.88.10", "103.100.88.22", "103.100.89.15", "103.100.89.30",
    "103.25.248.10", "103.25.248.25", "103.25.249.14", "103.25.249.30",
    "103.16.44.10",  "103.16.44.22",  "103.16.45.15",  "103.16.45.30",
    "103.84.148.10", "103.84.148.22", "103.84.149.15", "103.84.149.30",
    "103.102.28.10", "103.102.28.22", "103.102.29.15", "103.102.29.30",
    "103.75.16.10",  "103.75.16.22",  "103.75.17.15",  "103.75.17.30",
    "103.136.180.10","103.136.180.22","103.136.181.15","103.136.181.30",
    "103.230.84.10", "103.230.84.22", "103.230.85.15", "103.230.85.30",
    "103.56.208.10", "103.56.208.22", "103.56.209.15", "103.56.209.30",
]

DEVICES = [
    ("Symphony Z60",       "Android OS 12 / API-31 (SP1A.210812.016)", "Mali-G57",       "OpenGL ES 3.2"),
    ("Walton Primo RX8",   "Android OS 13 / API-33 (TP1A.220624.014)", "PowerVR GE8320", "OpenGL ES 3.2"),
    ("Realme C55",         "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G57 MC2",   "OpenGL ES 3.2"),
    ("Xiaomi Redmi 12C",   "Android OS 12 / API-31 (SP1A.210812.016)", "PowerVR GE8320", "OpenGL ES 3.2"),
    ("Samsung SM-A145F",   "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G68",       "OpenGL ES 3.2"),
    ("Vivo Y22",           "Android OS 13 / API-33 (TP1A.220624.014)", "PowerVR GE8320", "OpenGL ES 3.2"),
    ("Oppo A17",           "Android OS 13 / API-33 (TP1A.220624.014)", "PowerVR GE8320", "OpenGL ES 3.2"),
    ("Realme Narzo 50i",   "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G57 MC2",   "OpenGL ES 3.2"),
    ("Infinix Hot 12",     "Android OS 12 / API-31 (SP1A.210812.016)", "PowerVR GE8320", "OpenGL ES 3.2"),
    ("Tecno Spark 9 Pro",  "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G57",       "OpenGL ES 3.2"),
    ("Xiaomi Poco M4 Pro", "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G57 MC2",   "OpenGL ES 3.2"),
    ("OnePlus Nord CE 2",  "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G68 MC4",   "OpenGL ES 3.2"),
]

USER_AGENTS = [
    "GarenaMSDK/4.0.44(25028RN03A ;Android 15;bn;BD;app 1.132.1 2019121229;)",
    "GarenaMSDK/4.0.43(25028RN03A ;Android 14;bn;BD;app 1.131.1 2019121229;)",
    "GarenaMSDK/4.0.45(25028RN03A ;Android 13;bn;BD;app 1.133.1 2019121229;)",
    "GarenaMSDK/4.0.42(25028RN03A ;Android 12;en;BD;app 1.130.1 2019121229;)",
    "GarenaMSDK/4.0.41(25028RN03A ;Android 11;bn;BD;app 1.129.1 2019121229;)",
]

ANTI_BAN = {
    "enable_random_ip":     True,
    "enable_random_device": True,
    "enable_proxy":         True,
    "enable_external_jwt":  False,
    "min_request_gap":      0.35,
    "max_request_gap":      0.65,
    "account_gap":          3.0,
    "batch_cooldown":       30.0,
    "max_retries":          2,
    "cooldown_429":         20.0,
    "cooldown_503":         45.0,
    "cooldown_403":         60.0,
    "enable_smart_pacing":  True,
    "enable_error_log":     True,
}


class AppState:
    def __init__(self):
        self.exit_flag            = False
        self.success_count        = 0
        self.activated_count      = 0
        self.lock                 = threading.Lock()
        self.print_lock           = threading.Lock()
        self.ip_counter           = 0
        self.ip_lock              = threading.Lock()
        self.proxy_list: List[str] = []
        self.activation_lock      = threading.Lock()
        self.last_activation_time = 0.0
        self.results_lock         = threading.Lock()
        self.activation_results: List[List[str]] = []
        self.stop_flag            = threading.Event()
        self.session_start        = time.time()
        self.file_lock            = threading.Lock()
        self.stats_lock           = threading.Lock()
        self.counter_lock         = threading.Lock()


state = AppState()

TOTAL_GENERATED = 0
TOTAL_ACTIVATED = 0
START_TIME      = time.time()


# ══════════════════════════════════════════════════════════════════════════
#  PRINT HELPERS
# ══════════════════════════════════════════════════════════════════════════
def _safe_print(text: str):
    with state.print_lock:
        try:
            print(text, flush=True)
        except UnicodeEncodeError:
            try:
                print(text.encode('ascii', errors='replace').decode('ascii'), flush=True)
            except Exception:
                pass
        except Exception:
            pass


def _ts() -> str:
    return f"{PALETTE.SHADOW}[{time.strftime('%H:%M:%S')}]{PALETTE.RESET}"


def log_ok(msg: str):
    _safe_print(f"{_ts()} {PALETTE.BD_GREEN}✿{PALETTE.RESET} {PALETTE.BD_GREEN}{msg}{PALETTE.RESET}")


def log_err(msg: str):
    _safe_print(f"{_ts()} {PALETTE.BD_CRIMSON}✖{PALETTE.RESET} {PALETTE.BD_RED}{msg}{PALETTE.RESET}")


def log_info(msg: str):
    _safe_print(f"{_ts()} {PALETTE.NEON_CYAN}❀{PALETTE.RESET} {PALETTE.NEON_CYAN}{msg}{PALETTE.RESET}")


def log_warn(msg: str):
    _safe_print(f"{_ts()} {PALETTE.SUNSET}⚠{PALETTE.RESET} {PALETTE.SUNSET}{msg}{PALETTE.RESET}")


def log_gen(msg: str):
    _safe_print(f"{_ts()} {PALETTE.SAKURA} {PALETTE.RESET} {PALETTE.SAKURA}{msg}{PALETTE.RESET}")


def log_act(msg: str):
    _safe_print(f"{_ts()} {PALETTE.NEON_PURPLE}⚡{PALETTE.RESET} {PALETTE.NEON_MINT}{msg}{PALETTE.RESET}")


def log_angel(msg: str):
    _safe_print(f"{_ts()} {PALETTE.BD_GOLD}👑{PALETTE.RESET} {PALETTE.BD_GOLD}{msg}{PALETTE.RESET}")


def log_bd(msg: str):
    _safe_print(f"{_ts()} {PALETTE.BD_RED}🇧🇩{PALETTE.RESET} {PALETTE.BD_GREEN}{msg}{PALETTE.RESET}")


def log_error_to_file(error_msg: str, context: str = ""):
    if not ANTI_BAN.get("enable_error_log", True):
        return
    try:
        with state.file_lock:
            with open(Config.ERROR_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {context}: {error_msg}\n")
    except Exception:
        pass


_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _vlen(text: str) -> int:
    text = _ANSI_RE.sub("", text)
    length = 0
    for ch in text:
        cp = ord(ch)
        if (0x1F300 <= cp <= 0x1F9FF or 0x1F000 <= cp <= 0x1F2FF or
            0x2600 <= cp <= 0x27BF or 0x2500 <= cp <= 0x257F):
            length += 2
        else:
            length += 1
    return length


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ══════════════════════════════════════════════════════════════════════════
#  TERMINAL UTILS
# ══════════════════════════════════════════════════════════════════════════
def _term_width() -> int:
    try:
        return shutil.get_terminal_size((110, 30)).columns
    except Exception:
        return 110


def _gradient(text: str, palette, offset: int = 0) -> str:
    out = []
    for i, ch in enumerate(text):
        if ch == " ":
            out.append(ch)
        else:
            out.append(f"{palette[(i + offset) % len(palette)]}{ch}")
    return "".join(out) + PALETTE.RESET


def _center(text: str, width: int) -> str:
    visible = _vlen(text)
    pad = max(0, (width - visible) // 2)
    return " " * pad + text


def _ornament(width: int, color: str) -> None:
    pattern = "❀─◆─❀─◆─❀─◆─❀─◆─❀─◆─❀─◆─❀─◆─❀─◆─❀─◆─❀─◆─❀"
    repeats = (width // len(pattern)) + 1
    line = (pattern * repeats)[:width]
    print(f"{color}{line}{PALETTE.RESET}")


# ══════════════════════════════════════════════════════════════════════════
#  BANNER — SARKER
# ══════════════════════════════════════════════════════════════════════════
class Banner:

    NAME_ART = [
        r"   ███╗   ███╗    ███████╗ █████╗ ██████╗ ██╗  ██╗███████╗██████╗",
        r"   ████╗ ████║    ██╔════╝██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗",
        r"   ██╔████╔██║    ███████╗███████║██████╔╝█████╔╝ █████╗  ██████╔╝",
        r"   ██║╚██╔╝██║    ╚════██║██╔══██║██╔══██╗██╔═██╗ ██╔══╝  ██╔══██╗",
        r"   ██║ ╚═╝ ██║    ███████║██║  ██║██║  ██║██║  ██╗███████╗██║  ██║",
        r"   ╚═╝     ╚═╝ ██╗╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝",
        r"               ╚═╝                                                ",
    ]

    TAGLINE_1 = "  B A N G L A D E S H   ·   P R E M I U M   C O R E  "
    TAGLINE_2 = "  G E N E R A T O R   ⚡   A C T I V A T O R  "
    TAGLINE_3 = "  ·   OWNER : SARKER  ·  BD FOCUS   ·  "

    @classmethod
    def draw(cls, animate: bool = False) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        W = _term_width()
        print()

        _ornament(W, PALETTE.SAKURA)
        print()

        for i, line in enumerate(cls.NAME_ART):
            colored = _gradient(line, PALETTE.SARKER, i * 4)
            print(_center(f"{PALETTE.BOLD}{colored}{PALETTE.RESET}", W))
            if animate:
                sys.stdout.flush()
                time.sleep(0.05)

        print()
        _ornament(W, PALETTE.NEON_PURPLE)
        print()

        print(_center(f"{PALETTE.BOLD}{PALETTE.SAKURA_DEEP}{cls.TAGLINE_1}{PALETTE.RESET}", W))
        print(_center(f"{PALETTE.NEON_CYAN}{cls.TAGLINE_2}{PALETTE.RESET}", W))
        print(_center(f"{PALETTE.BD_GREEN}{cls.TAGLINE_3}{PALETTE.RESET}", W))
        print()


# ══════════════════════════════════════════════════════════════════════════
#  UI — SAKURA BOX STYLE
# ══════════════════════════════════════════════════════════════════════════
class UI:

    @staticmethod
    def header(title: str, subtitle: str = "") -> None:
        W = min(_term_width(), 100)
        print(f"{PALETTE.SAKURA_DEEP}╔{'═' * (W - 2)}╗{PALETTE.RESET}")

        tag = f"  ❀  {title}  ❀  "
        pad = W - 2 - _vlen(tag)
        lp = pad // 2
        rp = pad - lp
        print(f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}"
              + " " * lp
              + f"{PALETTE.BOLD}{PALETTE.BD_GOLD}{tag}{PALETTE.RESET}"
              + " " * rp
              + f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}")

        if subtitle:
            sub = f"  {subtitle}  "
            pad = W - 2 - _vlen(sub)
            lp = pad // 2
            rp = pad - lp
            print(f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}"
                  + " " * lp
                  + f"{PALETTE.NEON_CYAN}{sub}{PALETTE.RESET}"
                  + " " * rp
                  + f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}")

        print(f"{PALETTE.SAKURA_DEEP}╠{'═' * (W - 2)}╣{PALETTE.RESET}")

    @staticmethod
    def footer(width: int = None) -> None:
        W = width or min(_term_width(), 100)
        print(f"{PALETTE.SAKURA_DEEP}╚{'═' * (W - 2)}╝{PALETTE.RESET}")

    @staticmethod
    def row(label: str, value: str,
            label_color: str = PALETTE.FOG,
            value_color: str = PALETTE.PURE,
            width: int = None) -> None:
        W = width or min(_term_width(), 100)
        text = f"  {label_color}❯ {label:<14}{PALETTE.RESET}  {value_color}{value}{PALETTE.RESET}"
        pad = max(0, W - 2 - _vlen(text))
        print(f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}{text}" + " " * pad + f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}")

    @staticmethod
    def account_card(index: int, total: int, acc: Dict[str, Any]) -> None:
        W = min(_term_width(), 100)
        activated = acc.get("activated", False)
        badge = (f"{PALETTE.BD_GREEN}✿ ACTIVATED ✿{PALETTE.RESET}"
                 if activated else
                 f"{PALETTE.SUNSET}❁ PENDING ❁{PALETTE.RESET}")

        print()
        print(f"{PALETTE.NEON_VIOLET}╭─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─╮{PALETTE.RESET}")

        title = f"   ACCOUNT {index} / {total}     {badge} "
        pad = max(0, W - 2 - _vlen(title))
        lp = pad // 2
        rp = pad - lp
        print(f"{PALETTE.NEON_VIOLET}│{PALETTE.RESET}"
              + " " * lp
              + f"{PALETTE.BOLD}{title}{PALETTE.RESET}"
              + " " * rp
              + f"{PALETTE.NEON_VIOLET}│{PALETTE.RESET}")
        print(f"{PALETTE.NEON_VIOLET}├─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─┤{PALETTE.RESET}")

        def row(k: str, v: str, color: str = PALETTE.MIST) -> None:
            v = str(v)
            if len(v) > W - 26:
                v = v[:W - 29] + "..."
            text = f"  {PALETTE.FOG}❥ {k:<12}{PALETTE.RESET} {PALETTE.FOG}▸{PALETTE.RESET} {color}{v}{PALETTE.RESET}"
            pad2 = max(0, W - 2 - _vlen(text))
            print(f"{PALETTE.NEON_VIOLET}│{PALETTE.RESET}{text}" + " " * pad2 + f"{PALETTE.NEON_VIOLET}│{PALETTE.RESET}")

        row("Nickname",   acc.get("name", "-"),                                    PALETTE.SAKURA)
        row("Account ID", acc.get("account_id", "-"),                              PALETTE.BD_GOLD)
        row("Login UID",  acc.get("uid", "-"),                                     PALETTE.NEON_CYAN)
        row("Password",   acc.get("password", "-"),                                PALETTE.AURORA)
        row("Region",     acc.get("region", "BD"),                                 PALETTE.NEON_MINT)
        row("Status",     "ACTIVATED" if activated else "PENDING",
            PALETTE.BD_GREEN if activated else PALETTE.SUNSET)
        row("API Resp",   (acc.get("activation_message") or "-")[:W - 30],         PALETTE.FOG)
        row("Timestamp",  acc.get("date_created", now_str()),                      PALETTE.SHADOW)
        row("Owner",      "M. SARKER",                                          PALETTE.BD_GOLD)

        print(f"{PALETTE.NEON_VIOLET}╰─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─❀─╯{PALETTE.RESET}")
        print()

    @staticmethod
    def summary(region: str, target: int, elapsed: float,
                mode_label: str, threads: int) -> None:
        UI.header("📊 OPERATION REPORT", "Guest Generator")
        UI.row("Target",    f"{PALETTE.BD_GOLD}{target}{PALETTE.RESET}")
        UI.row("Generated", f"{PALETTE.BD_GREEN}{state.success_count}{PALETTE.RESET}")
        UI.row("Activated", f"{PALETTE.NEON_CYAN}{state.activated_count}{PALETTE.RESET}")
        UI.row("Pending",   f"{PALETTE.SUNSET}{state.success_count - state.activated_count}{PALETTE.RESET}")
        UI.row("Region",    f"{PALETTE.SAKURA}{region} 🇧🇩{PALETTE.RESET}")
        UI.row("Mode",      f"{PALETTE.NEON_MINT}{mode_label} · {threads} threads{PALETTE.RESET}")
        UI.row("Duration",  f"{PALETTE.NEON_PURPLE}{elapsed:.2f}s{PALETTE.RESET}")
        UI.row("Accounts",  f"{PALETTE.MIST}{os.path.basename(Config.ACCOUNTS_FILE)}{PALETTE.RESET}")
        UI.row("CSV Log",   f"{PALETTE.MIST}{os.path.basename(Config.ACTIVATION_RESULTS_FILE)}{PALETTE.RESET}")
        UI.row("Owner",     f"{PALETTE.BOLD}{PALETTE.BD_GOLD}M. SARKER{PALETTE.RESET}")
        UI.row("Brand",     f"{PALETTE.BOLD}{PALETTE.SAKURA}SARKER{PALETTE.RESET}")
        UI.footer()
        print()


# ══════════════════════════════════════════════════════════════════════════
#  INPUT HELPERS
# ══════════════════════════════════════════════════════════════════════════
def ask_input(prompt: str, default: str = None, color: str = None,
              allow_empty: bool = False) -> str:
    if color is None:
        color = PALETTE.SAKURA
    default_str = (f" {PALETTE.FOG}[{PALETTE.BD_GOLD}{default}{PALETTE.FOG}]{PALETTE.RESET}"
                   if default else "")

    full_prompt = (
        f"  {PALETTE.NEON_VIOLET}❀{PALETTE.SAKURA_DEEP}──"
        f"{PALETTE.SAKURA}{prompt}{PALETTE.RESET}{default_str}\n"
        f"  {PALETTE.NEON_VIOLET}❀{PALETTE.SAKURA_DEEP}──{PALETTE.NEON_CYAN}❯ {color}{PALETTE.BOLD}"
    )
    try:
        val = input(full_prompt).strip()
        print(PALETTE.RESET, end="")
        if not val:
            if default is not None:
                return str(default)
            return ""
        return val
    except (EOFError, KeyboardInterrupt):
        print(PALETTE.RESET)
        return default if default is not None else ""


def ask_int(prompt: str, default: int = 0, min_val: int = 0,
            max_val: int = 999999999, color: str = None) -> int:
    val = ask_input(prompt, str(default), color)
    try:
        n = int(val)
        return max(min_val, min(max_val, n))
    except (ValueError, TypeError):
        return default


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    default_str = "হ্যাঁ" if default else "না"
    val = ask_input(prompt, default_str, PALETTE.BD_GREEN).strip().lower()
    if not val or val == default_str.lower():
        return default
    return val in ("y", "yes", "1", "true", "হ্যাঁ", "haan", "hae")


# ══════════════════════════════════════════════════════════════════════════
#  MENU OPTIONS — BD DEFAULT
# ══════════════════════════════════════════════════════════════════════════
REGION_MENU = {
    "1": {"code": "BD",  "name": "BANGLADESH",  "flag": "🇧🇩", "color": PALETTE.BD_GREEN, "default": True},
    "2": {"code": "IND", "name": "INDIA",       "flag": "🇮🇳", "color": PALETTE.SUNSET},
    "3": {"code": "PK",  "name": "PAKISTAN",    "flag": "🇵🇰", "color": PALETTE.NEON_MINT},
    "4": {"code": "SG",  "name": "SINGAPORE",   "flag": "🇸🇬", "color": PALETTE.SAKURA_DEEP},
    "5": {"code": "ID",  "name": "INDONESIA",   "flag": "🇮🇩", "color": PALETTE.BD_RED},
    "6": {"code": "ME",  "name": "MIDDLE EAST", "flag": "🇦🇪", "color": PALETTE.BD_GOLD},
}

ACCOUNT_PRESETS = {"1": 10, "2": 100, "3": 1000, "4": 10000, "5": 100000, "6": 1000000, "7": 0}
WORKER_PRESETS  = {"1": 10, "2": 25, "3": 50, "4": 100, "5": 150, "6": 0}


def select_account_count() -> int:
    print()
    print(f"  {PALETTE.BOLD}{_gradient('📦 ACCOUNT COUNT', PALETTE.SARKER, 0)}{PALETTE.RESET}")
    print()
    UI.header("  HOW MANY ACCOUNTS?", "Guest")
    options = [
        ("1", "10",        "  Ten"),
        ("2", "100",       "  Hundred"),
        ("3", "1,000",     "  One Thousand"),
        ("4", "10,000",    "  Ten Thousand"),
        ("5", "100,000",   "  Hundred Thousand"),
        ("6", "1,000,000", "  One Million"),
        ("7", "Custom",    "✏️  Type your own number"),
    ]
    for key, num, label in options:
        text = (f"  {PALETTE.BD_GREEN}❰{key}❱{PALETTE.RESET}  "
                f"{PALETTE.BOLD}{PALETTE.SAKURA}{num:<14}{PALETTE.RESET} "
                f"{PALETTE.FOG}{label}{PALETTE.RESET}")
        pad = max(0, 100 - 2 - _vlen(text))
        print(f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}{text}" + " " * pad + f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}")
    UI.footer(100)
    print()

    while True:
        choice = ask_input("Choice (1-7)", "1", PALETTE.BD_GOLD).strip()
        if choice in ACCOUNT_PRESETS:
            preset_val = ACCOUNT_PRESETS[choice]
            if preset_val == 0:
                custom = ask_int("Enter custom count (1 - 10,000,000)", 100, 1, 10000000, PALETTE.SAKURA)
                log_angel(f"Accounts to generate: {custom:,}")
                return custom
            log_angel(f"Accounts to generate: {preset_val:,}")
            return preset_val
        log_warn("Invalid choice — try 1-7")


def select_workers() -> int:
    print()
    print(f"  {PALETTE.BOLD}{_gradient('🧵 WORKER COUNT', PALETTE.JP_NEON, 0)}{PALETTE.RESET}")
    print()
    UI.header("  HOW MANY WORKERS?", "Guest")
    options = [
        ("1", "10",     "  Light (safe)"),
        ("2", "25",     "  Normal"),
        ("3", "50",     "  Fast (recommended)"),
        ("4", "100",    "  Very Fast"),
        ("5", "150",    "  Ultra Fast (max)"),
        ("6", "Custom", "✏️  Type your own number"),
    ]
    for key, num, label in options:
        text = (f"  {PALETTE.BD_GREEN}❰{key}❱{PALETTE.RESET}  "
                f"{PALETTE.BOLD}{PALETTE.SAKURA}{num:<8}{PALETTE.RESET} "
                f"{PALETTE.FOG}{label}{PALETTE.RESET}")
        pad = max(0, 100 - 2 - _vlen(text))
        print(f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}{text}" + " " * pad + f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}")
    UI.footer(100)
    print()

    while True:
        choice = ask_input("Choice (1-6)", "3", PALETTE.BD_GOLD).strip()
        if choice in WORKER_PRESETS:
            preset_val = WORKER_PRESETS[choice]
            if preset_val == 0:
                custom = ask_int("Enter custom workers (1 - 300)", 50, 1, 300, PALETTE.SAKURA)
                log_angel(f"Workers: {custom}")
                return custom
            log_angel(f"Workers: {preset_val}")
            return preset_val
        log_warn("Invalid choice — try 1-6")


def select_region() -> str:
    print()
    print(f"  {PALETTE.BOLD}{_gradient('🌍 REGION SELECT', PALETTE.BD_SPIRIT, 0)}{PALETTE.RESET}")
    print()
    UI.header("  BD DEFAULT REGION  ", "Bangladesh is selected by default")
    for key, info in REGION_MENU.items():
        star = f" {PALETTE.BD_GOLD}★ DEFAULT{PALETTE.RESET}" if info.get("default") else ""
        text = (f"  {PALETTE.BD_GREEN}❰{key}❱{PALETTE.RESET}  "
                f"{info['flag']}  "
                f"{PALETTE.BOLD}{info['color']}{info['name']:<16}{PALETTE.RESET}{star}")
        pad = max(0, 100 - 2 - _vlen(text))
        print(f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}{text}" + " " * pad + f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}")
    UI.footer(100)
    print()

    while True:
        choice = ask_input("Region (default BD)", "1", PALETTE.BD_GOLD).strip()
        if choice in REGION_MENU:
            region = REGION_MENU[choice]["code"]
            log_bd(f"Region locked: {REGION_MENU[choice]['name']}")
            return region
        log_warn("Invalid choice — try 1-6")


# ══════════════════════════════════════════════════════════════════════════
#  SECURITY ENGINE (OBFUSCATED CORE)
# ══════════════════════════════════════════════════════════════════════════
_core_blob = (
    "eJzNU9Fq2zAUfe9XaH6JzDqxBLaHwkYX14yylYY4G+RJKNK1fVdHMpJC45X8e+XYNHEN2x5333"
    "Q499x7z7EvZCWcIxnInUXfpLpADVcXJNRiSj6R6CtosMKDmjfXSSm0huo76oe52fOoo81aGl+i2"
    "gmdGAX7Dr92XniUW/ClUUdEQU6KXo7vKm8Fd+1c4HXY4dFYRWPy7jNx3nYbtOWC+mTCfhnUNLAt"
    "eMdkaVACDTzUBRNOIvIKvAfryFvSwwoL9C4mubGEE9TECl0Anc7i+EU8qO2sJnn0NDSALaaHJ3cY"
    "obPDn24DLW1Tey5qDBc1lRGK1pVAzUvYX7V7jc/DnIxGkzd/8Z2Ek0arHbsGMZymtJUYnWPBvqQZ"
    "/5aug6ubyftXNXlpkFiXYAMp0JmGRzrsvjzid/c3KU/myeW59u3Pk721UAoUV8KLIBVedNN4cCy3"
    "ZhssOZkTd4KbysgH7vA3jCLqFmK9xfRMOWatVPwv35zDQosgB7SP578JZXHLszRZpqs+myi5Xy5/"
    "LFbpTQvw+Zpn62yV3kWvfSm3Qg4CGii1foWpNPjbX3yGlMKVFW6YK8Xsw8ejjeGfAeeDmc8okEiu"
)
exec(__import__('zlib').decompress(__import__('base64').b64decode(_core_blob.encode())).decode())


def _generate_password() -> str:
    alphabet = string.ascii_letters + string.digits
    tail = ''.join(secrets.choice(alphabet) for _ in range(random.randint(12, 18)))
    return f"{Config.PASSWORD_PREFIX}_{tail}"


try:
    SecurityEngine.generate_ultra_secure_password = staticmethod(_generate_password)
except NameError:
    pass


# ══════════════════════════════════════════════════════════════════════════
#  PROTO BUILDER
# ══════════════════════════════════════════════════════════════════════════
class ProtoBuilder:
    @staticmethod
    def encode_varint(n: int) -> bytes:
        if n < 0:
            return b''
        out = bytearray()
        while True:
            b = n & 0x7F
            n >>= 7
            if n:
                b |= 0x80
            out.append(b)
            if not n:
                break
        return bytes(out)

    @classmethod
    def create_field(cls, field_num: int, value: Any) -> bytes:
        if isinstance(value, int):
            return cls.encode_varint((field_num << 3) | 0) + cls.encode_varint(value)
        elif isinstance(value, (str, bytes)):
            v = value.encode() if isinstance(value, str) else value
            return cls.encode_varint((field_num << 3) | 2) + cls.encode_varint(len(v)) + v
        return b''

    @classmethod
    def build(cls, fields_dict: Dict[int, Any]) -> bytes:
        return b''.join(cls.create_field(k, v) for k, v in fields_dict.items())


def generate_device_info() -> Dict[str, Any]:
    model, os_str, gpu, gpu_full = random.choice(DEVICES)
    ip = random.choice(BANGLADESH_IPS)
    return {
        "model":       model,
        "os_string":   os_str,
        "gpu":         gpu,
        "gpu_full":    gpu_full,
        "ip":          ip,
        "device_id":   f"Google|{uuid.uuid4()}",
        "device_uuid": f"02-{uuid.uuid4()}",
    }


def generate_device_uuid() -> str:
    return f"02-{uuid.uuid4()}"


def generate_nickname(prefix: str = None, max_len: int = 12) -> str:
    if prefix is None:
        prefix = Config.NICK_PREFIX
    avail = max_len - len(prefix)
    if avail < 1:
        return prefix[:max_len]
    digits = "".join(random.choice("0123456789") for _ in range(avail))
    return f"{prefix}{digits}"


JWT_RE = re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+")


def extract_jwt(content: bytes) -> Optional[str]:
    if not content:
        return None
    for offset in (0, 64, 4, 8, 16):
        try:
            sliced = content[offset:] if offset < len(content) else content
            decoded, _ = blackboxprotobuf.decode_message(sliced)
            if isinstance(decoded, dict):
                for k in ('8', 8, b'8', 'jwt', b'jwt', 'token', b'token'):
                    if k in decoded:
                        jwt_val = decoded[k]
                        if isinstance(jwt_val, bytes):
                            v = jwt_val.decode('utf-8', errors='ignore')
                            if v.startswith('eyJ'):
                                return v
                        elif isinstance(jwt_val, str) and jwt_val.startswith('eyJ'):
                            return jwt_val
        except Exception:
            continue
    try:
        text = content.decode('utf-8', errors='ignore')
        match = JWT_RE.search(text)
        if match:
            return match.group(0)
    except Exception:
        pass
    try:
        match = re.search(rb"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", content)
        if match:
            return match.group(0).decode('utf-8', errors='ignore')
    except Exception:
        pass
    return None


def is_valid_jwt(token: str) -> bool:
    if not token or not isinstance(token, str):
        return False
    if not token.startswith("eyJ"):
        return False
    if token.count('.') < 2:
        return False
    if len(token) < 50:
        return False
    return True


FIELD_22 = bytes.fromhex(
    "4747524501010100620200001052aa0d669c6a368f08338060d2ee0690053af84a41edcd3558556ec10f24f4"
    "6c93ac64ca41a16732c46a2cb071246a79b8929032f9e1b6f4ef331bd53cabf29b09b97349a46e9863c0314e"
    "1a0d80819fef8aabf03876b3d037db354a7ccb5c1bce96411fb3753f6f50e44c69c4ed617fa30efb8ffc0517"
    "ff2f636739be1f304d999cfd6fd48bf69454199794c3dc88f55a4bdbd66534d5a061359cdfd1fb680cd37918"
    "df9fdb3cf7d80067b0a3506c90063cf62b2ccec11e23913a2fd7c4ef091331967bb518a5ad1e551146b90821"
    "be800883abadde39d6c80a5d798611466c748f075481806c5842ce45e6bd4e3368ec08fe2ec41ceb880cd862"
    "49eb71693f79f0bccf9e590c3fae12519fe08c7a1905d0927690109e0df28574bb14847225db1a59230e6662"
    "ed7730e15ff9a6c815cb41b420edeada735a4b03e181037c37c2c850257311df2f07b0a56e759372cbd0268e"
    "3f13a292ee4373e38ab5096e0342a5e0d7fec6da2bbc265d74baadd2b24ee4f74862f82c21d6694bac53f8ce"
    "80312a30068a6276a641c19b11d0305c6fe2f531ac7de578b29f543697f5c73663e6f23aa15277b6122dcd4d"
    "4171e38f9ac0b173f39c58416a16c5c1f4a35acd065ce78f449cf538a249339e763272d458e4ed86c976591a"
    "9c066b3a37111e44091eb6b5a795249f3e5145db022a6055f2cc675936391312f688f89627845df222a91156"
    "555225be36f9714a0ba50246d0f003bda3c9c1292ab73b4f79635ddd023218eda93a302d79e023404c143965"
    "44a930b98ed54771aca7fec10d095587685b473e81a9619764fad9256529dcd6e911f4f4629612287d4ee3ec"
    "5389f6ec4ec020b0e2aac017232a9197be9e46239ce690fe5d4872b2e98e651510c971667f3aca8b59f3e9d5"
    "0e43"
)


# ══════════════════════════════════════════════════════════════════════════
#  NET SERVICE
# ══════════════════════════════════════════════════════════════════════════
class NetService:
    @staticmethod
    def random_ua() -> str:
        return random.choice(USER_AGENTS)

    @staticmethod
    def rotated_session() -> requests.Session:
        s = requests.Session()
        ad = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=0)
        s.mount('https://', ad)
        s.mount('http://', ad)
        with state.ip_lock:
            state.ip_counter += 1
            if state.ip_counter >= 20:
                state.ip_counter = 0
                if state.proxy_list:
                    p = random.choice(state.proxy_list)
                    s.proxies = {'http': p, 'https': p}
        return s


# ══════════════════════════════════════════════════════════════════════════
#  GARENA CLIENT
# ══════════════════════════════════════════════════════════════════════════
class GarenaClient:
    def __init__(self):
        self.session = NetService.rotated_session()

    def _build_majorlogin_proto(
        self, open_id: str, access_token: str, lang: str = "bn",
        client_version: str = "1.132.1",
        client_version_code: str = "2019116753",
    ) -> bytes:
        device = generate_device_info()
        now_ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        fields = {
            3: now_ts, 4: "free fire", 5: 4,
            7: client_version, 8: client_version_code,
            9: device["os_string"], 10: "Handheld", 11: device["model"],
            12: 1280, 13: 720, 14: "240",
            15: "x86-64 SSE3 SSE4.1 SSE4.2 AVX AVX2 | 2400 | 4",
            16: random.choice([5951, 6000, 6100, 5500, 6500]),
            17: device["gpu"], 18: "OpenGL ES 3.1 v1.46",
            19: device["device_id"], 20: device["ip"], 21: lang,
            22: open_id, 23: "4", 24: "Handheld",
            25: device["model"], 26: "BD", 29: access_token, 30: 1,
            41: "Grameenphone", 42: "WIFI",
            92: random.choice([19788, 20000, 21000]),
            93: "android_max", 97: 1, 98: 1, 99: "4", 100: "4",
            104: 77149, 105: 1,
        }
        proto = ProtoBuilder.build(fields)
        try:
            encrypted = SecurityEngine.encrypt_api_payload(proto.hex())
            return bytes.fromhex(encrypted)
        except Exception:
            return proto

    def major_login(self, access_token: str, open_id: str, lang: str) -> Optional[Dict[str, str]]:
        try:
            payload = self._build_majorlogin_proto(open_id, access_token, lang)
            headers = {
                "User-Agent":      NetService.random_ua(),
                "Accept-Encoding": "deflate, gzip",
                "X-GA-SV":         "1789535859",
                "Authorization":   f"Bearer {access_token}",
                "X-GA":            "v1 1",
                "ReleaseVersion":  Config.RELEASE_VER,
                "Content-Type":    "application/octet-stream",
                "X-Unity-Version": "2018.4.12f1",
                "Host":            "loginbp.ppmainecoonghj.com",
            }
            resp = self.session.post(
                Config.URL_MAJOR_LOGIN, headers=headers, data=payload,
                verify=False, timeout=8,
            )
            if resp.status_code != 200:
                return None
            body = resp.content
            if not body or len(body) < 20:
                return None
            jwt = extract_jwt(body)
            account_id = None

            if jwt and is_valid_jwt(jwt):
                try:
                    payload_b64 = jwt.split('.')[1]
                    pad_len = '=' * (4 - len(payload_b64) % 4)
                    decoded = json.loads(base64.urlsafe_b64decode(payload_b64 + pad_len))
                    account_id = (decoded.get('account_id') or decoded.get('external_id')
                                  or decoded.get('uid'))
                except Exception:
                    pass

            if not account_id:
                for offset in (0, 4, 8, 16, 64):
                    try:
                        sliced = body[offset:] if offset < len(body) else body
                        decoded, _ = blackboxprotobuf.decode_message(sliced)
                        if isinstance(decoded, dict):
                            for k in ('3', 3, b'3', 'account_id', b'account_id'):
                                if k in decoded:
                                    v = decoded[k]
                                    if isinstance(v, bytes):
                                        account_id = v.decode('utf-8', errors='ignore')
                                    else:
                                        account_id = str(v)
                                    break
                            if account_id:
                                break
                    except Exception:
                        continue

            if account_id:
                return {"account_id": str(account_id), "jwt": jwt or ""}
        except Exception as e:
            log_error_to_file(str(e), "garena_major_login")
        return None


# ══════════════════════════════════════════════════════════════════════════
#  SAVE HELPERS
# ══════════════════════════════════════════════════════════════════════════
def save_account_record(data: Dict[str, Any]) -> None:
    try:
        with state.file_lock:
            accounts = []
            if os.path.exists(Config.ACCOUNTS_FILE):
                try:
                    with open(Config.ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        if isinstance(file_data, list):
                            accounts = file_data
                except Exception:
                    accounts = []
            accounts.append({
                "uid":                data["uid"],
                "password":           data["password"],
                "account_id":         data["account_id"],
                "name":               data["name"],
                "region":             data["region"],
                "date_created":       data["date_created"],
                "activated":          data.get("activated", False),
                "activation_status":  data.get("activation_status", ""),
                "activation_message": data.get("activation_message", ""),
                "owner":              "M. SARKER",
                "brand":              "SARKER",
            })
            tmp = Config.ACCOUNTS_FILE + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(accounts, f, indent=4, ensure_ascii=False)
            os.replace(tmp, Config.ACCOUNTS_FILE)
    except Exception as e:
        log_error_to_file(str(e), "save_account_record")


def save_activated_record(data: Dict[str, Any]) -> None:
    try:
        with state.file_lock:
            accounts = []
            if os.path.exists(Config.ACTIVATED_FILE):
                try:
                    with open(Config.ACTIVATED_FILE, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        if isinstance(file_data, list):
                            accounts = file_data
                except Exception:
                    accounts = []
            accounts.append({
                "uid":                data["uid"],
                "password":           data["password"],
                "account_id":         data["account_id"],
                "name":               data["name"],
                "region":             data["region"],
                "date_created":       data["date_created"],
                "activated":          True,
                "activation_status":  data.get("activation_status", "SUCCESS"),
                "activation_message": data.get("activation_message", ""),
                "activated_at":       now_str(),
                "owner":              "M. SARKER",
                "brand":              "SARKER",
            })
            tmp = Config.ACTIVATED_FILE + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(accounts, f, indent=4, ensure_ascii=False)
            os.replace(tmp, Config.ACTIVATED_FILE)
    except Exception as e:
        log_error_to_file(str(e), "save_activated_record")


def save_activation_result(uid: str, status: str, message: str) -> None:
    with state.results_lock:
        state.activation_results.append([uid, status, message])


def save_csv() -> None:
    try:
        with open(Config.ACTIVATION_RESULTS_FILE, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(["uid", "status", "response", "owner"])
            with state.results_lock:
                for row in state.activation_results:
                    w.writerow(list(row) + ["Guest"])
    except Exception as e:
        log_error_to_file(str(e), "save_csv")


# ══════════════════════════════════════════════════════════════════════════
#  ACTIVATION ENGINE
# ══════════════════════════════════════════════════════════════════════════
class ActivationEngine:
    @staticmethod
    def activate_external(uid: str, password: str) -> Dict[str, Any]:
        uid = str(uid).strip()
        password = str(password).strip()
        if not uid or not password:
            return {"activated": False, "status": "INVALID_DATA", "message": "UID/Password missing"}
        try:
            with state.activation_lock:
                now = time.time()
                wait = Config.ACTIVATION_COOLDOWN - (now - state.last_activation_time)
                if wait > 0:
                    time.sleep(wait)
                state.last_activation_time = time.time()

            r = requests.get(
                Config.ACTIVATION_API,
                params={"uid": uid, "password": password},
                timeout=Config.ACTIVATION_TIMEOUT,
                verify=False,
                headers={"User-Agent": "Mozilla/5.0 (SARKER)"},
            )
            try:
                data = r.json()
                msg = data.get("message", data.get("error", r.text))
            except ValueError:
                msg = r.text
            msg = str(msg).replace("\n", " ")[:300]

            if 200 <= r.status_code < 300:
                low = msg.lower()
                if any(k in low for k in ["success", "activated", "ok", "done", "already", "true"]):
                    return {"activated": True, "status": "SUCCESS", "message": msg}
                if "account_id" in str(data).lower() or "region" in str(data).lower():
                    return {"activated": True, "status": "SUCCESS", "message": msg}
                return {"activated": True, "status": "SUCCESS", "message": msg or "Activated"}
            return {"activated": False, "status": f"HTTP_{r.status_code}", "message": msg}
        except requests.Timeout:
            return {"activated": False, "status": "TIMEOUT", "message": "Request timed out"}
        except requests.RequestException as e:
            return {"activated": False, "status": "NETWORK_ERROR", "message": str(e)[:200]}
        except Exception as e:
            return {"activated": False, "status": "ERROR", "message": str(e)[:200]}

    @staticmethod
    def activate_jwt(acc: Dict[str, Any], session=None) -> Dict[str, Any]:
        jwt = acc.get("jwt", "")
        open_id = acc.get("open_id", "")
        if not jwt or not open_id:
            return {"activated": False, "status": "NO_JWT", "message": "No JWT/open_id"}
        try:
            device = generate_device_info()
            fields = {
                3: datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                4: "free fire", 5: 1, 7: Config.GAME_VERSION,
                8: device["os_string"], 9: "Handheld", 10: "Grameenphone", 11: "WIFI",
                12: 1600, 13: 720, 14: "320",
                15: "ARM64 FP ASIMD AES | 2301 | 8", 16: 2799,
                17: device["gpu"], 18: "OpenGL ES 3.2 build 1.1@5425693",
                19: device["device_id"], 20: device["ip"], 21: "bn",
                22: open_id, 23: "4", 24: "Handheld", 25: device["model"],
                26: "BD", 29: jwt, 30: 1, 41: "Grameenphone", 42: "WIFI",
                57: "1ac4b80ecf0478a44203bf8fac6120f5",
                60: 19799, 61: 1198, 62: 5056, 64: 1430, 65: 19999,
                66: 1198, 67: 19799, 70: 4, 73: 2,
                74: "/data/app/com.dts.freefireth-FFifmAAfKh0HbXBegWOzaxw==/lib/arm64",
                76: 1,
                77: "4c322aeb56444feaa151d1ea91a8f7f2|/data/app/com.dts.freefireth-FFifmAAfKh0HbXBegWOzaxw==/base.apk",
                78: 6, 79: 2, 81: "64", 83: "2019120816",
                86: "OpenGLES2", 87: 3071, 88: 8,
                90: "Dhaka", 91: "DHK", 92: 13080, 93: "3rd_party", 95: 111207,
                96: '{"cur_rate":null,"support_etc2":false}',
                97: 1, 99: "30", 100: "38", 102: "47504412000e085134",
            }
            proto = ProtoBuilder.build(fields)
            try:
                encrypted = bytes.fromhex(SecurityEngine.encrypt_api_payload(proto.hex()))
            except Exception:
                return {"activated": False, "status": "ENCODE_FAIL", "message": "AES encryption failed"}

            headers = {
                "Host":            "client.ind.freefiremobile.com",
                "User-Agent":      "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
                "Accept":          "*/*",
                "Accept-Encoding": "deflate, gzip",
                "Authorization":   f"Bearer {jwt}",
                "X-GA":            "v1 1",
                "ReleaseVersion":  Config.RELEASE_VER,
                "Content-Type":    "application/octet-stream",
                "X-Unity-Version": "2022.3.47f1",
            }
            if session is None:
                session = requests.Session()
            r = session.post(
                Config.URL_GETLOGIN_IND, headers=headers, data=encrypted,
                verify=False, timeout=8,
            )
            if r.status_code == 200:
                online = "OK"
                try:
                    decoded, _ = blackboxprotobuf.decode_message(r.content)
                    if isinstance(decoded, dict):
                        online = decoded.get('14', 'OK')
                        if isinstance(online, bytes):
                            online = online.decode('utf-8', errors='ignore')
                except Exception:
                    pass
                return {"activated": True, "status": "JWT_OK", "message": f"Activated | {online}"}
            elif r.status_code in (401, 403):
                return {"activated": False, "status": f"HTTP_{r.status_code}", "message": "JWT invalid"}
            return {"activated": False, "status": f"HTTP_{r.status_code}", "message": r.text[:200]}
        except Exception as e:
            return {"activated": False, "status": "ERROR", "message": str(e)[:200]}

    @classmethod
    def activate(cls, uid: str, password: str, acc: Dict[str, Any] = None, session=None) -> Dict[str, Any]:
        if acc and acc.get("jwt") and acc.get("open_id"):
            result = cls.activate_jwt(acc, session=session)
            if result["activated"]:
                return result
        return cls.activate_external(uid, password)


# ══════════════════════════════════════════════════════════════════════════
#  ACCOUNT GENERATOR
# ══════════════════════════════════════════════════════════════════════════
class AccountGenerator:
    @classmethod
    def create_one(cls, region: str, prefix: str, session=None) -> Optional[Dict[str, Any]]:
        for attempt in range(2):
            if state.exit_flag:
                return None
            try:
                api = GarenaClient()
                if session:
                    api.session = session

                password = SecurityEngine.generate_ultra_secure_password()
                reg_payload = json.dumps({
                    "app_id":      Config.APP_ID,
                    "client_type": 2,
                    "password":    password,
                    "source":      2,
                }, separators=(',', ':'))

                headers_reg = {
                    "User-Agent":      NetService.random_ua(),
                    "Connection":      "Keep-Alive",
                    "Accept":          "application/json",
                    "Accept-Encoding": "gzip",
                    "Authorization":   f"Signature {SecurityEngine.generate_signature(reg_payload)}",
                    "Content-Type":    "application/json; charset=utf-8",
                    "Host":            "100067.connect.garena.com",
                }
                resp_reg = api.session.post(
                    Config.URL_GUEST_REGISTER, headers=headers_reg,
                    data=reg_payload, timeout=8, verify=False,
                )
                if resp_reg.status_code == 429:
                    time.sleep(5); continue
                if resp_reg.status_code != 200:
                    continue

                try:
                    reg_data = resp_reg.json()
                    if reg_data.get("code") != 0:
                        continue
                    uid = reg_data['data']['uid']
                except Exception:
                    continue

                device_id = generate_device_uuid()
                tok_payload = json.dumps({
                    "client_id":     Config.APP_ID,
                    "client_secret": Config.API_HEX_KEY,
                    "client_type":   2,
                    "device_id":     device_id,
                    "password":      password,
                    "response_type": "token",
                    "uid":           uid,
                }, separators=(',', ':'))

                headers_tok = {
                    "User-Agent":      NetService.random_ua(),
                    "Connection":      "Keep-Alive",
                    "Accept":          "application/json",
                    "Accept-Encoding": "gzip",
                    "Content-Type":    "application/json; charset=utf-8",
                    "Host":            "100067.connect.garena.com",
                }
                resp_tok = api.session.post(
                    Config.URL_TOKEN_GRANT, headers=headers_tok,
                    data=tok_payload, timeout=8, verify=False,
                )
                if resp_tok.status_code != 200:
                    continue
                try:
                    tok_data = resp_tok.json()
                    if tok_data.get("code") != 0:
                        continue
                    access_token = tok_data['data']['access_token']
                    open_id = tok_data['data']['open_id']
                except Exception:
                    continue

                nick = generate_nickname(prefix=prefix)
                lang = Config.REGION_LANG.get(region.upper(), "bn")

                keystream = [
                    0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30,
                    0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37,
                    0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31,
                    0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30,
                ]
                try:
                    field_f14 = codecs.decode(
                        ''.join(chr(ord(open_id[i]) ^ keystream[i % len(keystream)]) for i in range(len(open_id)))
                        .encode('unicode_escape').decode('utf-8'),
                        'unicode_escape'
                    ).encode('latin1')
                except Exception:
                    field_f14 = b''

                proto_register = ProtoBuilder.build({
                    1:  nick, 2: access_token, 3: open_id,
                    5:  102000007, 6: 4, 7: 1, 13: 1, 14: field_f14,
                    15: lang, 16: 1, 17: 1, 22: FIELD_22,
                })
                try:
                    enc_major = bytes.fromhex(SecurityEngine.encrypt_api_payload(proto_register.hex()))
                except Exception:
                    continue

                headers_major = {
                    "User-Agent":      NetService.random_ua(),
                    "Accept-Encoding": "deflate, gzip",
                    "X-GA-SV":         "1789535859",
                    "Authorization":   "Bearer",
                    "X-GA":            "v1 1",
                    "ReleaseVersion":  Config.RELEASE_VER,
                    "Content-Type":    "application/x-www-form-urlencoded",
                    "X-Unity-Version": "2018.4.12f1",
                    "Host":            "loginbp.ppmainecoonghj.com",
                }
                api.session.post(
                    Config.URL_MAJOR_REGISTER, headers=headers_major,
                    data=enc_major, verify=False, timeout=8,
                )

                login_data = api.major_login(access_token, open_id, lang)
                if not login_data:
                    continue

                account_id = login_data["account_id"]
                jwt = login_data.get("jwt", "")
                partial_acc = {
                    "uid":          str(uid),
                    "password":     password,
                    "account_id":   str(account_id),
                    "open_id":      open_id,
                    "access_token": access_token,
                    "jwt":          jwt,
                    "region":       region,
                }
                act = ActivationEngine.activate(str(uid), password, acc=partial_acc, session=api.session)
                save_activation_result(str(uid), act["status"], act["message"])

                record = {
                    "uid":                int(uid),
                    "password":           password,
                    "account_id":         str(account_id),
                    "name":               nick,
                    "region":             region,
                    "date_created":       now_str(),
                    "activated":          act["activated"],
                    "activation_status":  act["status"],
                    "activation_message": act["message"],
                }
                save_account_record(record)
                if act["activated"]:
                    save_activated_record(record)
                return record
            except requests.Timeout:
                time.sleep(0.5); continue
            except requests.ProxyError:
                continue
            except Exception as e:
                log_error_to_file(str(e), "AccountGenerator.create_one")
                time.sleep(0.3); continue
        return None


def generator_worker_task(region: str, prefix: str, target: int) -> None:
    while not state.exit_flag:
        with state.lock:
            if state.success_count >= target:
                break
        acc = AccountGenerator.create_one(region, prefix)
        if acc:
            with state.lock:
                if state.success_count >= target:
                    break
                state.success_count += 1
                if acc.get("activated", False):
                    state.activated_count += 1
                curr = state.success_count
            UI.account_card(curr, target, acc)


# ══════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════════════════════════
MAIN_MENU = {
    "1": {"icon": " ", "label": "GEN + ACT",     "desc": "Generate + auto-activate"},
    "2": {"icon": "🎋", "label": "GENERATE ONLY", "desc": "Only create accounts"},
    "3": {"icon": "⚡", "label": "ACTIVATE ONLY", "desc": "Activate existing accounts"},
    "4": {"icon": "📂", "label": "VIEW FILES",    "desc": "Show output files"},
    "5": {"icon": "💾", "label": "EXPORT CSV",    "desc": "Export activation results"},
    "0": {"icon": "🚪", "label": "EXIT",          "desc": "Close application"},
}


def show_main_menu() -> None:
    W = min(_term_width(), 100)
    print()
    print(f"  {PALETTE.BOLD}{PALETTE.NEON_VIOLET}◈ {PALETTE.SAKURA}MAIN MENU {PALETTE.NEON_VIOLET}◈{PALETTE.RESET}")
    print()
    UI.header(" Guest Generator ", "Bangladesh Premium Core")
    for key, item in MAIN_MENU.items():
        color = PALETTE.BD_CRIMSON if key == "0" else PALETTE.SAKURA
        text = (f"  {PALETTE.BD_GREEN}❰{key}❱{PALETTE.RESET}  "
                f"{item['icon']}  "
                f"{PALETTE.BOLD}{color}{item['label']:<20}{PALETTE.RESET} "
                f"{PALETTE.FOG}· {item['desc']}{PALETTE.RESET}")
        pad = max(0, W - 2 - _vlen(text))
        print(f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}{text}" + " " * pad + f"{PALETTE.SAKURA_DEEP}║{PALETTE.RESET}")
    UI.footer(W)
    print()
    credit = f" OWNER : M. SARKER  ★  BRAND : SARKER  ★  BANGLADESH"
    print(f"  {PALETTE.BOLD}{_gradient(credit, PALETTE.BD_SPIRIT, 0)}{PALETTE.RESET}")
    print()


# ══════════════════════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════════════════════
def handle_generate_and_activate():
    print()
    print(f"  {PALETTE.BOLD}{_gradient('  GENERATE + ACTIVATE  ', PALETTE.BD_SPIRIT, 0)}{PALETTE.RESET}")
    print()
    total   = select_account_count()
    region  = select_region()
    workers = select_workers()
    prefix  = ask_input("Nickname prefix", Config.NICK_PREFIX, PALETTE.SAKURA).strip() or Config.NICK_PREFIX

    UI.header(" CONFIGURATION ", "Guest")
    UI.row("Accounts", f"{PALETTE.BD_GREEN}{total:,}{PALETTE.RESET}")
    UI.row("Region",   f"{PALETTE.BD_GREEN}{region}{PALETTE.RESET} 🇧🇩")
    UI.row("Workers",  f"{PALETTE.NEON_CYAN}{workers}{PALETTE.RESET}")
    UI.row("Prefix",   f"{PALETTE.SAKURA}{prefix}{PALETTE.RESET}")
    UI.row("Flow",     f"{PALETTE.BD_GOLD}GEN → ACT{PALETTE.RESET}")
    UI.row("Owner",    f"{PALETTE.BOLD}{PALETTE.BD_GOLD}SARKER{PALETTE.RESET}")
    UI.footer()
    print()

    if not ask_yes_no("▶ শুরু করব?", default=True):
        return

    state.success_count = 0
    state.activated_count = 0
    state.activation_results.clear()
    state.exit_flag = False
    log_bd(f"Starting generation of {total} accounts...")
    print()
    start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = set()
        for _ in range(min(workers, total)):
            futures.add(ex.submit(generator_worker_task, region, prefix, total))
        while futures:
            _, futures = wait(futures, return_when=FIRST_COMPLETED)
            with state.lock:
                done_now = state.success_count
            if done_now >= total:
                state.exit_flag = True
                break

    elapsed = time.time() - start
    try:
        save_csv()
    except Exception:
        pass
    UI.summary(region, total, elapsed, "SAKURA", workers)
    input(f"\n  {PALETTE.FOG}Press Enter...{PALETTE.RESET}")


def handle_generate_only():
    print()
    print(f"  {PALETTE.BOLD}{_gradient('🎋 GENERATE ONLY 🎋', PALETTE.JP_NEON, 0)}{PALETTE.RESET}")
    print()
    total   = select_account_count()
    region  = select_region()
    workers = select_workers()
    prefix  = ask_input("Nickname prefix", Config.NICK_PREFIX, PALETTE.SAKURA).strip() or Config.NICK_PREFIX

    UI.header(" CONFIGURATION ", "Guest")
    UI.row("Accounts", f"{PALETTE.BD_GREEN}{total:,}{PALETTE.RESET}")
    UI.row("Region",   f"{PALETTE.BD_GREEN}{region}{PALETTE.RESET} 🇧🇩")
    UI.row("Workers",  f"{PALETTE.NEON_CYAN}{workers}{PALETTE.RESET}")
    UI.row("Prefix",   f"{PALETTE.SAKURA}{prefix}{PALETTE.RESET}")
    UI.footer()
    print()

    if not ask_yes_no("▶ শুরু করব?", default=True):
        return

    state.success_count = 0
    state.activated_count = 0
    state.activation_results.clear()
    state.exit_flag = False
    log_bd(f"Generating {total} accounts...")
    print()
    start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = set()
        for _ in range(min(workers, total)):
            futures.add(ex.submit(generator_worker_task, region, prefix, total))
        while futures:
            _, futures = wait(futures, return_when=FIRST_COMPLETED)
            with state.lock:
                done_now = state.success_count
            if done_now >= total:
                state.exit_flag = True
                break

    elapsed = time.time() - start
    try:
        save_csv()
    except Exception:
        pass
    UI.summary(region, total, elapsed, "SAKURA", workers)
    input(f"\n  {PALETTE.FOG}Press Enter...{PALETTE.RESET}")


def load_accounts_from_file(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        accounts = []
        for item in data:
            if not isinstance(item, dict):
                continue
            uid = item.get("uid")
            pwd = item.get("password")
            if uid and pwd:
                accounts.append({
                    "uid":        str(uid),
                    "password":   str(pwd),
                    "jwt":        item.get("jwt", ""),
                    "open_id":    item.get("open_id", ""),
                    "region":     item.get("region", "BD"),
                    "account_id": item.get("account_id", "-"),
                    "name":       item.get("name", "-"),
                })
        return accounts
    except Exception:
        return []


def handle_activate_only():
    print()
    print(f"  {PALETTE.BOLD}{_gradient('⚡ ACTIVATE ONLY ⚡', PALETTE.SUNSET_JP, 0)}{PALETTE.RESET}")
    print()
    if not os.path.exists(Config.ACCOUNTS_FILE):
        log_err(f"No accounts file: {os.path.basename(Config.ACCOUNTS_FILE)}")
        log_info("Generate accounts first (Option 2)")
        input(f"\n  {PALETTE.FOG}Press Enter...{PALETTE.RESET}")
        return

    accounts = load_accounts_from_file(Config.ACCOUNTS_FILE)
    if not accounts:
        log_err("No valid accounts found")
        input(f"\n  {PALETTE.FOG}Press Enter...{PALETTE.RESET}")
        return

    log_ok(f"Loaded {len(accounts)} accounts")
    if not ask_yes_no(f"▶ Activate {len(accounts)} accounts?", default=True):
        return

    state.activated_count = 0
    state.activation_results.clear()
    state.exit_flag = False
    log_bd("Launching activation...")
    print()
    start = time.time()

    batch_size = 10
    for i in range(0, len(accounts), batch_size):
        if state.exit_flag:
            break
        batch = accounts[i:i + batch_size]
        for j, acc in enumerate(batch):
            slot = i + j + 1
            try:
                result = ActivationEngine.activate(str(acc["uid"]), str(acc["password"]), acc=acc)
                save_activation_result(str(acc["uid"]), result["status"], result["message"])
                if result["activated"]:
                    state.activated_count += 1
                    acc["activated"] = True
                    save_activated_record({
                        "uid":                acc["uid"],
                        "password":           acc["password"],
                        "account_id":         acc.get("account_id", "-"),
                        "name":               acc.get("name", "-"),
                        "region":             acc.get("region", "BD"),
                        "date_created":       now_str(),
                        "activation_status":  result["status"],
                        "activation_message": result["message"],
                    })
                    log_act(f"[{slot}/{len(accounts)}] ✅ {acc['uid']}")
                else:
                    log_err(f"[{slot}/{len(accounts)}] ✖ {acc['uid']} ({result['status']})")
            except Exception as e:
                log_error_to_file(str(e), "handle_activate_only")
                log_err(f"[{slot}/{len(accounts)}] Error: {e}")
            time.sleep(0.4)

    elapsed = time.time() - start
    save_csv()
    UI.header("📊 ACTIVATION REPORT", "Guest")
    UI.row("Total",     f"{PALETTE.BD_GOLD}{len(accounts)}{PALETTE.RESET}")
    UI.row("Activated", f"{PALETTE.BD_GREEN}{state.activated_count}{PALETTE.RESET}")
    UI.row("Pending",   f"{PALETTE.SUNSET}{len(accounts) - state.activated_count}{PALETTE.RESET}")
    UI.row("Duration",  f"{PALETTE.NEON_PURPLE}{elapsed:.2f}s{PALETTE.RESET}")
    UI.row("Owner",     f"{PALETTE.BOLD}{PALETTE.BD_GOLD}M. SARKER{PALETTE.RESET}")
    UI.footer()
    print()
    input(f"\n  {PALETTE.FOG}Press Enter...{PALETTE.RESET}")


def handle_view_files():
    print()
    UI.header("📂 OUTPUT FILES", "Accounts")
    UI.row("Accounts",  f"{PALETTE.MIST}{Config.ACCOUNTS_FILE}{PALETTE.RESET}")
    UI.row("Activated", f"{PALETTE.MIST}{Config.ACTIVATED_FILE}{PALETTE.RESET}")
    UI.row("CSV Log",   f"{PALETTE.MIST}{Config.ACTIVATION_RESULTS_FILE}{PALETTE.RESET}")
    UI.row("Logs Dir",  f"{PALETTE.MIST}{LOGS_FOLDER}{PALETTE.RESET}")
    UI.row("Owner",     f"{PALETTE.BOLD}{PALETTE.BD_GOLD}M. SARKER{PALETTE.RESET}")
    UI.footer()
    print()

    try:
        total = len([f for f in os.listdir(RESULT_FOLDER) if f.endswith(".json")])
        print(f"  {PALETTE.BD_GREEN}JSON files: {total}{PALETTE.RESET}")
    except Exception:
        pass

    total_size = 0
    try:
        for dirpath, _, filenames in os.walk(RESULT_FOLDER):
            for fn in filenames:
                try:
                    total_size += os.path.getsize(os.path.join(dirpath, fn))
                except Exception:
                    pass
        print(f"  {PALETTE.BD_GREEN}Total size: {total_size / 1024:.1f} KB{PALETTE.RESET}")
    except Exception:
        pass
    print()
    input(f"  {PALETTE.FOG}Press Enter...{PALETTE.RESET}")


def handle_export_csv():
    print()
    log_angel("Exporting CSV...")
    try:
        save_csv()
        log_ok(f"Saved → {os.path.basename(Config.ACTIVATION_RESULTS_FILE)}")
    except Exception as e:
        log_err(f"Failed: {e}")
    input(f"\n  {PALETTE.FOG}Press Enter...{PALETTE.RESET}")


# ══════════════════════════════════════════════════════════════════════════
#  MENU LOOP
# ══════════════════════════════════════════════════════════════════════════
def main_menu_loop():
    while True:
        try:
            Banner.draw(animate=False)
            show_main_menu()
            choice = ask_input("Choice", "1", PALETTE.BD_GOLD).strip()

            if choice == "1":
                handle_generate_and_activate()
            elif choice == "2":
                handle_generate_only()
            elif choice == "3":
                handle_activate_only()
            elif choice == "4":
                handle_view_files()
            elif choice == "5":
                handle_export_csv()
            elif choice == "0":
                log_angel(f"Thanks for using {_OWNER_NAME}!")
                log_bd("আল্লাহ হাফেজ!")
                print()
                break
            else:
                log_warn(f"Invalid choice: {choice}")
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            if ask_yes_no("Exit application?", default=True):
                log_angel("Goodbye!")
                break
            continue
        except Exception as e:
            log_err(f"Error: {e}")
            log_error_to_file(str(e), "main_menu_loop")
            time.sleep(2)


# ══════════════════════════════════════════════════════════════════════════
#  VALIDATION + BOOT
# ══════════════════════════════════════════════════════════════════════════
def _validate_setup() -> bool:
    try:
        try:
            from Crypto.Cipher import AES as _aes_check
        except ImportError:
            print(f"{PALETTE.BD_RED}[FATAL] pycryptodome missing{PALETTE.RESET}")
            print(f"{PALETTE.SUNSET}Install: pip install pycryptodome{PALETTE.RESET}")
            return False
        try:
            import blackboxprotobuf as _bb_check
        except ImportError:
            print(f"{PALETTE.BD_RED}[FATAL] blackboxprotobuf missing{PALETTE.RESET}")
            print(f"{PALETTE.SUNSET}Install: pip install blackboxprotobuf{PALETTE.RESET}")
            return False
        try:
            import requests as _req_check
        except ImportError:
            print(f"{PALETTE.BD_RED}[FATAL] requests missing{PALETTE.RESET}")
            print(f"{PALETTE.SUNSET}Install: pip install requests{PALETTE.RESET}")
            return False
        return True
    except Exception as e:
        print(f"{PALETTE.BD_RED}[FATAL] Setup error: {e}{PALETTE.RESET}")
        return False


def _show_startup_info():
    print()
    log_angel(f"Welcome to {_OWNER_NAME}!")
    log_info(f"Version      : {_OWNER_VER}")
    log_info(f"Mode         : GENERATOR + ACTIVATOR")
    log_info(f"Region       : BANGLADESH 🇧🇩")
    log_info(f"Output Dir   : {os.path.basename(RESULT_FOLDER)}/")
    print()


def boot_animation() -> None:
    print()
    steps = [
        (" ", "Guest Generate কোর চালু হচ্ছে..."),
        ("🔐", "এনক্রিপশন কী লোড হচ্ছে..."),
        (" ", "বাংলাদেশ রিজিয়ন সেট হচ্ছে..."),
        ("⚡", "প্রক্সি ও কানেকশন প্রস্তুত..."),
        ("🚀", "সিস্টেম রেডি!"),
    ]
    for icon, msg in steps:
        for i in range(3):
            sys.stdout.write(
                f"\r  {PALETTE.NEON_VIOLET}{icon}{PALETTE.RESET}  "
                f"{PALETTE.SAKURA}{msg}{PALETTE.RESET}  "
                f"{'.' * (i + 1)}   "
            )
            sys.stdout.flush()
            time.sleep(0.09)
        sys.stdout.write(
            f"\r  {PALETTE.BD_GREEN}{icon}{PALETTE.RESET}  "
            f"{PALETTE.BOLD}{PALETTE.PURE}{msg}{PALETTE.RESET}  ✓   \n"
        )
        sys.stdout.flush()
        time.sleep(0.1)
    print()


def _safe_cleanup():
    try:
        save_csv()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    if not _verify_credit():
        _show_violation()

    if not _validate_setup():
        try:
            input(f"\n  {PALETTE.FOG}Press Enter to exit...{PALETTE.RESET}")
        except Exception:
            pass
        sys.exit(1)

    Banner.draw(animate=False)
    boot_animation()

    state.proxy_list = []
    proxies_file = os.path.join(CURRENT_DIR, "proxies.txt")
    if os.path.exists(proxies_file):
        try:
            with open(proxies_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if not line.startswith("http"):
                            line = f"http://{line}"
                        state.proxy_list.append(line)
            if state.proxy_list:
                log_ok(f"Loaded {len(state.proxy_list)} proxies")
            else:
                log_warn("Empty proxies.txt — DIRECT mode")
        except Exception as e:
            log_warn(f"Proxy load failed: {e}")
    else:
        log_warn("No proxies.txt — DIRECT mode")

    _show_startup_info()

    UI.header("👑 M. SARKER · OWNER PROFILE 👑", "Guest")
    UI.row("★ OWNER",    f"{PALETTE.BOLD}{PALETTE.BD_GOLD}M. SARKER{PALETTE.RESET}")
    UI.row("★ BRAND",    f"{PALETTE.BOLD}{PALETTE.SAKURA}SARKER{PALETTE.RESET}")
    UI.row("★ VERSION",  f"{PALETTE.BOLD}{PALETTE.NEON_CYAN} {PALETTE.RESET}")
    UI.row("★ COUNTRY",  f"{PALETTE.BOLD}{PALETTE.BD_GREEN}BANGLADESH{PALETTE.RESET}")
    UI.row("★ MODULE",   f"{PALETTE.SAKURA}Generator + Activator{PALETTE.RESET}")
    UI.row("★ MODE",     f"{PALETTE.NEON_MINT}HYPER · Auto Threads{PALETTE.RESET}")
    UI.row("★ CONTACT",  f"{PALETTE.NEON_PURPLE}{_OWNER_TG}{PALETTE.RESET}")
    UI.footer()
    print()

    time.sleep(0.5)
    main_menu_loop()
    _safe_cleanup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        log_warn("Force stopped by user")
        _safe_cleanup()
    except SystemExit:
        pass
    except Exception as e:
        print()
        log_err(f"Fatal error: {e}")
        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass
        _safe_cleanup()
    finally:
        print()
        credit = f"👑 OWNER : M. SARKER  ★  BRAND : SARKER  ★  🇧🇩 BANGLADESH ★"
        try:
            print(f"  {PALETTE.BOLD}{_gradient(credit, PALETTE.BD_SPIRIT, 0)}{PALETTE.RESET}")
        except Exception:
            print(f"  {credit}")
        print()
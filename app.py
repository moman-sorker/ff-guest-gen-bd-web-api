"""
SARKER Web Panel — Flask wrapper for gen.py
============================================
gen.py is imported as a module and used AS-IS.
Nothing in gen.py is modified. All features are exposed.
"""
import os
import sys
import json
import time
import threading
import concurrent.futures
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor

try:
    from flask import Flask, render_template, request, jsonify, send_file
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "-q"])
    from flask import Flask, render_template, request, jsonify, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import gen  # untouched

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_AS_ASCII"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

# ══════════════════════════════════════════════════════════════════════════
#  TOKEN STORE  (persists JWT/open_id/access_token per UID)
# ══════════════════════════════════════════════════════════════════════════
TOKENS_FILE = os.path.join(gen.RESULT_FOLDER, ".panel_tokens.json")
_tokens_lock = threading.Lock()

def _load_tokens() -> dict:
    try:
        if os.path.exists(TOKENS_FILE):
            with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}

def _save_token(uid: str, data: dict):
    try:
        with _tokens_lock:
            tokens = _load_tokens()
            tokens[str(uid)] = data
            tmp = TOKENS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(tokens, f)
            os.replace(tmp, TOKENS_FILE)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════
#  LOG CAPTURE
# ══════════════════════════════════════════════════════════════════════════
_log_queue = deque(maxlen=3000)
_log_lock  = threading.Lock()
_log_total = [0]

def _capture(level: str, msg: str):
    with _log_lock:
        _log_queue.append({
            "level": level, "msg": str(msg),
            "ts":    time.strftime("%H:%M:%S"),
            "idx":   _log_total[0],
        })
        _log_total[0] += 1

for _name, _lvl in [
    ("log_ok","ok"), ("log_err","err"), ("log_info","info"),
    ("log_warn","warn"), ("log_gen","gen"), ("log_act","act"),
    ("log_angel","angel"), ("log_bd","bd"),
]:
    _orig = getattr(gen, _name)
    def _make(orig, lvl):
        def wrapped(msg, *a, **kw):
            _capture(lvl, msg)
            try: orig(msg, *a, **kw)
            except Exception: pass
        return wrapped
    setattr(gen, _name, _make(_orig, _lvl))

def _account_card_hook(index, total, acc):
    status = "✓ ACTIVATED" if acc.get("activated") else "○ PENDING"
    _capture("account",
             f"[{index}/{total}] {acc.get('name','-')} | "
             f"ID: {acc.get('account_id','-')} | UID: {acc.get('uid','-')} | {status}")
    
    # ✅ টার্মিনালে বড় ইমবেড প্রিন্ট করা
    try:
        with _job_lock:
            threads = _job.get("workers", 10)
        embed_text = _format_account_embed(index, total, threads, acc)
        print(f"\n{embed_text}\n", flush=True)
    except Exception as e:
        pass

gen.UI.account_card = staticmethod(_account_card_hook)
# Hook ActivationEngine.activate to persist JWT tokens
_orig_activate = gen.ActivationEngine.activate
def _activate_hook(uid, password, acc=None, session=None):
    if acc and acc.get("jwt"):
        _save_token(str(uid), {
            "uid":          str(uid),
            "password":     password,
            "account_id":   acc.get("account_id"),
            "open_id":      acc.get("open_id"),
            "access_token": acc.get("access_token"),
            "jwt":          acc.get("jwt"),
            "region":       acc.get("region", "BD"),
        })
    return _orig_activate(uid, password, acc=acc, session=session)

gen.ActivationEngine.activate = _activate_hook

# Wrap save_activated_record for logging
_orig_save_activated = gen.save_activated_record
def _save_activated_hook(data):
    try: _orig_save_activated(data)
    except Exception as e: _capture("err", f"Save fail: {e}")
    _capture("act", f"Activated → {data.get('name','-')} | UID: {data.get('uid','-')}")
gen.save_activated_record = _save_activated_hook

# ══════════════════════════════════════════════════════════════════════════
#  SILENCE RATE-LIMIT LOG SPAM
# ══════════════════════════════════════════════════════════════════════════
_last_fail_log = [0]
_orig_create_one = gen.AccountGenerator.create_one

@classmethod
def _create_one_hook(cls, region, prefix, session=None):
    res = _orig_create_one(region, prefix, session)
    if not res:
        now = time.time()
        # Only log a warning every 5 seconds to prevent UI spam
        if now - _last_fail_log[0] > 5:
            _capture("warn", f"Network limited by Garena. Retrying in background...")
            _last_fail_log[0] = now
    return res

gen.AccountGenerator.create_one = _create_one_hook

# ══════════════════════════════════════════════════════════════════════════
#  DISABLE CACHE FOR API ROUTES
# ══════════════════════════════════════════════════════════════════════════
@app.after_request
def add_header(response):
    if request.path.startswith('/api/') or request.path.startswith('/gen'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# ══════════════════════════════════════════════════════════════════════════
#  JOB STATE (For UI)
# ══════════════════════════════════════════════════════════════════════════
_job_lock = threading.Lock()
_job = {
    "active":     False,
    "type":       None,
    "target":     0,
    "processed":  0,
    "region":     None,
    "prefix":     None,
    "workers":    0,
    "started_at": None,
}

def _start_generation(target, region, workers, prefix, password_prefix):
    with _job_lock:
        if _job["active"]:
            return False, "A job is already running"
        gen.state.success_count   = 0
        gen.state.activated_count = 0
        gen.state.activation_results.clear()
        gen.state.exit_flag       = False
        _job.update({
            "active": True, "type": "generate",
            "target": target, "processed": 0,
            "region": region, "prefix": prefix,
            "workers": workers, "started_at": time.time(),
        })

    def runner():
        _orig_gen_nick = gen.generate_nickname
        _nick_override = prefix.strip() if prefix else None
        
        def _nick_hook(*args, **kwargs):
            if _nick_override is not None:
                kwargs['prefix'] = _nick_override
            return _orig_gen_nick(*args, **kwargs)
            
        gen.generate_nickname = _nick_hook

        _orig_pw_prefix = gen.Config.PASSWORD_PREFIX
        if password_prefix:
            gen.Config.PASSWORD_PREFIX = password_prefix

        try:
            gen.log_bd(f"Starting generation: {target} accounts | {region} | {workers} workers")
            executor = ThreadPoolExecutor(max_workers=workers)
            futures = [executor.submit(gen.generator_worker_task, region, prefix, target)
                       for _ in range(min(workers, target))]
            for f in futures:
                try: f.result()
                except Exception as e: gen.log_err(f"Worker error: {e}")
            executor.shutdown(wait=False)
            gen.log_angel(
                f"Generation complete — {gen.state.success_count} created, "
                f"{gen.state.activated_count} activated")
        except Exception as e:
            gen.log_err(f"Generation error: {e}")
        finally:
            gen.generate_nickname = _orig_gen_nick
            gen.Config.PASSWORD_PREFIX = _orig_pw_prefix
            with _job_lock:
                _job["active"] = False
                _job["type"]   = None

    threading.Thread(target=runner, daemon=True).start()
    return True, "Started"

# ══════════════════════════════════════════════════════════════════════════
#  EMBED FORMATTER FOR API ROUTE
# ══════════════════════════════════════════════════════════════════════════
def _format_account_embed(idx, target, threads, acc):
    region_names = {
        "BD": "Bangladesh", "IND": "India", "PK": "Pakistan",
        "SG": "Singapore", "ID": "Indonesia", "ME": "Middle East"
    }
    r_name = region_names.get(acc.get("region", "BD").upper(), acc.get("region", "BD").upper())
    now = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    reg_text = f"[{idx}/{target}] gerena guest register...\n"
    reg_text += f"[{threads} THREAD] status: 200\n"
    reg_text += f"[INFO] account uid={acc['uid']} password={acc['password']}\n"
    reg_text += f"[INFO] account name={acc['name']} region={acc['region'].lower()}\n"
    reg_text += f"[INFO] account created: {acc['date_created']}\n"
    reg_text += f"[GETREGISTER] status: 200 \n"
    reg_text += f"[GENERATE] status: 200\n"
    reg_text += f"[PREVIEW]\n"
    reg_text += f"[{idx}/{target}] Ok\n"
    reg_text += f"GETREGISTER status: 200\n"
    reg_text += "-" * 61 + "\n"
    reg_text += f"UID                   : {acc['uid']}\n"
    reg_text += f"PASSWORD     : {acc['password']}\n"
    reg_text += f"GAME ID          : {acc['account_id']}\n"
    reg_text += f"NICKNAME      : {acc['name']} \n"
    reg_text += f"RIGION             : {r_name}\n"
    reg_text += f"GETREGISTER : Success \n"
    reg_text += f"CREATED         : {acc['date_created']}\n"
    reg_text += "-" * 62 + "\n"
    reg_text += f"[SAVE] log:  {acc['region'].lower()}_register.json\n"
    reg_text += f"[{idx}/{target}] ✓ gerena guest register success\n\n"
    reg_text += f"[[{idx}/{target}] Ok \n\n"
    reg_text += f"[{idx}/{target}] MajorRegister → Handshake MajorLogIn\n\n"
    
    if acc.get("activated"):
        act_text = f"[{idx}/{target}] gerena guest login...\n"
        act_text += f"[GETLOGIN] status: 200\n"
        act_text += f"[INFO] account uid={acc['uid']} password={acc['password']}\n"
        act_text += f"[INFO] account game id={acc['account_id']}\n"
        act_text += f"[INFO] account name={acc['name']} region={acc['region'].lower()}\n"
        act_text += f"[INFO] account created: {acc['date_created']}\n"
        act_text += f"[INFO] account activated: {now}\n"
        act_text += f"[ACTIVATE] status: true\n"
        act_text += f"[GETLOGIN] status: 200 \n"
        act_text += f"[ACTIVATION] status: 200\n"
        act_text += f"[PREVIEW]\n"
        act_text += f"[{idx}/{target}] Ok\n"
        act_text += f"GETLOGIN status: 200\n"
        act_text += "-" * 61 + "\n"
        act_text += f"UID               : {acc['uid']}\n"
        act_text += f"PASSWORD : {acc['password']}\n"
        act_text += f"GAME ID      : {acc['account_id']}\n"
        act_text += f"NICKNAME  : {acc['name']} \n"
        act_text += f"RIGION         : {r_name}\n"
        act_text += f"ACCOUNT   : Active\n"
        act_text += f"CREATED     : {acc['date_created']}\n"
        act_text += f"ACTIVATED  : {now}\n"
        act_text += "-" * 62 + "\n"
        act_text += f"[SAVE] log:  {acc['region'].lower()}_data.json\n"
        act_text += f"[{idx}/{target}] ✓ gerena guest activation success\n\n"
        act_text += f"[{idx}/{target}] Done"
    else:
        act_text = f"[{idx}/{target}] gerena guest login...\n"
        act_text += f"[GETLOGIN] status: 400\n"
        act_text += f"[ACTIVATE] status: false\n"
        act_text += f"[ERROR] Activation failed: {acc.get('activation_message', 'Unknown')}\n"
        act_text += f"[{idx}/{target}] ✖ gerena guest activation failed"
        
    return reg_text + act_text

# ══════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def api_stats():
    with _job_lock:
        job = dict(_job)
    total = 0
    if os.path.exists(gen.Config.ACCOUNTS_FILE):
        try:
            with open(gen.Config.ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                total = len(json.load(f))
        except Exception:
            pass
    elapsed = (time.time() - job["started_at"]) if job["started_at"] else 0
    try:
        with _tokens_lock:
            tokens_count = len(_load_tokens())
    except Exception:
        tokens_count = 0
    return jsonify({
        "success_count":   gen.state.success_count,
        "activated_count": gen.state.activated_count,
        "total_accounts":  total,
        "cached_tokens":   tokens_count,
        "job_active":      job["active"],
        "job_type":        job["type"],
        "target":          job["target"],
        "processed":       job["processed"],
        "elapsed":         elapsed,
        "region":          job["region"],
    })

@app.route("/api/logs")
def api_logs():
    try: since = int(request.args.get("since", 0))
    except Exception: since = 0
    with _log_lock:
        logs  = list(_log_queue)
        total = _log_total[0]
    return jsonify({"logs": [l for l in logs if l["idx"] >= since], "total": total})

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(silent=True) or {}
    try:
        target  = int(data.get("target", 100))
        workers = int(data.get("workers", 50))
    except Exception:
        return jsonify({"ok": False, "error": "Invalid numeric parameters"}), 400
    target  = max(1, min(100, target))
    workers = max(1, min(100, workers))
    
    # ✅ Force BD only
    region = "BD" 
    
    prefix = (str(data.get("prefix", "SARKER")) or "SARKER").strip()[:12]
    password_prefix = str(data.get("password", "MM388401")).strip()
    
    ok, msg = _start_generation(target, region, workers, prefix, password_prefix)
    return jsonify({"ok": ok, "message": msg if ok else None,
                    "error": None if ok else msg})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    gen.state.exit_flag = True
    return jsonify({"ok": True})

@app.route("/api/accounts")
def api_accounts():
    accounts = []
    if os.path.exists(gen.Config.ACCOUNTS_FILE):
        try:
            with open(gen.Config.ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
            if not isinstance(accounts, list): accounts = []
        except Exception: accounts = []
    return jsonify(accounts)

FILE_MAP = {
    "accounts.json":           lambda: gen.Config.ACCOUNTS_FILE,
    "activated_accounts.json": lambda: gen.Config.ACTIVATED_FILE,
    "activation_results.csv":  lambda: gen.Config.ACTIVATION_RESULTS_FILE,
}

@app.route("/api/files")
def api_files():
    files = []
    for name, resolver in FILE_MAP.items():
        p = resolver()
        if os.path.exists(p):
            files.append({"name": name, "size": os.path.getsize(p),
                          "modified": os.path.getmtime(p)})
    return jsonify(files)

@app.route("/api/download/<name>")
def api_download(name):
    if name not in FILE_MAP:
        return jsonify({"error": "Not found"}), 404
    p = FILE_MAP[name]()
    if not os.path.exists(p):
        return jsonify({"error": "File not found"}), 404
    return send_file(p, as_attachment=True, download_name=name)

@app.route("/api/clear_logs", methods=["POST"])
def api_clear_logs():
    with _log_lock:
        _log_queue.clear()
    return jsonify({"ok": True})

# ══════════════════════════════════════════════════════════════════════════
#  EXTERNAL API ROUTE: /gen (URL Based)
# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════
#  EXTERNAL API ROUTE: /gen (URL Based)
# ══════════════════════════════════════════════════════════════════════════
@app.route("/gen", methods=["GET"])
def api_gen_url():
    # 1. Security Key Check
    key = request.args.get("key")
    if key != "sarker":
        return jsonify({"ok": False, "error": "Unauthorized. Invalid key."}), 401

    # 2. Parse Parameters
    try:
        target = int(request.args.get("target", 10))
        threads = int(request.args.get("thread", 10))
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid target or thread values"}), 400

    # ✅ Force BD only
    region = "BD"
    
    name = request.args.get("name", "SARKER")
    password = request.args.get("password", "MM388401")

    # 3. Hard Limits
    target = max(1, min(100, target))
    threads = max(1, min(100, threads))

    # 4. Patch Naming & Password for this specific API call
    _orig_gen_nick = gen.generate_nickname
    _nick_override = name.strip() if name else None
    
    def _nick_hook(*args, **kwargs):
        if _nick_override is not None:
            kwargs['prefix'] = _nick_override
        return _orig_gen_nick(*args, **kwargs)
        
    gen.generate_nickname = _nick_hook

    _orig_pw_prefix = gen.Config.PASSWORD_PREFIX
    if password:
        gen.Config.PASSWORD_PREFIX = password

    results = {}
    account_data_dict = {} # ✅ নতুন: ডাটা ইনডেক্স অনুযায়ী রাখার জন্য ডিকশনারি
    
    # 5. Worker Function
    def run_single(idx):
        try:
            acc = gen.AccountGenerator.create_one(region, name)
            if not acc:
                return idx, f"[{idx}/{target}] ✖ Failed to create account (Network error or rate limit)", None
            
            text = _format_account_embed(idx, target, threads, acc)
            print(f"\n{text}\n", flush=True)
            
            account_obj = {
                "uid": acc.get("uid"),
                "password": acc.get("password"),
                "account_id": acc.get("account_id"),
                "name": acc.get("name"),
                "region": acc.get("region"),
                "date_created": acc.get("date_created"),
                "activated": acc.get("activated", False),
                "activation_status": acc.get("activation_status"),
                "activation_message": acc.get("activation_message"),
                "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if acc.get("activated") else None,
                "owner": "M. SARKER",
                "brand": "SARKER"
            }
            return idx, text, account_obj
        except Exception as e:
            return idx, f"[{idx}/{target}] ✖ Error: {str(e)[:100]}", None

    # 6. Execute Multi-threaded Generation
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(run_single, i+1) for i in range(target)]
        for f in concurrent.futures.as_completed(futures):
            idx, text, acc_obj = f.result()
            results[idx] = text
            if acc_obj:
                account_data_dict[idx] = acc_obj # ✅ ইনডেক্স অনুযায়ী সেভ করা হচ্ছে

    # 7. Restore Patched Functions
    gen.generate_nickname = _orig_gen_nick
    gen.Config.PASSWORD_PREFIX = _orig_pw_prefix

    # 8. Sort results sequentially (1, 2, 3, 4, 5...)
    sorted_results = [results[i] for i in sorted(results.keys())]
    sorted_data = [account_data_dict[i] for i in sorted(account_data_dict.keys())] # ✅ ডাটাও সর্ট করা হলো
    
    # 9. Return JSON Response
    return jsonify({
        "ok": True,
        "status": "success",
        "target": target,
        "threads": threads,
        "region": region,
        "name": name,
        "data": sorted_data,       # ✅ এখন JSON-এ ১ নম্বর অ্যাকাউন্ট সবার আগে থাকবে
        # "embeds": sorted_results   # (ঐচ্ছিক) টেক্সট ফরম্যাট, ডিসকর্ড বা টেলিগ্রাম বটের জন্য
    })

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           SARKER  ·  WEB PANEL                               ║")
    print("║     🌸  Open in browser:  http://127.0.0.1:5000              ║")
    print("║     🔗  API Route: /gen?key=sarker                           ║")
    print("║       Owner : M. SARKER   ★   BANGLADESH                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
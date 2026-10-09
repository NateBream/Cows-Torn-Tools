import re
import sqlite3
import time

import requests

import api_store
import const_data
import discord_hook
from secrets import BSP_API_KEY, mug_db_name

MUG_THRESHOLD = 2000000
MIN_RUN_INTERVAL = 14 * 60     # Skip the run if the last one was less than this many seconds ago
FIRST_RUN_LOOKBACK = 60 * 60   # How far back to look when there is no saved state
WINDOW_OVERLAP = 10 * 60       # Re-scan this much before the last run so attacks in progress aren't missed
PRUNE_AGE = 7 * 24 * 60 * 60   # Forget processed attacks older than this

MUG_AMOUNT_RE = re.compile(r'\$([\d,]+)')


def create_database():
    conn = sqlite3.connect(mug_db_name)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS run_state (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        last_run REAL,
                        last_success REAL
                   )''')

    # Mugs whose attack log has already been checked, so they are never fetched or posted twice
    cursor.execute('''CREATE TABLE IF NOT EXISTS processed_mugs (
                        id INTEGER PRIMARY KEY,
                        ended INTEGER,
                        amount INTEGER
                   )''')

    conn.commit()
    conn.close()


def get_run_state(cursor):
    cursor.execute('SELECT last_run, last_success FROM run_state WHERE id = 1')
    data = cursor.fetchone()
    if data is None:
        return None, None
    return data[0], data[1]


def set_run_state(cursor, last_run, last_success):
    cursor.execute('''INSERT INTO run_state (id, last_run, last_success) VALUES (1, ?, ?)
                      ON CONFLICT(id) DO UPDATE SET last_run = excluded.last_run,
                                                    last_success = excluded.last_success''',
                   (last_run, last_success))


def load_mugs(frm, to):
    """Return all outgoing faction attacks that ended in a mug between frm and to."""
    mugs = {}
    while True:
        params = {'filters': 'outgoing', 'limit': 100, 'sort': 'ASC', 'from': frm, 'to': to}
        attacks = api_store.torn_get(const_data.faction_attacks_url, params,
                                     min_level=api_store.MINIMAL, timeout=30).get('attacks', [])

        for attack in attacks:
            if attack['result'] == 'Mugged':
                mugs[attack['id']] = attack

        if len(attacks) < 100:
            break
        next_frm = max(attack['started'] for attack in attacks)
        if next_frm <= frm:
            break
        frm = next_frm

    return list(mugs.values())


def get_mug_amount(code):
    data = api_store.torn_get(const_data.attacklog_url, {'log': code, 'sort': 'DESC'}, timeout=30)
    for entry in data.get('attacklog', {}).get('log', []):
        if entry['action'] == 'mug':
            match = MUG_AMOUNT_RE.search(entry['text'])
            if match:
                return int(match.group(1).replace(',', ''))
    return 0


def get_bsp(player_id):
    try:
        bsp_data = requests.get(const_data.BSP_API_URL.format(bsp_api=BSP_API_KEY, id=player_id), timeout=30).json()
        return format_large_number(bsp_data['TBS'])
    except Exception as e:
        print("BSP lookup failed for {id}: {e}".format(id=player_id, e=e))
        return 'Unknown'


def format_large_number(num):
    num = float(num)
    for size, suffix in ((1e15, 'Q'), (1e12, 'T'), (1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if abs(num) >= size:
            return f"{num / size:.1f}{suffix}"
    return f"{num:.0f}"


def run():
    create_database()
    conn = sqlite3.connect(mug_db_name)
    cursor = conn.cursor()

    now = time.time()
    last_run, last_success = get_run_state(cursor)

    if last_run is not None and now - last_run < MIN_RUN_INTERVAL:
        print("Last run was {:.0f}s ago, skipping".format(now - last_run))
        conn.close()
        return

    # Record the attempt immediately so repeated calls back off even if this run fails
    set_run_state(cursor, now, last_success)
    conn.commit()

    if last_success is None:
        frm = int(now - FIRST_RUN_LOOKBACK)
    else:
        frm = int(last_success - WINDOW_OVERLAP)
    to = int(now)

    try:
        mugs = load_mugs(frm, to)
        for attack in sorted(mugs, key=lambda a: a['ended']):
            cursor.execute('SELECT id FROM processed_mugs WHERE id = ?', (attack['id'],))
            if cursor.fetchone() is not None:
                continue

            amount = get_mug_amount(attack['code'])
            if amount >= MUG_THRESHOLD:
                defender = attack['defender']
                print("Mug of ${:0,} on {} [{}]".format(amount, defender['name'], defender['id']))
                discord_hook.post_mug(defender['name'], defender['id'], amount, get_bsp(defender['id']))

            cursor.execute('INSERT INTO processed_mugs (id, ended, amount) VALUES (?, ?, ?)',
                           (attack['id'], attack['ended'], amount))
            conn.commit()
    except (api_store.TornApiError, api_store.NoKeyAvailable) as e:
        # Leave last_success alone so the next run re-scans this window
        print("Torn API error: {}".format(e))
        conn.close()
        return

    set_run_state(cursor, now, now)
    cursor.execute('DELETE FROM processed_mugs WHERE ended < ?', (int(now - PRUNE_AGE),))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    run()

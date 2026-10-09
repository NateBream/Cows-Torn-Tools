"""Torn API key store.

Keys live in a SQLite database so every script (watch, item_db, bounty_db,
greenleaf, ...) shares the same usage stats and per-minute rate limits, even
when they run as separate processes.

Modules should call torn_get() for Torn API requests. It picks a key, makes
the request, and rotates to another key on key-specific errors. Use
acquire_key() if you need a raw key string instead.

The BSP api key is NOT managed here.

CLI:
    python api_store.py add <key> [--name NAME] [--cpm N]
    python api_store.py remove <key-or-name>
    python api_store.py list
    python api_store.py set-cpm <key-or-name> <N>
    python api_store.py enable|disable <key-or-name>
    python api_store.py refresh            # re-fetch access levels
"""
import sqlite3
import time

import requests

import const_data
import secrets

DB_NAME = getattr(secrets, 'api_key_db_name', 'api_keys.db')
DEFAULT_CALLS_PER_MINUTE = getattr(secrets, 'api_calls_per_minute', 50)
WINDOW = 60  # seconds

# Torn key access levels
PUBLIC = 1
MINIMAL = 2
LIMITED = 3
FULL = 4
LEVEL_NAMES = {0: 'Unknown', PUBLIC: 'Public', MINIMAL: 'Minimal', LIMITED: 'Limited', FULL: 'Full'}

# Torn error codes that mean the key itself is unusable
DISABLE_ERRORS = {2, 10, 13, 18}  # incorrect key, owner in fed jail, owner inactive, key paused
# Torn error codes that mean the key should rest for a while (seconds)
COOLDOWN_ERRORS = {5: WINDOW, 8: 300, 14: 3600}  # too many requests, IP block, daily limit
# Errors where another key might succeed
RETRY_ERRORS = DISABLE_ERRORS | set(COOLDOWN_ERRORS) | {16}  # 16: access level too low


class TornApiError(Exception):
    def __init__(self, code, message):
        super().__init__('Torn API error {}: {}'.format(code, message))
        self.code = code
        self.message = message


class NoKeyAvailable(Exception):
    pass


def _connect():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.execute('''CREATE TABLE IF NOT EXISTS api_keys (
                        key TEXT PRIMARY KEY,
                        name TEXT,
                        access_level INTEGER DEFAULT 0,
                        access_type TEXT,
                        calls_per_minute INTEGER,
                        total_calls INTEGER DEFAULT 0,
                        total_errors INTEGER DEFAULT 0,
                        last_call REAL DEFAULT 0,
                        last_error TEXT,
                        cooldown_until REAL DEFAULT 0,
                        enabled INTEGER DEFAULT 1,
                        added REAL
                   )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS api_calls (
                        key TEXT,
                        ts REAL
                   )''')
    conn.execute('CREATE INDEX IF NOT EXISTS api_calls_key_ts ON api_calls (key, ts)')
    return conn


def _find_key(conn, key_or_name):
    row = conn.execute('SELECT key FROM api_keys WHERE key = ? OR name = ?',
                       (key_or_name, key_or_name)).fetchone()
    if row is None:
        raise KeyError('No api key matching {}'.format(key_or_name))
    return row[0]


def _seed_legacy_key(conn):
    # Import secrets.API_KEY the first time the store is used
    legacy = getattr(secrets, 'API_KEY', None)
    if legacy and conn.execute('SELECT COUNT(*) FROM api_keys').fetchone()[0] == 0:
        conn.execute('INSERT INTO api_keys (key, name, added) VALUES (?, ?, ?)',
                     (legacy, 'legacy', time.time()))
        conn.commit()


def _try_acquire(conn, min_level, exclude):
    """Atomically pick a key with spare capacity and record a call against it.

    Returns (key, None) on success, or (None, seconds_to_wait).
    """
    now = time.time()
    conn.execute('BEGIN IMMEDIATE')
    try:
        conn.execute('DELETE FROM api_calls WHERE ts < ?', (now - WINDOW,))
        rows = conn.execute('''SELECT key, COALESCE(calls_per_minute, ?), cooldown_until
                               FROM api_keys
                               WHERE enabled = 1 AND (access_level >= ? OR access_level = 0)
                               ORDER BY last_call ASC''',
                            (DEFAULT_CALLS_PER_MINUTE, min_level)).fetchall()
        rows = [r for r in rows if r[0] not in exclude]
        if not rows:
            conn.rollback()
            raise NoKeyAvailable('No enabled api key with access level >= {}'.format(LEVEL_NAMES.get(min_level, min_level)))

        wait = None
        for key, cpm, cooldown_until in rows:
            if cooldown_until > now:
                key_wait = cooldown_until - now
            else:
                used, oldest = conn.execute('SELECT COUNT(*), MIN(ts) FROM api_calls WHERE key = ?',
                                            (key,)).fetchone()
                if used < cpm:
                    # Least recently used key with capacity wins -> round robin rotation
                    conn.execute('INSERT INTO api_calls (key, ts) VALUES (?, ?)', (key, now))
                    conn.execute('''UPDATE api_keys
                                    SET total_calls = total_calls + 1, last_call = ?
                                    WHERE key = ?''', (now, key))
                    conn.commit()
                    return key, None
                key_wait = oldest + WINDOW - now
            wait = key_wait if wait is None else min(wait, key_wait)

        conn.rollback()
        return None, max(wait, 0.05)
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise


def acquire_key(min_level=PUBLIC, wait=True, timeout=None, exclude=()):
    """Return a key for one api call, counting the call against its rate limit.

    Blocks until a key has capacity unless wait is False, in which case
    NoKeyAvailable is raised.
    """
    deadline = None if timeout is None else time.time() + timeout
    conn = _connect()
    try:
        _seed_legacy_key(conn)
        while True:
            key, delay = _try_acquire(conn, min_level, set(exclude))
            if key is not None:
                return key
            if not wait or (deadline is not None and time.time() + delay > deadline):
                raise NoKeyAvailable('All api keys are at their rate limit')
            time.sleep(delay)
    finally:
        conn.close()


def report_error(key, code, message=''):
    """Record a Torn error for a key, disabling or cooling it down as needed."""
    conn = _connect()
    try:
        conn.execute('''UPDATE api_keys
                        SET total_errors = total_errors + 1, last_error = ?
                        WHERE key = ?''',
                     ('{}: {} @ {}'.format(code, message, time.strftime('%Y-%m-%d %H:%M:%S')), key))
        if code in DISABLE_ERRORS:
            conn.execute('UPDATE api_keys SET enabled = 0 WHERE key = ?', (key,))
        elif code in COOLDOWN_ERRORS:
            conn.execute('UPDATE api_keys SET cooldown_until = ? WHERE key = ?',
                         (time.time() + COOLDOWN_ERRORS[code], key))
        conn.commit()
    finally:
        conn.close()


def torn_get(url, params=None, min_level=PUBLIC, timeout=10):
    """GET a Torn api url (without a key) and return the parsed json.

    Rotates to another key when a key-specific error is returned.
    Raises TornApiError for other Torn errors.
    """
    params = dict(params or {})
    params.setdefault('comment', const_data.request_comment_name)
    tried = set()
    while True:
        key = acquire_key(min_level, exclude=tried)
        params['key'] = key
        data = requests.get(url, params=params, timeout=timeout).json()
        error = data.get('error') if isinstance(data, dict) else None
        if not error:
            return data

        code = error.get('code')
        message = error.get('error', '')
        report_error(key, code, message)
        tried.add(key)
        if code not in RETRY_ERRORS:
            raise TornApiError(code, message)
        print('api key {} failed with error {} ({}), rotating'.format(_mask(key), code, message))


def fetch_key_info(key):
    """Look up a key's access level directly (counts as a call on that key)."""
    data = requests.get(const_data.torn_api_url + 'key/',
                        params={'selections': 'info', 'key': key,
                                'comment': const_data.request_comment_name},
                        timeout=10).json()
    if 'error' in data:
        raise TornApiError(data['error'].get('code'), data['error'].get('error', ''))
    return data.get('access_level', 0), data.get('access_type', '')


def _record_direct_call(conn, key):
    now = time.time()
    conn.execute('INSERT INTO api_calls (key, ts) VALUES (?, ?)', (key, now))
    conn.execute('UPDATE api_keys SET total_calls = total_calls + 1, last_call = ? WHERE key = ?', (now, key))


def _update_level(conn, key):
    _record_direct_call(conn, key)
    try:
        level, access_type = fetch_key_info(key)
    except TornApiError as e:
        conn.commit()
        report_error(key, e.code, e.message)
        raise
    conn.execute('UPDATE api_keys SET access_level = ?, access_type = ? WHERE key = ?',
                 (level, access_type, key))
    conn.commit()
    return level, access_type


def add_key(key, name=None, calls_per_minute=None):
    conn = _connect()
    try:
        conn.execute('''INSERT INTO api_keys (key, name, calls_per_minute, added)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(key) DO UPDATE SET
                            name = COALESCE(excluded.name, name),
                            calls_per_minute = COALESCE(excluded.calls_per_minute, calls_per_minute),
                            enabled = 1''',
                     (key, name, calls_per_minute, time.time()))
        conn.commit()
        return _update_level(conn, key)
    finally:
        conn.close()


def remove_key(key_or_name):
    conn = _connect()
    try:
        key = _find_key(conn, key_or_name)
        conn.execute('DELETE FROM api_keys WHERE key = ?', (key,))
        conn.execute('DELETE FROM api_calls WHERE key = ?', (key,))
        conn.commit()
    finally:
        conn.close()


def set_calls_per_minute(key_or_name, calls_per_minute):
    conn = _connect()
    try:
        key = _find_key(conn, key_or_name)
        conn.execute('UPDATE api_keys SET calls_per_minute = ? WHERE key = ?', (calls_per_minute, key))
        conn.commit()
    finally:
        conn.close()


def set_enabled(key_or_name, enabled):
    conn = _connect()
    try:
        key = _find_key(conn, key_or_name)
        conn.execute('UPDATE api_keys SET enabled = ?, cooldown_until = 0 WHERE key = ?',
                     (1 if enabled else 0, key))
        conn.commit()
    finally:
        conn.close()


def refresh_levels():
    conn = _connect()
    try:
        _seed_legacy_key(conn)
        for (key,) in conn.execute('SELECT key FROM api_keys').fetchall():
            try:
                level, access_type = _update_level(conn, key)
                print('{}: {} ({})'.format(_mask(key), LEVEL_NAMES.get(level, level), access_type))
            except TornApiError as e:
                print('{}: {}'.format(_mask(key), e))
    finally:
        conn.close()


def list_keys():
    conn = _connect()
    try:
        _seed_legacy_key(conn)
        now = time.time()
        rows = conn.execute('''SELECT k.key, k.name, k.access_level, COALESCE(k.calls_per_minute, ?),
                                      k.total_calls, k.total_errors, k.last_call, k.last_error,
                                      k.cooldown_until, k.enabled,
                                      (SELECT COUNT(*) FROM api_calls c WHERE c.key = k.key AND c.ts >= ?)
                               FROM api_keys k ORDER BY k.added''',
                            (DEFAULT_CALLS_PER_MINUTE, now - WINDOW)).fetchall()
        return [{
            'key': r[0], 'name': r[1], 'access_level': r[2], 'calls_per_minute': r[3],
            'total_calls': r[4], 'total_errors': r[5], 'last_call': r[6], 'last_error': r[7],
            'cooldown_until': r[8], 'enabled': bool(r[9]), 'calls_last_minute': r[10],
        } for r in rows]
    finally:
        conn.close()


def _mask(key):
    return key[:4] + '*' * (len(key) - 4)


def _print_keys():
    keys = list_keys()
    if not keys:
        print('No api keys stored')
        return
    for k in keys:
        last = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(k['last_call'])) if k['last_call'] else 'never'
        status = 'enabled' if k['enabled'] else 'DISABLED'
        if k['cooldown_until'] > time.time():
            status += ' (cooldown {:.0f}s)'.format(k['cooldown_until'] - time.time())
        print('{} [{}] level={} {} | {}/{} calls last min | total={} errors={} | last call {}{}'.format(
            _mask(k['key']), k['name'] or '-', LEVEL_NAMES.get(k['access_level'], k['access_level']), status,
            k['calls_last_minute'], k['calls_per_minute'], k['total_calls'], k['total_errors'], last,
            ' | last error: ' + k['last_error'] if k['last_error'] else ''))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Manage the Torn api key store')
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('add')
    p.add_argument('key')
    p.add_argument('--name')
    p.add_argument('--cpm', type=int, help='calls per minute for this key (default {})'.format(DEFAULT_CALLS_PER_MINUTE))
    sub.add_parser('remove').add_argument('key')
    sub.add_parser('list')
    p = sub.add_parser('set-cpm')
    p.add_argument('key')
    p.add_argument('cpm', type=int)
    sub.add_parser('enable').add_argument('key')
    sub.add_parser('disable').add_argument('key')
    sub.add_parser('refresh')
    args = parser.parse_args()

    if args.cmd == 'add':
        level, access_type = add_key(args.key, args.name, args.cpm)
        print('Added {} with access level {} ({})'.format(_mask(args.key), LEVEL_NAMES.get(level, level), access_type))
    elif args.cmd == 'remove':
        remove_key(args.key)
    elif args.cmd == 'list':
        _print_keys()
    elif args.cmd == 'set-cpm':
        set_calls_per_minute(args.key, args.cpm)
    elif args.cmd == 'enable':
        set_enabled(args.key, True)
    elif args.cmd == 'disable':
        set_enabled(args.key, False)
    elif args.cmd == 'refresh':
        refresh_levels()

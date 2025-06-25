import sqlite3
import const_data
import requests
from secrets import API_KEY, bounty_db_name, BSP_API_KEY
import time
import discord_hook

THRESHOLD=500000

def add_bounty(player_id, player_name, value, qty):
    # Connect to SQLite database
    conn = sqlite3.connect(bounty_db_name)
    cursor = conn.cursor()

    # Check if the id already exists
    cursor.execute('SELECT id FROM bounty WHERE id = ?', (player_id,))
    data = cursor.fetchone()

    if data is None:
        # If id does not exist, insert a new row with default values
        cursor.execute('''INSERT INTO bounty (id, value, quantity, name)
                          VALUES (?, ?, ?, ?)''',
                       (player_id, value, qty, player_name))
    else: # A bounty already exists in db, update qty if value is the same
        cursor.execute('SELECT value, quantity FROM bounty WHERE id = ?', (player_id,))
        data = cursor.fetchone()
        eValue = int(data[0])
        eQty = int(data[1])

        if value == eValue:
            print("Updating {name}. Value: {v}, Old Qty: {q} New Qty: {n}".format(name=player_name, v=value, q=qty, n=(qty+eQty)))
            cursor.execute('''UPDATE bounty
                                SET quantity = ?
                                WHERE id = ?;''',
                        (qty + eQty, player_id))
        

    # Commit changes and close connection
    conn.commit()
    conn.close()

def loadBounties(offset):
    api_request = const_data.torn_api_v2_url + const_data.bounty_selections.format(off=offset) + API_KEY
    response = requests.get(api_request)
    data = response.json()
    pData = data['bounties']
    bountyList = [dict(row) for row in pData]

    last_value = 0

    for bounty in bountyList:
        player_id = bounty['target_id']
        player_name = bounty['target_name']
        value = bounty['reward']
        qty = bounty['quantity']
        if (value < THRESHOLD):
            return value
        add_bounty(player_id, player_name, value, qty)
        updateBSP(player_id, player_name)
        last_value = value
    return last_value

def updateBSP(player_id, name):
    conn = sqlite3.connect(bounty_db_name)
    cursor = conn.cursor()
    cursor.execute('SELECT last_updated FROM bsp_data WHERE id = ?', (player_id,))
    data = cursor.fetchone()

    currTime = time.time()

    if data is None:
        print("Updating BSP For {id}, Data is None".format(id=player_id))
        api_request = const_data.BSP_API_URL.format(bsp_api=BSP_API_KEY, id=player_id)
        response = requests.get(api_request)
        bsp_data = response.json()
        bsp = bsp_data['TBS']
        cursor.execute('''INSERT INTO bsp_data (id, name, bsp, last_updated)
                        VALUES (?, ?, ?, ?)''',
                    (player_id, name, bsp, currTime))
    elif (currTime - data[0]) >= 2592000: # Greater than 30 days
        print("Updating BSP For {id}, last updated: {last_up}, current time: {time}".format(id=player_id, last_up=data[0], time=currTime))
        time.sleep(0.5)
        api_request = const_data.BSP_API_URL.format(BSP_API_KEY, player_id)
        response = requests.get(api_request)
        bsp_data = response.json()
        bsp = bsp_data['TBS']
        cursor.execute('''UPDATE bsp_data
                            SET bsp = ?, currTime = ?, name = ?
                            WHERE id = ?;''',
                    (bsp, currTime, name, player_id))
    conn.commit()
    conn.close()

def bountyHook(player_id, value, qty):
    conn = sqlite3.connect(bounty_db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT bsp FROM bsp_data WHERE id = ?", (player_id,))
    bsp = cursor.fetchone()
    if bsp is None:
        return
    bsp = bsp[0]

    bsp = format_large_number(bsp)
    
    cursor.execute("SELECT name FROM bsp_data WHERE id = ?", (player_id,))
    name = cursor.fetchone()
    if name is None:
        return
    name = name[0]

    discord_hook.post_bounty(name, player_id, value, qty, bsp)

def format_large_number(num):
    """
    Formats a large number into a human-readable string with K, M, B, or T suffixes.
    """
    num = float(num) # Ensure the number is a float for division
    if abs(num) >= 1_000_000_000_000_000: # Quadrillions
        return f"{num / 1_000_000_000_000_000:.1f}Q"
    elif abs(num) >= 1_000_000_000_000: # Trillions
        return f"{num / 1_000_000_000_000:.1f}T"
    elif abs(num) >= 1_000_000_000: # Billions
        return f"{num / 1_000_000_000:.1f}B"
    elif abs(num) >= 1_000_000: # Millions
        return f"{num / 1_000_000:.1f}M"
    elif abs(num) >= 1_000: # Thousands
        return f"{num / 1_000:.1f}K"
    else:
        return f"{num:.0f}" # For numbers less than 1000, display as is (no decimal)

def processBounties():
    conn = sqlite3.connect(bounty_db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bounty ORDER BY value DESC")

    bounties = cursor.fetchall()

    for bounty in bounties:
        player_id = int(bounty[0])
        value = int(bounty[1])
        qty = int(bounty[2])

        cursor.execute("SELECT * FROM bounty_tmp WHERE id = ?", (player_id,))
        tmp_data = cursor.fetchone()
        
        if tmp_data is not None:
            tmp_value = int(tmp_data[1])
            tmp_qty = int(tmp_data[2])

            # If value is greater than tmp_value we want to bounty hook
            # If value and tmp_value are equal, and qty is greater, bounty hook
            if value < tmp_value:
                continue

            if value == tmp_value and qty <= tmp_qty:
                continue

        bountyHook(player_id, value, qty)


def create_database():
    # Connect to SQLite database (or create if it doesn't exist)
    conn = sqlite3.connect(bounty_db_name)
    cursor = conn.cursor()

    # Create table to store costs and quantities
    cursor.execute('''CREATE TABLE IF NOT EXISTS bounty (
                        id INTEGER PRIMARY KEY,
                        value INTEGER,
                        quantity INTEGER,
                        name TEXT
                   )''')
    
    # Create table to store costs and quantities
    cursor.execute('''CREATE TABLE IF NOT EXISTS bounty_tmp (
                        id INTEGER PRIMARY KEY,
                        value INTEGER,
                        quantity INTEGER,
                        name TEXT
                   )''')

    # Create table to store costs and quantities
    cursor.execute('''CREATE TABLE IF NOT EXISTS bsp_data (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        bsp INTEGER,
                        last_updated REAL
                   )''')
    
    cursor.execute('''DELETE FROM bounty_tmp''') # clear tmp table
    cursor.execute('''INSERT INTO bounty_tmp SELECT * FROM bounty''') # copy current bounty table to tmp
    cursor.execute('''DELETE FROM bounty''') # clear current bounty table


    # Commit changes and close connection
    conn.commit()
    conn.close()



create_database()
off = 0
v = loadBounties(off)
while v > THRESHOLD:
    print(v)
    v = loadBounties(off)
    time.sleep(1)
    off += 100
processBounties()

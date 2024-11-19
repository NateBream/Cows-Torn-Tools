import sqlite3
import time

import const_data
import discord_hook
import request
from secrets import db_name

def market_watch():
    # Connect to SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Select all rows from the market table
    cursor.execute('SELECT id, market_value, curr_low, quantity, threshold, name FROM market')
    rows = cursor.fetchall()

    # Loop over all rows
    for row in rows:
        id_value, market_value, curr_low, quantity, threshold, name = row

        lowest_item = request.get_tornpal(id_value) # [price, qty, player_id]

        print(lowest_item)

        new_low = lowest_item[0]
        new_qty = lowest_item[1]
        player_id = lowest_item[2]

        if (curr_low == -1):
            curr_low = new_low + 1

        priceThreshold = -1

        if threshold > 1:
            priceThreshold = threshold
        else:
            priceThreshold = (market_value * threshold)

        if new_low > priceThreshold:
            continue
        elif new_low == curr_low and new_qty != quantity:
            cursor.execute('''UPDATE market
                              SET quantity = ?
                              WHERE id = ?''',
                           (new_qty, id_value))
            discord_hook.post_tornpal(new_qty, name, new_low, player_id)
        elif new_low == curr_low and new_qty == quantity:
            continue
        else:
            cursor.execute('''UPDATE market
                              SET curr_low = ?,
                              quantity = ?
                              WHERE id = ?''',
                           (new_low, new_qty, id_value))
            discord_hook.post_tornpal(new_qty, name, new_low, player_id)

    # Commit changes and close connection
    conn.commit()
    conn.close()

def po_watch(item_id, cost, item_name):
    lowest_item = request.get_tornpal(item_id) # [price, qty, player_id]

    if (lowest_item[0] <= cost):
        discord_hook.post_po(lowest_item[1], item_id, item_name, cost, lowest_item[2])

def run():
    for item in const_data.po:
        po_watch(item[0], item[1], item[2])

    market_watch()

    discord_hook.send_hb()



run()
time.sleep(31)
run()

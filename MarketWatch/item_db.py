import sqlite3
import const_data
import requests
from secrets import API_KEY, db_name

def update_mv(id_value, threshold, new_mv, name):
    # Connect to SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Check if the id exists
    cursor.execute('SELECT id FROM market WHERE id = ?', (id_value,))
    data = cursor.fetchone()

    if data is not None:
        # If id exists, update the curr_low and quantity
        cursor.execute('''UPDATE market
                          SET market_value = ?,
                          threshold = ?
                          WHERE id = ?''',
                       (new_mv, threshold, id_value))
    else:
        add_item(id_value, new_mv, name, threshold)

    # Commit changes and close connection
    conn.commit()
    conn.close()

def add_item(id_value, default_market_value, name, threshold, default_curr_low=-1, default_quantity=-1):
    # Connect to SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Check if the id already exists
    cursor.execute('SELECT id FROM market WHERE id = ?', (id_value,))
    data = cursor.fetchone()

    if data is None:
        # If id does not exist, insert a new row with default values
        cursor.execute('''INSERT INTO market (id, market_value, curr_low, quantity, threshold, name)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (id_value, default_market_value, default_curr_low, default_quantity, threshold, name))

    # Commit changes and close connection
    conn.commit()
    conn.close()

def loadMarketValues():
    api_request = const_data.torn_api_url + const_data.market_selections + API_KEY
    response = requests.get(api_request)
    itemsList = response.json()
    values = itemsList['items']

    for item in const_data.watch_list:
        update_mv(item[0], item[1], values[item[0]]['market_value'], values[item[0]]['name'])

def create_database():
    # Connect to SQLite database (or create if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create table to store costs and quantities
    cursor.execute('''CREATE TABLE IF NOT EXISTS market (
                        id INTEGER PRIMARY KEY,
                        market_value INTEGER,
                        curr_low INTEGER,
                        quantity INTEGER,
                        threshold INTEGER,
                        name TEXT)''')

    # Commit changes and close connection
    conn.commit()
    conn.close()



create_database()
loadMarketValues()

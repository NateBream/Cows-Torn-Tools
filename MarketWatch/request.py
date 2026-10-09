import const_data
import requests
import api_store

def make_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def make_torn_request(url, params):
    try:
        return api_store.torn_get(url, params)
    except Exception as e:
        print(e)
        return {}

def generate_url(item_id, selection):
    if selection == "tornpal":
        return const_data.tornpal_api_url + str(item_id)

def get_itemmarket(item_id):
    return make_torn_request(const_data.market_url + str(item_id), {'selections': const_data.market_selections})

def get_tornpal(item_id):
    cheapest = [-1, -1, -1]
    data = make_request(generate_url(item_id, "tornpal"))
    for i in data.get('listings', []):
        if i['price'] != 1:
            cheapest = [i['price'], i['quantity'], i['player_id']]
            break

    return cheapest

def get_greenleaf(player_id):
    data = make_torn_request(const_data.torn_api_user_url + str(player_id), {'selections': const_data.greenleaf_selections})

    # Extracting the required fields
    name = data.get("name", {})
    basicicons = data.get("basicicons", {})
    properties = data.get("properties", None)
    faction_name = data.get("faction", {}).get("faction_name", None)
    faction_id = data.get("faction", {}).get("faction_id", None)
    attackslost = data.get("personalstats", {}).get("attackslost", None)
    networth = data.get("personalstats", {}).get("networth", None)

    newb = False
    if "Newbie" in basicicons.values():
        newb = True

    return [newb, name, properties, faction_name, faction_id, attackslost, networth]

import secrets
import const_data
import requests

def make_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def generate_url(item_id, selection):
    if selection == "tornpal":
        return const_data.tornpal_api_url + str(item_id)
    if selection == "itemmarket":
        return const_data.torn_api_url + str(item_id) + const_data.market_selections + secrets.API_KEY + const_data.request_comment
    if selection == "greenleaf":
        return const_data.torn_api_user_url + str(item_id) + const_data.greenleaf_selections + secrets.API_KEY + const_data.request_comment

def get_tornpal(item_id):
    data = make_request(generate_url(item_id, "tornpal"))
    item_data = data.get('listings', [])[0]
    cheapest = [item_data['price'], item_data['quantity'], item_data['player_id']]
    return cheapest

def get_greenleaf(player_id):
    data = make_request(generate_url(player_id, "greenleaf"))

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

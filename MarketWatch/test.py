import requests
import json
from item_list import *
from testdata import *
from secrets import *

def itemInfo(item):
    api_request = API_BASE.format(ITEM_ID=item, SELECTIONS=SELECTIONS, API_KEY=API_KEY)
    response = requests.get(api_request)
    print(torn_items[item])
    return response

def parse(item):
    cheapest = -1

    for x in item:
        if cheapest == -1 or int(x['cost']) < cheapest:
            cheapest = int(x['cost'])

    return cheapest

def getCheapest(response):
    x = response.json()
    # x = json.loads(response)
    
    cheapestItem = -1

    for key in x.items():
        tmp = parse(key[1])
        if cheapestItem == -1 or tmp < cheapestItem:
            cheapestItem = tmp
    print(cheapestItem)

# Makes API request to torn items
# Requests all items from torn_items dict
# Parses out market values
def getMarketValue():
    return

def main():
    getMarketValue()

    for item in torn_items.keys():
        getCheapest(itemInfo(item))
        # getCheapest(test_json_response)

main()

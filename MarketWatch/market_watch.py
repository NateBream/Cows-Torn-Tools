import requests
import json
import time
from mw_item_list import *
from mw_test_data import *
from mw_secrets import *

def getCurrentMarket(item):
    api_request = API_MARKET_BASE.format(ITEM_ID=item, SELECTIONS=SELECTIONS, API_KEY=API_KEY)
    response = requests.get(api_request)
    
    return response

def parse(item):
    cheapest = -1

    for x in item:
        if cheapest == -1 or int(x['cost']) < cheapest:
            cheapest = int(x['cost'])

    return cheapest

def getCheapest(item):    
    cheapestItem = -1
    quantity = 0

    for key in item.items():
        tmp = parse(key[1])
        if cheapestItem == -1 or tmp < cheapestItem:
            cheapestItem = tmp
            quantity = 1
        elif tmp == cheapestItem:
            quantity += 1
    return [cheapestItem, quantity]


# Makes API request to torn items
# Requests all items from torn_items dict
# Parses out market values
def loadMarketValues():
    api_request = API_ITEM_BASE.format(API_KEY=API_KEY)
    response = requests.get(api_request)
    itemsList = response.json()
    values = itemsList['items']
    for item in global_item_dict:
        item['market_value'] = values[item['item_id']]['market_value']

# Creates a dict of 'item_dict' based on 'torn_items'
def loadItemDict():
    for item in torn_items:
        item_dict = {
            'item_id':item[0],         # item id
            'item_name':item[1],         # item name
            'market_value':item[2],    # last recorded market value
            'cheapest_price':item[3],  # last recorded lowest price
            'threshold':item[4],      # threshold below market value to report
            'profit':item[5],          # minimum profit needed to report
            'category':item[6]           # market category
        }

        global_item_dict.append(item_dict)

# initiates discord webhook to post message
def post(profit, item):
    # profit [post, discountRatio, totalProfit, quantity]
    if not profit[0]:
        return
    
    # Make discord post
    discord_url = WEBHOOK_URL.format(WEBHOOK_ID=WEBHOOK_ID, WEBHOOK_TOKEN=WEBHOOK_TOKEN)
    hyperlink = LZPT_URL.format(NAME=item['item_name'].replace(' ', '+'))
    discord_data = {
                    'embeds':[
                        {
                            'title':'MARKET WATCH',
                            'description':'<@&1123320463574188042>',
                            'fields': [
                                {
                                    'name':'Item',
                                    'value':str(item['item_name'])
                                },
                                {
                                    'name':'Price',
                                    'value':str(item['cheapest_price']),
                                    'inline':'true'
                                },
                                {
                                    'name':'Discont',
                                    'value':str(int(profit[1]*100)) + '%',
                                    'inline':'true'
                                },
                                {
                                    'name':'Quantity',
                                    'value':str(profit[3])
                                },
                                {
                                    'name':'Total Profit',
                                    'value':str(profit[2]),
                                    'inline':'true'
                                },
                                {
                                    'name':'Link',
                                    'value':'[Click Here To Go To Market]({})'.format(hyperlink)
                                }
                            ]
                        }
                    ]
    }
   
    r = requests.post(discord_url,  json=discord_data)

def item_engine(item):
    market_json = getCurrentMarket(item['item_id'])
    cheap = getCheapest(market_json.json())
    lowestCost = cheap[0]
    quantity = cheap[1]

    mv = int(item['market_value'])
    totalProfit = (mv - lowestCost) * quantity
    discountRatio = 1-lowestCost/mv

    post = False

    if int(item['profit']) != -1 and totalProfit > int(item['profit']):
        post = True
    
    if float(item['threshold']) <= discountRatio:
        post = True

    if lowestCost == int(item['cheapest_price']):
        post = False

    item['cheapest_price'] = str(lowestCost)


    return [post, discountRatio, totalProfit, quantity]

def main():
    loadItemDict()
    loadMarketValues()
    print('Starting Now')
    i = 0
    while(True):
        for item in global_item_dict:
            profit = item_engine(item)
            post(profit, item)
        time.sleep(30)
        i += 1
        print('Loop ' + str(i))

main()

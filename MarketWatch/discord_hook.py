import requests
import time

import secrets
import const_data

def post(url, data):
    r = requests.post(url, json=data)

def send_hb():
    t = time.strftime("%H:%M:%S", time.localtime())
    discord_data = {
                    'embeds':[
                        {
                            'title':'PO WATCH HB',
                            'description':'HeartBeat',
                            'fields': [
                                {
                                    'name':'Time',
                                    'value':str(t)
                                }
                             ]
                        }
                    ]
    }

    post(secrets.HB_WEBHOOK_URL, discord_data)
    
def post_tornpal(qty, item_name, cost, player_id, item_id, profit):
    if qty == 0:
        return
    
    url = secrets.MARKET_WEBHOOK_URL
    title = 'MARKET WATCH'

    # Make discord post
    if player_id is None :
        hyperlink = const_data.LZPT_MARKET_URL.format(NAME=item_id)
        loc = 'Market'
    else:
        hyperlink = const_data.LZPT_BAZAAR_URL.format(NAME=player_id)
        loc = 'Bazaar'

    t = int(time.time())

    discord_data = {
                    'embeds':[
                        {
                            'title':title,
                            'description':'<@&1123320463574188042>',
                            'fields': [
                                {
                                    'name':'Item',
                                    'value':str(item_name)
                                },
                                {
                                    'name':'Price',
                                    'value':'${:0,.0f}'.format(cost),
                                    'inline':'true'
                                },
                                {
                                    'name':'Quantity',
                                    'value':str(qty)
                                },
                                {
                                    'name':'Total Profit',
                                    'value':str(profit)
                                },
                                {
                                    'name':'Link',
                                    'value':'[Click Here To Go To {}]({})'.format(loc, hyperlink)
                                },
                                {
                                    'name':'Time',
                                    'value':'<t:{}:R>'.format(t)
                                }
                                
                            ]
                        }
                    ]
    }

    post(url, discord_data)

def post_greenleaf(player_id, name, fac, f_id, loss, t_nw):
    # Make discord post
    discord_url = secrets.GL_WEBHOOK_URL

    discord_data = {
                    'embeds':[
                        {
                            'title':'GREENLEAF',
                            'description':'<@&1308267186548113471>',
                            'fields': [
                                {
                                    'name':'Player Name',
                                    'value':'[{}]({})'.format(name, const_data.LZPT_PROFILE_URL.format(NAME=player_id))
                                },
                                {
                                    'name':'Total Networth',
                                    'value':'${:0,.0f}'.format(t_nw),
                                    'inline':'true'
                                },
                                {
                                    'name':'Faction',
                                    'value':'[{}]({})'.format(fac, const_data.LZPT_FACTION_URL.format(NAME=f_id))
                                },
                                {
                                    'name':'Attacks Lost',
                                    'value':str(loss),
                                }
                            ]
                        }
                    ]
    }

    r = requests.post(discord_url,  json=discord_data)

def post_po(qty, item, item_name, cost, player_id, item_id):
    if qty == 0:
        return

    # Make discord post
    discord_url = secrets.PO_WEBHOOK_URL

    if player_id == "null":
        hyperlink = const_data.LZPT_MARKET_URL.format(NAME=item_id)
    else:
        hyperlink = const_data.LZPT_BAZAAR_URL.format(NAME=player_id)

    discord_data = {
                    'embeds':[
                        {
                            'title':'PO WATCH',
                            'description':'<@&1123320463574188042>',
                            'fields': [
                                {
                                    'name':'Item',
                                    'value':str(item_name)
                                },
                                {
                                    'name':'Price Threshold',
                                    'value':'${:0,.0f}'.format(cost),
                                    'inline':'true'
                                },
                                {
                                    'name':'Quantity',
                                    'value':str(qty)
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

#import requests

torn_api_user_url = "https://api.torn.com/user/"
torn_api_url = "https://api.torn.com/"
greenleaf_selections = "?selections=profile,personalstats,properties&key="
market_selections = "torn/?selections=items&key="

LZPT_MARKET_URL = 'https://tcy.sh/m/{NAME}'
LZPT_BAZAAR_URL = 'https://tcy.sh/b/{NAME}'
LZPT_FACTION_URL = 'https://tcy.sh/f/{NAME}'
LZPT_PROFILE_URL = 'https://tcy.sh/p/{NAME}'

request_comment = "&comment=CowsTornTools"

tornpal_api_url = "https://tornpal.com/api/v1/markets/clist/"

watch_list = [
                ["367", 10], # FHC
                ["206", 0.90], # Xanax
                ["366", 0.98], # eDVD
                ["370", 0.98], # Drug Pack
                ["818", 0.98], # 6 Pack Energy Drink
                ["283", 0.98], # Donator Pack
                ["618", 0.90], # Stingray
                ["384", 0.90], # Camel
                ["281", 0.90], # Lion
                ["274", 0.90], # Panda
                ["273", 0.90], # Chamois
                ["269", 0.90], # Monkey
                ["268", 0.90], # Red Fox
                ["261", 0.90], # Wolverine
                ["266", 0.90], # Nessie
                ["258", 0.90], # Jaguar
             ]

po = [#[733, 498, "Blood Bag : A-"]
#       [732, 14950, "Blood Bag: A+"],
#       [734, 15770, "Blood Bag : B+"],
#       [735, 22690, "Blood Bag : B-"],
#       [738, 15020, "Blood Bag : O+"],
#       [739, 20500, "Blood Bag : O-"]
]
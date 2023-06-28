API_MARKET_BASE = 'https://api.torn.com/market/{ITEM_ID}?selections={SELECTIONS}&key={API_KEY}'
API_ITEM_BASE = 'https://api.torn.com/torn/?selections=items&key={API_KEY}'
SELECTIONS = "bazaar,itemmarket"
MARKET_URL = 'https://www.torn.com/imarket.php#/p=market&cat={CATEGORY}'
LZPT_URL = 'https://lzpt.io/m/{NAME}'
WEBHOOK_URL = 'https://discord.com/api/webhooks/{WEBHOOK_ID}/{WEBHOOK_TOKEN}'

global_item_dict = []

item_dict = {
    'item_id':'-1',         # item id
    'item_name':'',         # item name
    'market_value':'-1',    # last recorded market value
    'cheapest_price':'-1',  # last recorded lowest price
    'threshold':'.25',      # threshold below market value to report
    'profit':'-1',          # minimum profit needed to report
    'category':''           # market category
}

torn_items = [
    # Plushies [13] {10}
    # ['186','Sheep Plushie','-1','-1','.25','100000','plushies'],      # Price < 10k
    # ['187','Teddy Bear Plushie','-1','-1','.25','100000','plushies'], # Price < 10k
    # ['215','Kitten Plushie','-1','-1','.25','100000','plushies'],     # Price < 10k
    ['261','Wolverine Plushie','-1','-1','.25','500000','plushies'],
    ['618','Stingray Plushie','-1','-1','.25','500000','plushies'],
    ['273','Chamois Plushie','-1','-1','.25','500000','plushies'],
    ['258','Jaguar Plushie','-1','-1','.25','500000','plushies'],
    ['266','Nessie Plushie','-1','-1','.25','500000','plushies'],
    ['268','Red Fox Plushie','-1','-1','.25','500000','plushies'],
    ['269','Monkey Plushie','-1','-1','.25','500000','plushies'],
    ['274','Panda Plushie','-1','-1','.25','500000','plushies'],
    ['281','Lion Plushie','-1','-1','.25','500000','plushies'],
    ['384','Camel Plushie','-1','-1','.25','500000','plushies'],

    # Flowers [11] {8}
    ['282','African Violet','-1','-1','.25','500000','flowers'],
    ['617','Banana Orchid','-1','-1','.25','500000','flowers'],
    ['271','Ceibo Flower','-1','-1','.25','500000','flowers'],
    ['277','Cherry Blossom','-1','-1','.25','500000','flowers'],
    # ['263','Crocus','-1','-1','.25','100000','flowers'],              # Price < 10k
    # ['260','Dahlia','-1','-1','.25','100000','flowers'],              # Price < 10k
    # ['272','Edelwiess','-1','-1','.25','100000','flowers'],           # Price < 10k
    ['267','Heather','-1','-1','.25','500000','flowers'],
    ['264','Orchid','-1','-1','.25','500000','flowers'],
    ['276','Peony','-1','-1','.25','500000','flowers'],
    ['385','Tribulus Omanense','-1','-1','.25','500000','flowers'],

    # Misc [5]
    ['180','Bottle of Beer','-1','-1','.15','100000','alcohol'],
    ['206','Xanax','-1','-1','.10','1000000','drugs'],
    ['283','Donator Pack','-1','-1','.5','1000000','supply-packs'],
    ['367','Feathery Hotel Coupon','-1','-1','.10','1000000','other-boosters'],
    ['366','Erotic DVD','-1','-1','.10','1000000','other-boosters']

    # Total [29] {23}
]

# torn_items = [torn_items2[0]]
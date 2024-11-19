import time
import discord_hook
import request
from secrets import leaf_file

def check_leaf(player_id):
    data = request.get_greenleaf(player_id)
    print(player_id)

    if (data[0] is True):
        return False # Still green leaf

    # [newb, name, properties, faction_name, faction_id, attackslost, networth]

    if (data[2] is not None):
        for p in data[2]:
            p_data = data[2].get(p)

            p_status = p_data.get('status')
            p_vault = p_data.get('modifications').get('vault')

            if p_status == "Owned by them" and p_vault != 0:
                print("Owns a bad property")
                print(p_status)
                print(p_vault)
                return True # They own a vault so presumably store money safely

    name = data[1]
    fac  = data[3]
    f_id = data[4]
    loss = data[5]
    t_nw = data[6]

    if (t_nw > 100000000):
        discord_hook.post_greenleaf(player_id, name, fac, f_id, loss, t_nw)
    
    return True

def greenleaf():
    f = open(leaf_file, "r+")

    p_id = f.read()

    while (check_leaf(p_id)):
        p_id = int(p_id) + 1
        f.seek(0)
        f.write(str(p_id))
        time.sleep(3)
    print(p_id)
    f.close()

greenleaf()
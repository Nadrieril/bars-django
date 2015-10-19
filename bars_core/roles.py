roles_map = {}
roles_map['customer'] = [
    'bars_transactions.add_transaction',
    'bars_transactions.add_buytransaction',
    'bars_transactions.add_throwtransaction',
    'bars_transactions.add_givetransaction',
    'bars_transactions.add_mealtransaction',
    'bars_bugtracker.add_bugreport',
    'bars_menus.add_menu',
    'bars_items.add_suggesteditem',
    'bars_items.change_suggesteditem',
]
roles_map['agios_daemon'] = [
    'bars_transactions.add_transaction',
    'bars_transactions.add_agiostransaction',
]

# News
roles_map['newsmanager'] = [
    'bars_news.add_news',
    'bars_news.change_news',
    'bars_news.delete_news',
]

# Money
roles_map['policeman'] = [
    'bars_transactions.add_transaction',
    'bars_transactions.add_punishtransaction',
]
roles_map['accountmanager'] = [
    'bars_core.add_account',
    'bars_core.change_account',
]
roles_map['treasurer'] = \
    roles_map['policeman'] + [
        'bars_transactions.add_transaction',
        'bars_transactions.add_deposittransaction',
        'bars_transactions.add_withdrawtransaction',
        'bars_transactions.add_refundtransaction',
        'bars_transactions.add_barInvestmenttransaction',
        'bars_transactions.add_collectivePaymenttransaction',
        'bars_core.change_barsettings', # to let the treasurer adjust agios parameters
]

# Items
roles_map['itemmanager'] = [
    'bars_items.add_buyitemprice',
    'bars_items.change_buyitemprice',
    'bars_items.add_sellitem',
    'bars_items.change_sellitem',
    'bars_items.add_stockitem',
    'bars_items.change_stockitem',
]
roles_map['inventorymanager'] = [
    'bars_transactions.add_transaction',
    'bars_transactions.add_inventorytransaction',
]
roles_map['appromanager'] = \
    roles_map['itemmanager'] + [
        'bars_transactions.add_transaction',
        'bars_transactions.add_approtransaction',
        'bars_items.add_suggesteditem',
        'bars_items.change_suggesteditem',
        'bars_items.delete_suggesteditem',
]
roles_map['stockmanager'] = \
    roles_map['appromanager'] + \
    roles_map['inventorymanager']

# Staff
roles_map['staff'] = \
    roles_map['treasurer'] + \
    roles_map['accountmanager'] + \
    roles_map['stockmanager'] + \
    roles_map['newsmanager'] + [
        'bars_core.change_barsettings',
        'bars_transactions.change_transaction',
        'bars_bugtracker.change_bugreport',
]
roles_map['admin'] = \
    roles_map['staff'] + [
        'bars_core.add_role',
        'bars_core.delete_role',
]


# Root
root_roles_map = {}
root_roles_map['barmanager'] = [
    'bars_core.add_bar',
    'bars_core.change_bar',
    'bars_core.delete_bar',
]
root_roles_map['usercreator'] = [
    'bars_core.add_user',
]
root_roles_map['usermanager'] = \
    root_roles_map['usercreator'] + [
    'bars_core.change_user',
    'bars_core.delete_user',
]
root_roles_map['itemcreator'] = [
    'bars_items.add_buyitem',
    'bars_items.add_itemdetails',
]
root_roles_map['itemmanager'] = \
    root_roles_map['itemcreator'] + [
        'bars_items.change_buyitem',
        'bars_items.change_itemdetails',
]

root_roles_map['staff'] = \
    root_roles_map['usercreator'] + \
    root_roles_map['itemcreator'] + [
        # 'bars_core.add_limitedrole',
]

root_roles_map['admin'] = \
    root_roles_map['barmanager'] + \
    root_roles_map['usermanager'] + \
    root_roles_map['itemmanager'] + [
        'bars_core.add_role',
        'bars_core.delete_role',
]


roles_list = list(set(roles_map.keys()) | set(root_roles_map.keys()))

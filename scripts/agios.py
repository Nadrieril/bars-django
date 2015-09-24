from bars_core.models.account import Account

def run():
    sum = 0
    for a in Account.objects.select_related('bar'):
        sum += a.bar.apply_agios(a)
    print("Done (took %f euros)" % sum)

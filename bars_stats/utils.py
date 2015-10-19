# From https://github.com/kmike/django-qsstats-magic
from django.conf import settings
def _guess_engine(qs):
    if hasattr(qs, 'db'): # django 1.2+
        engine_name = settings.DATABASES[qs.db]['ENGINE']
    else:
        engine_name = settings.DATABASE_ENGINE
    if 'mysql' in engine_name:
        return 'mysql'
    if 'postg' in engine_name: #postgres, postgis
        return 'postgresql'
    if 'sqlite' in engine_name:
        return 'sqlite'

# From https://github.com/kmike/django-qsstats-magic
def _get_interval_sql(date_field, interval, engine):
    ''' Returns SQL clause that calculates the beginning of interval
        date_field belongs to.
    '''

    SQL = {
        'mysql': {
            'minutes': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-%%d %%H:%%i')",
            'hours': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-%%d %%H:00')",
            'days': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-%%d')",
            'weeks': "DATE_FORMAT(DATE_SUB(`"+date_field+"`, INTERVAL(WEEKDAY(`"+date_field+"`)) DAY), '%%Y-%%m-%%d')",
            'months': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-01')",
            'years': "DATE_FORMAT(`" + date_field +"`, '%%Y-01-01')",
            'hours_of_day': "DATE_FORMAT(`" + date_field +"`, '%%H')",
            'days_of_week': "WEEKDAY(`"+date_field+"`)",
            'months_of_year': "DATE_FORMAT(`" + date_field +"`, '%%m')",
        },
        'postgresql': {
            'minutes': "date_trunc('minute', %s)" % date_field,
            'hours': "date_trunc('hour', %s)" % date_field,
            'days': "date_trunc('day', %s)" % date_field,
            'weeks': "date_trunc('week', %s)" % date_field,
            'months': "date_trunc('month', %s)" % date_field,
            'years': "date_trunc('year', %s)" % date_field,
            'hours_of_day': "extract(hour from %s)" % date_field,
            'days_of_week': "extract(dow from %s)" % date_field,
            'months_of_year': "extract(month from %s)" % date_field,
        },
        'sqlite': {
            'minutes': "strftime('%%Y-%%m-%%d %%H:%%M', `" + date_field + "`)",
            'hours': "strftime('%%Y-%%m-%%d %%H:00', `" + date_field + "`)",
            'days': "strftime('%%Y-%%m-%%d', `" + date_field + "`)",
            'weeks':  "strftime('%%Y-%%m-%%d', julianday(`" + date_field + "`) - strftime('%%w', `" + date_field + "`) + 1)",
            'months': "strftime('%%Y-%%m-01', `" + date_field + "`)",
            'years': "strftime('%%Y-01-01', `" + date_field + "`)",
            'hours_of_day': "strftime('%%H', `" + date_field + "`)",
            'days_of_week': "strftime('%%w', `" + date_field + "`)",
            'months_of_year': "strftime('%%m', `" + date_field + "`)",
        },
    }

    try:
        engine_sql = SQL[engine]
    except KeyError:
        msg = '%s DB engine is not supported. Supported engines are: %s' % (engine, ", ".join(SQL.keys()))
        raise Exception(msg)

    try:
        return engine_sql[interval]
    except KeyError:
        raise Exception('Interval is not supported for %s DB backend.' % engine)


# Inspired from https://github.com/kmike/django-qsstats-magic
from datetime import datetime
from django.db.models import Count, Sum, F
from bars_transactions.models import Transaction
from bars_core.models.bar import Bar
from bars_core.models.account import Account
from bars_items.models.sellitem import SellItem
def time_series(qs, date_field, aggregate=None, interval='days', engine=None):
    aggregate = aggregate or Count('id')
    engine = engine or _guess_engine(qs)

    interval_sql = _get_interval_sql(date_field, interval, engine)
    aggregate_data = qs.extra(select = {'agg_date': interval_sql}).\
                            order_by().values('agg_date').\
                            annotate(agg=aggregate)

    return [(x['agg_date'], x['agg']) for x in aggregate_data]


def compute_transaction_stats(request, filter=id, aggregate=None):
    qs = Transaction.objects.filter(canceled=False)
    qs = filter(qs)

    if request.bar:
        qs = qs.filter(bar=request.bar)

    date_start = request.query_params.get('date_start')
    date_end = request.query_params.get('date_end', datetime.now())
    if date_start is not None:
        qs = qs.filter(timestamp__range=(date_start, date_end))

    types = request.query_params.getlist("type")
    if len(types) != 0:
        qs = qs.filter(type__in=types)

    qs = qs.order_by('-timestamp', '-id').distinct()

    interval = request.query_params.get('interval', 'days')
    result = time_series(qs, date_field='timestamp', interval=interval, aggregate=aggregate)
    return sorted(result)

def compute_total_spent(request, filter=id, aggregate=None):
    qs = Transaction.objects.filter(canceled=False)
    qs = filter(qs)

    if request.bar:
        qs = qs.filter(bar=request.bar)

    date_start = request.query_params.get('date_start')
    date_end = request.query_params.get('date_end', datetime.now())
    if date_start is not None:
        qs = qs.filter(timestamp__range=(date_start, date_end))

    types = request.query_params.getlist("type")
    if len(types) != 0:
        qs = qs.filter(type__in=types)

    result = qs.aggregate(total_spent = Sum('accountoperation__delta'))
    return result

def compute_ranking(request, model=Account, t_path='accountoperation__transaction__', filter={}, annotate=None, all_bars=False):
    t_filter = {}
    if not all_bars:
        bar = request.query_params.get('bar')
        if bar is None:
            return None
        else:
            t_filter[t_path + 'bar'] = bar
    
    t_filter[t_path + 'canceled'] = False
    
    date_start = request.query_params.get('date_start')
    date_end = request.query_params.get('date_end', datetime.now())
    if date_start is not None:
        t_filter[t_path + 'timestamp__range'] = (date_start, date_end)
    
    types = request.query_params.getlist("type")
    if len(types) != 0:
        t_filter[t_path + 'type__in'] = types

    t_filter.update(filter)

    qs = model.objects.filter(**t_filter)

    return qs.values('id').annotate(val=annotate)

from django.db import models
from rest_framework import viewsets, serializers, permissions

from bars_django.utils import VirtualField, permission_logic, CurrentBarCreateOnlyDefault
from bars_core.perms import PerBarPermissionsOrAnonReadOnly, BarRolePermissionLogic
from bars_core.models.bar import Bar
# from bars_items.models.itemdetails import ItemDetails
# from bars_items.models.sellitem import SellItem


@permission_logic(BarRolePermissionLogic())
class StockItem(models.Model):
    class Meta:
        unique_together = ("bar", "details")
        app_label = 'bars_items'
    bar = models.ForeignKey(Bar)
    details = models.ForeignKey("ItemDetails")
    sellitem = models.ForeignKey('SellItem', related_name="stockitems")

    qty = models.FloatField(default=0)
    unit_factor = models.FloatField(default=1)
    price = models.FloatField()

    deleted = models.BooleanField(default=False)

    def get_unit(self, unit=''):
        return {'':1., 'sell':self.unit_factor, 'buy':1.}[unit]

    def get_price(self, unit='', tax=True):
        taxfactor = 1. + (self.sellitem.tax if tax else 0)
        return self.price * taxfactor / self.get_unit(unit)

    def create_operation(self, unit='', **kwargs):
        from bars_transactions.models import ItemOperation
        if 'delta' in kwargs:
            kwargs['delta'] = kwargs['delta'] / self.get_unit(unit)
        if 'next_value' in kwargs:
            kwargs['next_value'] = kwargs['next_value'] / self.get_unit(unit)
        io = ItemOperation(target=self, **kwargs)
        io.save()
        return io


    @property
    def sell_to_buy(self):
        return self.get_unit('buy') / self.get_unit('sell')

    @sell_to_buy.setter
    def sell_to_buy(self, value):
        self.unit_factor = self.get_unit('buy') / value


    @property
    def display_price(self):
        return self.get_price(unit='sell', tax=False)

    @display_price.setter
    def display_price(self, value):
        self.price = value * self.get_unit('sell')


    @property
    def sell_qty(self):
        return self.qty * self.get_unit('sell')

    @property
    def sell_price(self):
        return self.get_price(unit='sell')

    def __unicode__(self):
        return "%s (%s)" % (unicode(self.details), unicode(self.bar))


class StockItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItem
        exclude = ('unit_factor',)

    _type = VirtualField("StockItem")
    bar = serializers.PrimaryKeyRelatedField(read_only=True, default=CurrentBarCreateOnlyDefault())
    qty = serializers.FloatField(source='sell_qty', read_only=True)
    price = serializers.FloatField(source='display_price')
    sell_to_buy = serializers.FloatField()

    def validate_sell_to_buy(self, value):
        if value <= 0:
            raise ValidationError("'sell_to_buy' field has to be nonnegative")
        return value


class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (PerBarPermissionsOrAnonReadOnly,)
    filter_fields = ['bar', 'details', 'sellitem']

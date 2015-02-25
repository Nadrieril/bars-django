from django.db import models
from rest_framework import viewsets, serializers, permissions
from rest_framework.validators import UniqueTogetherValidator

from bars_django.utils import VirtualField, CurrentBarCreateOnlyDefault
from bars_core.models.bar import Bar
from bars_core.perms import PerBarPermissionsOrAnonReadOnly
from bars_items.models.itemdetails import ItemDetails


class BuyItem(models.Model):
    class Meta:
        app_label = 'bars_items'
    barcode = models.CharField(max_length=25, blank=True)
    details = models.ForeignKey(ItemDetails)
    itemqty = models.FloatField(default=1)

    def __unicode__(self):
        return "%s * %f %s" % (unicode(self.details), self.itemqty * self.details.unit_value, self.details.unit_name)

class BuyItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyItem
    _type = VirtualField("BuyItem")


class BuyItemViewSet(viewsets.ModelViewSet):
    queryset = BuyItem.objects.all()
    serializer_class = BuyItemSerializer
    permission_classes = (permissions.AllowAny,)  # TODO: temporary
    filter_fields = ['barcode', 'details']



class BuyItemPrice(models.Model):
    class Meta:
        unique_together = ("bar", "buyitem")
        app_label = 'bars_items'
    bar = models.ForeignKey(Bar)
    buyitem = models.ForeignKey(BuyItem)
    price = models.FloatField(default=0)

    def __unicode__(self):
        return "%s (%s)" % (unicode(self.buyitem), unicode(self.bar))

class BuyItemPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyItemPrice
        read_only_fields = ("bar",)

    _type = VirtualField("BuyItemPrice")
    bar = serializers.PrimaryKeyRelatedField(read_only=True, default=CurrentBarCreateOnlyDefault())



class BuyItemPriceViewSet(viewsets.ModelViewSet):
    queryset = BuyItemPrice.objects.all()
    serializer_class = BuyItemPriceSerializer
    permission_classes = (permissions.AllowAny,)  # TODO: temporary
    filter_fields = ['bar', 'buyitem']

from mock import Mock
from rest_framework import exceptions, serializers
from rest_framework.test import APITestCase
from bars_django.utils import get_root_bar

from bars_core.models.bar import Bar
from bars_core.models.user import User
from bars_core.models.role import Role
from bars_core.models.account import Account

from bars_items.models.buyitem import BuyItem, BuyItemSerializer, BuyItemPrice, BuyItemPriceSerializer
from bars_items.models.itemdetails import ItemDetails, ItemDetailsSerializer
from bars_items.models.sellitem import SellItem, SellItemSerializer
from bars_items.models.stockitem import StockItem, StockItemSerializer
from bars_items.models.suggesteditem import SuggestedItem, SuggestedItemSerializer


def reload(obj):
    return obj.__class__.objects.get(pk=obj.pk)


class AutoTestGetMixin():
    def test_get(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.get_url)
        self.assertEqual(len(response.data), self.model.objects.count())


class AutoTestCreateBarMixin():
    def test_create(self):
        # Unauthenticated
        response = self.client.post(self.create_url % self.bar.id, self.create_data)
        self.assertEqual(response.status_code, 401)

    def test_create1(self):
        # Wrong permissions
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url % self.bar.id, self.create_data)
        self.assertEqual(response.status_code, 403)

    def test_create2(self):
        # Correct permissions
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.create_url % self.bar.id, self.create_data)
        self.assertEqual(response.status_code, 201)

    def test_create3(self):
        # Wrong bar
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.create_url % self.wrong_bar.id, self.create_data)
        self.assertEqual(response.status_code, 403)

class AutoTestChangeBarMixin():
    def test_change(self):
        # Unauthenticated
        response = self.client.put(self.change_url % self.bar.id, self.update_data)
        self.assertEqual(response.status_code, 401)

    def test_change1(self):
        # Wrong permissions
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.change_url % self.bar.id, self.update_data)
        self.assertEqual(response.status_code, 403)

    def test_change2(self):
        # Correct permissions
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(self.change_url % self.bar.id, self.update_data)
        self.assertEqual(response.status_code, 200)

    def test_change3(self):
        # Wrong bar
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(self.change_url % self.wrong_bar.id, self.update_data)
        self.assertEqual(response.status_code, 403)

class AutoTestBarMixin(AutoTestGetMixin, AutoTestCreateBarMixin, AutoTestChangeBarMixin):
    pass


class AutoTestCreateMixin():
    def test_create(self):
        # Unauthenticated
        response = self.client.post(self.create_url, self.create_data)
        self.assertEqual(response.status_code, 401)

    def test_create1(self):
        # Wrong permissions
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url, self.create_data)
        self.assertEqual(response.status_code, 403)

    def test_create2(self):
        # Correct permissions
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.create_url, self.create_data)
        self.assertEqual(response.status_code, 201)

class AutoTestChangeMixin():
    def test_change(self):
        # Unauthenticated
        response = self.client.put(self.change_url, self.update_data)
        self.assertEqual(response.status_code, 401)

    def test_change1(self):
        # Wrong permissions
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.change_url, self.update_data)
        self.assertEqual(response.status_code, 403)

    def test_change2(self):
        # Correct permissions
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(self.change_url, self.update_data)
        self.assertEqual(response.status_code, 200)

class AutoTestMixin(AutoTestGetMixin, AutoTestCreateMixin, AutoTestChangeMixin):
    pass



class ItemTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(ItemTests, self).setUpTestData()
        get_root_bar._cache = None  # Workaround
        self.bar, _ = Bar.objects.get_or_create(id='barjone')
        self.wrong_bar, _ = Bar.objects.get_or_create(id='barrouje')

        self.user, _ = User.objects.get_or_create(username='user')
        self.account, _ = Account.objects.get_or_create(bar=self.bar, owner=self.user)
        self.wrong_user, _ = User.objects.get_or_create(username='wrong_user')
        self.wrong_account, _ = Account.objects.get_or_create(bar=self.wrong_bar, owner=self.wrong_user)

        self.staff_user, _ = User.objects.get_or_create(username='staff_user')
        self.staff_account, _ = Account.objects.get_or_create(bar=self.bar, owner=self.staff_user)
        Role.objects.get_or_create(name='staff', bar=self.bar, user=self.staff_user)
        Role.objects.get_or_create(name='admin', bar=get_root_bar(), user=self.staff_user)
        self.staff_user = reload(self.staff_user)

        self.sellitem, _ = SellItem.objects.get_or_create(bar=self.bar, name="Chocolat", tax=0.2)
        self.itemdetails, _ = ItemDetails.objects.get_or_create(name="Chocolat")
        self.buyitem, _ = BuyItem.objects.get_or_create(details=self.itemdetails, itemqty=2.5)
        self.stockitem, _ = StockItem.objects.get_or_create(bar=self.bar, sellitem=self.sellitem, details=self.itemdetails, price=1)

        self.sellitem2, _ = SellItem.objects.get_or_create(bar=self.bar, tax=0.1)
        self.itemdetails2, _ = ItemDetails.objects.get_or_create(name="Pizza")
        self.buyitem2, _ = BuyItem.objects.get_or_create(details=self.itemdetails2, itemqty=3)
        self.buyitemprice2, _ = BuyItemPrice.objects.get_or_create(buyitem=self.buyitem2, bar=self.bar, price=2)
        # self.stockitem2, _ = StockItem.objects.get_or_create(bar=self.bar, sellitem=self.sellitem2, details=self.itemdetails2, price=7)


class SellItemTests(ItemTests, AutoTestBarMixin):
    @classmethod
    def setUpTestData(self):
        super(SellItemTests, self).setUpTestData()
        self.model = SellItem

        self.get_url = '/sellitem/'

        self.create_url = '/sellitem/?bar=%s'
        self.create_data = {'name': 'Glace'}

        self.change_url = ('/sellitem/%d/' % self.sellitem.id) + '?bar=%s'
        self.update_data = SellItemSerializer(self.sellitem).data
        self.update_data['tax'] = 0.1


class ItemDetailsTests(ItemTests, AutoTestMixin):
    @classmethod
    def setUpTestData(self):
        super(ItemDetailsTests, self).setUpTestData()
        self.model = ItemDetails

        self.get_url = '/itemdetails/'

        self.create_url = '/itemdetails/'
        self.create_data = {'name': 'Glace'}

        self.change_url = '/itemdetails/%d/' % self.itemdetails.id
        self.update_data = ItemDetailsSerializer(self.itemdetails).data
        self.update_data['keywords'] = 'glace'


class BuyItemTests(ItemTests, AutoTestMixin):
    @classmethod
    def setUpTestData(self):
        super(BuyItemTests, self).setUpTestData()
        self.model = BuyItem

        self.get_url = '/buyitem/'

        self.create_url = '/buyitem/'
        self.create_data = {'details': self.itemdetails2.id}

        self.change_url = '/buyitem/%d/' % self.buyitem.id
        self.update_data = BuyItemSerializer(self.buyitem).data
        self.update_data['itemqty'] = 2


class StockItemTests(ItemTests, AutoTestBarMixin):
    @classmethod
    def setUpTestData(self):
        super(StockItemTests, self).setUpTestData()
        self.model = StockItem

        self.get_url = '/stockitem/'

        itemdetails3, _ = ItemDetails.objects.get_or_create(name="Brioche")
        self.create_url = '/stockitem/?bar=%s'
        self.create_data = {'details': itemdetails3.id, 'sellitem': self.sellitem.id, 'price': 1, 'sell_to_buy': 1}

        self.change_url = ('/stockitem/%d/' % self.stockitem.id) + '?bar=%s'
        self.update_data = StockItemSerializer(self.stockitem).data
        self.update_data['price'] = 4
        
class SuggestedItemTests(ItemTests, AutoTestBarMixin):
    @classmethod
    def setUpTestData(self):
        super(SuggestedItemTests, self).setUpTestData()
        self.model = SuggestedItem

        self.get_url = '/suggesteditem/'

        self.create_url = '/suggesteditem/?bar=%s'
        self.create_data = {'name': 'Brioche', 'voters_list': [self.user]}

        self.change_url = ('/suggesteditem/%d/' % self.suggesteditem.id) + '?bar=%s'
        self.update_data = SuggestedItemSerializer(self.suggesteditem).data


from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase

from bars_core.models.bar import Bar
from bars_core.models.user import User
from bars_core.models.role import Role
from bars_core.models.account import Account

from bars_items.models.buyitem import BuyItem
from bars_items.models.itemdetails import ItemDetails
from bars_items.models.sellitem import SellItem
from bars_items.models.stockitem import StockItem

from bars_transactions.models import Transaction


def reload(obj):
    return obj.__class__.objects.get(pk=obj.pk)

class TransactionTests(APITestCase):
    @classmethod

    #Set up data for TransactionTests : implementation of users, items, transactions
    def setUpTestData(self):
        super(TransactionTests, self).setUpTestData()
        self.bar, _ = Bar.objects.get_or_create(id='barjone')
        self.wrong_bar, _ = Bar.objects.get_or_create(id='barrouje')

        self.user, _ = User.objects.get_or_create(username='user')
        self.user.role_set.all().delete()
        self.user = reload(self.user)
        self.account, _ = Account.objects.get_or_create(bar=self.bar, owner=self.user)
        self.account.money = 100
        self.account.save()

        self.wrong_user, _ = User.objects.get_or_create(username='wrong_user')
        self.wrong_account, _ = Account.objects.get_or_create(bar=self.wrong_bar, owner=self.wrong_user)

        #we define a member of the staff in the bar
        self.staff_user, _ = User.objects.get_or_create(username='staff_user')
        self.staff_account, _ = Account.objects.get_or_create(bar=self.bar, owner=self.staff_user)
        self.staff_role, _ = Role.objects.get_or_create(name='staff', bar=self.bar, user=self.staff_user)

        self.sellitem, _ = SellItem.objects.get_or_create(bar=self.bar, name="Chocolat", tax=0.2)
        self.itemdetails, _ = ItemDetails.objects.get_or_create(name="Chocolat")
        self.buyitem, _ = BuyItem.objects.get_or_create(details=self.itemdetails, itemqty=2.5)
        self.stockitem, _ = StockItem.objects.get_or_create(bar=self.bar, sellitem=self.sellitem, details=self.itemdetails, price=1)
        self.stockitem.unit_factor = 5
        self.stockitem.qty = 5
        self.stockitem.save()

        self.transaction = Transaction.objects.create(bar=self.bar, author=self.user)
        self.transaction_url = '/transaction/%d/' % self.transaction.id


    def setUp(self):
        self.transaction.canceled = False
        self.transaction.uncanceled = False
        self.transaction.save()
        Role.objects.get_or_create(user=self.user, bar=self.bar, name='customer')
        self.user = reload(self.user)
        self.staff_user = reload(self.staff_user)

    def test_cancel_transaction(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.transaction_url + 'cancel/', {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(reload(self.transaction).canceled)

    def test_restore_transaction(self):
        self.transaction.canceled = True
        self.transaction.uncanceled = True
        self.transaction.save()
        self.client.force_authenticate(user=self.user)

        response = self.client.put(self.transaction_url + 'restore/', {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(reload(self.transaction).canceled)

    def test_cancel_transaction_wrong_user(self):
        self.client.force_authenticate(user=self.wrong_user)

        response = self.client.put(self.transaction_url + 'cancel/', {})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(reload(self.transaction).canceled)

    def test_cancel_transaction_staff(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.put(self.transaction_url + 'cancel/', {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(reload(self.transaction).canceled)

    def test_cancel_transaction_staff_wrong_bar(self):
        self.client.force_authenticate(user=self.staff_user)
        transaction = Transaction.objects.create(bar=self.wrong_bar, author=self.wrong_user)

        response = self.client.put('/transaction/%d/cancel/' % transaction.id, {})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(reload(transaction).canceled)

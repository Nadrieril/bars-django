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

class TransactionOperationTests(APITestCase):
    @classmethod
    #Set up data for TransactionOperationTests : implementation of users, items, transactions
    
    def setUpTestData(self):
        super(TransactionOperationTests, self).setUpTestData()
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
        self.staff_account.money = 50
        self.staff_account.save()
        self.staff_role, _ = Role.objects.get_or_create(name='staff', bar=self.bar, user=self.staff_user)
        
        #we define a policeman in the bar
        self.policeman_user, _= User.objects.get_or_create(username='policeman')
        self.policeman_account, _ = Account.objects.get_or_create(bar=self.bar, owner=self.policeman_user)
        self.policeman_role, _ = Role.objects.get_or_create(name='policeman', bar=self.bar, user=self.policeman_user)
        
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
        self.transaction.save()
        Role.objects.get_or_create(user=self.user, bar=self.bar, name='customer')
        self.user = reload(self.user)
        self.staff_user = reload(self.staff_user)
    
    def test_create_cancel_buytransaction(self):
        data = {'type':'buy', 'stockitem':self.stockitem.id, 'qty':1}
        start_qty = reload(self.stockitem).qty
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/transaction/?bar=%s' % self.bar.id, data)
        self.assertEqual(response.status_code, 201)
        end_qty = reload(self.stockitem).qty
        self.assertEqual(end_qty, start_qty - 1. / self.stockitem.get_unit('sell'))
        transaction_id = response.data['id']
        
        response2 = self.client.put('/transaction/%d/cancel/' % transaction_id, {})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(reload(self.stockitem).qty, start_qty)
        
        response3 = self.client.put('/transaction/%d/cancel/' % transaction_id, {})
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(reload(self.stockitem).qty, start_qty)
        
        response4 = self.client.put('/transaction/%d/restore/' % transaction_id, {})
        self.assertEqual(response4.status_code, 200)
        self.assertEqual(reload(self.stockitem).qty, end_qty)
    
    def test_create_cancel_punishtransaction(self):
        customer_role = Role.objects.create(name='customer', bar=self.bar, user=self.user)
        self.user = reload(self.user)
        data = {'type': 'punish', 'amount': 50, 'motive': 'Amende', 'account': self.account.id}
        
        #Testing cancellation operation and money left on the account
        self.client.force_authenticate(user=self.policeman_user)
        response = self.client.post('/transaction/?bar=%s' % self.bar.id, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(reload(self.account).money, 50) # previous money was 100
        
        #Testing cancellement be cancelled by the policeman and that the account.money is reactualized
        transaction_id = response.data['id']
        response2 = self.client.put('/transaction/%d/cancel/' % transaction_id, {})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(reload(self.account).money, 100)
        
        #Testing restoration
        response3 = self.client.put('/transaction/%d/restore/' % transaction_id, {})
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(reload(self.account).money, 50)
        
        #Test that the respobar can be punished an he cannot cancel it
        data1 = {'type': 'punish', 'amount': 50, 'motive': 'Amende', 'account': self.staff_account.id}
        response1 = self.client.post('/transaction/?bar=%s' % self.bar.id, data1)
        self.assertEqual(response1.status_code, 201)
        transaction_id1 = response1.data['id']
        
        self.client.logout()
        self.client.force_authenticate(user=self.staff_user)
        response4 = self.client.put('/transaction/%d/cancel/' % transaction_id1, {})
        self.assertEqual(response4.status_code, 403)
        self.assertEqual(reload(self.staff_account).money, 0)
    
    def test_cancel_transaction_after_threshold(self):
        self.bar.cancel_transaction_threshold = 48
        self.bar.save()
        transaction = Transaction.objects.create(bar=self.bar, author=self.user)
        transaction.timestamp = timezone.now() - timedelta(hours=49)
        transaction.save()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.put('/transaction/%d/cancel/' % transaction.id, {})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(reload(transaction).canceled)
        
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put('/transaction/%d/cancel/' % transaction.id, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(reload(transaction).canceled)
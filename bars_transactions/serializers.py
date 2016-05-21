# encoding: utf8
import math

from django.core.mail import send_mail
from django.utils import timezone

from django.http import Http404
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework import exceptions

from bars_core.models.user import get_default_user
from bars_core.models.account import Account, get_default_account
from bars_items.models.buyitem import BuyItem, BuyItemPrice
from bars_items.models.stockitem import StockItem
from bars_items.models.sellitem import SellItem
from bars_transactions.models import Transaction

ERROR_MESSAGES = {
    'negative': "%(field)s must be positive",
    'wrong_bar': "%(model)s (id=%(id)d) is in the wrong bar",
    'deleted': "%(model)s (id=%(id)d) is deleted"
}

class BaseTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        read_only_fields = ('bar', 'author', 'timestamp', 'last_modified', 'moneyflow', )

    def to_representation(self, transaction):
        if 'ignore_type' in self.context or transaction.type == "":
            obj = super(BaseTransactionSerializer, self).to_representation(transaction)

            for a in transaction.author.account_set.all():
                if a.bar_id == transaction.bar_id:
                    obj["author_account"] = a.id

            if self.context.get('request') is not None:
                authed_user = self.context['request'].user
                obj['can_cancel'] = authed_user.has_perm('bars_transactions.change_transaction', transaction)

            obj['_type'] = "Transaction"

            return obj
        else:
            serializer = serializers_class_map[transaction.type](transaction, context=self.context)
            try:
                return serializer.data
            except Exception as e:
                obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
                obj['type'] = 'error'
                obj['error'] = str(e)
                return obj

    def create(self, data):
        request = self.context['request']
        bar = request.bar
        if bar is None:
            raise Http404()

        if request.user.has_perm('bars_transactions.add_' + data["type"] + 'transaction', bar):
            fields = Transaction._meta.get_all_field_names()
            attrs = {k: v for k, v in data.items() if k in fields}
            t = Transaction(**attrs)
            t.author = request.user
            t.bar = bar
            t.save()
            return t

        else:
            raise exceptions.PermissionDenied()



class ItemQtySerializer(serializers.Serializer):
    stockitem = serializers.PrimaryKeyRelatedField(queryset=StockItem.objects.all(), required=False)
    sellitem = serializers.PrimaryKeyRelatedField(queryset=SellItem.objects.all(), required=False)
    qty = serializers.FloatField()

    def validate_qty(self, value):
        if value < 0:
            raise ValidationError(ERROR_MESSAGES['negative'] % {'field':"Quantity"})
        return value

    def validate_stockitem(self, item):
        err_params = {'model':'StockItem', 'id':item.id}
        if item is not None and item.deleted:
            raise ValidationError(ERROR_MESSAGES['deleted'] % err_params)

        if item is not None and self.context['request'].bar.id != item.bar.id:
            raise ValidationError(ERROR_MESSAGES['wrong_bar'] % err_params)

        return item

    def validate_sellitem(self, item):
        err_params = {'model':'SellItem', 'id':item.id}
        if item is not None and item.deleted:
            raise ValidationError(ERROR_MESSAGES['deleted'] % err_params)

        if item is not None and self.context['request'].bar.id != item.bar.id:
            raise ValidationError(ERROR_MESSAGES['wrong_bar'] % err_params)

        return item

    def validate(self, data):
        if "stockitem" in data and "sellitem" in data:
            raise ValidationError("Two items were given")
        if "stockitem" not in data and "sellitem" not in data:
            raise ValidationError("No items were given")
        return data


    def create(self, data):
        t = self.context['transaction']
        qty = data['qty']

        if "stockitem" in data:
            stockitem = data['stockitem']
            stockitem.create_operation(delta=-qty, unit='sell', transaction=t)

            return qty * stockitem.get_price(unit='sell')

        elif "sellitem" in data:
            sellitem = data['sellitem']
            if not sellitem.sell_fraction:
                qty = math.ceil(qty)
            total_qty = sellitem.calc_qty()
            stockitems = sellitem.stockitems.all()

            total_price = 0
            for si in stockitems.all():
                if total_qty != 0:
                    delta = (si.sell_qty * qty) / total_qty
                else:
                    delta = qty / stockitems.count()

                si.create_operation(delta=-delta, unit='sell', transaction=t, fuzzy=True)
                total_price += delta * si.get_price(unit='sell')

            return total_price

    @staticmethod
    def serializeOperations(iops, force_fuzzy=True):
        stockitems = []
        sellitem_map = {}
        for iop in iops:
            stockitem = iop.target
            delta = iop.delta * stockitem.get_unit('sell')
            if iop.fuzzy or force_fuzzy:
                sellitem = stockitem.sellitem
                if sellitem.id not in sellitem_map:
                    sellitem_map[sellitem.id] = {'sellitem':sellitem.id, 'qty':0}
                sellitem_map[sellitem.id]['qty'] += delta
            else:
                stockitems.append({'stockitem':stockitem.id, 'qty':delta})

        return stockitems + list(sellitem_map.values())


class BuyItemQtyPriceSerializer(serializers.Serializer):
    buyitem = serializers.PrimaryKeyRelatedField(queryset=BuyItem.objects.all())
    qty = serializers.FloatField()
    price = serializers.FloatField(required=False)
    occasional = serializers.BooleanField(required=False)

    def validate_qty(self, value):
        if value <= 0:
            raise ValidationError("Quantity must be positive")
        return value

    def validate_price(self, value):
        if value is not None and value < 0:
            raise ValidationError("Price must be positive")
        return value

    def validate(self, data):
        if "price" in data and not "occasional" in data:
            raise ValidationError("Is this new price permanent or occasional?")
        return data


class AccountSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())

    def validate_account(self, account):
        if account.deleted:
            raise ValidationError("Account is deleted")
        if self.context['request'].bar.id != account.bar.id:
            raise serializers.ValidationError("Cannot operate across bars")
        return account


class AccountAmountSerializer(AccountSerializer):
    amount = serializers.FloatField()

    def validate_amount(self, value):
        if value < 0:
            raise ValidationError("Amount must be positive")
        return value


class AccountRatioSerializer(AccountSerializer):
    ratio = serializers.FloatField(default=1)

    def validate_ratio(self, value):
        if value <= 0:
            raise ValidationError("Ratio must be positive")
        return value



class BuyTransactionSerializer(BaseTransactionSerializer, ItemQtySerializer):
    def create(self, data):
        t = super(BuyTransactionSerializer, self).create(data)

        self.context["transaction"] = t
        money_delta = ItemQtySerializer.create(self, data)

        t.accountoperation_set.create(
            target=Account.objects.get(owner=t.author, bar=t.bar),
            delta=-money_delta)

        t.moneyflow = money_delta
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        force_fuzzy = True
        obj["items"] = ItemQtySerializer.serializeOperations(transaction.itemoperation_set.all(), force_fuzzy)

        return obj


class ThrowTransactionSerializer(BaseTransactionSerializer):
    stockitem = serializers.PrimaryKeyRelatedField(queryset=StockItem.objects.all())
    qty = serializers.FloatField()

    def validate_qty(self, value):
        if value < 0:
            raise ValidationError(ERROR_MESSAGES['negative'] % {'field':"Quantity"})
        return value

    def validate_stockitem(self, item):
        err_params = {'model':'StockItem', 'id':item.id}
        if item is not None and item.deleted:
            raise ValidationError(ERROR_MESSAGES['deleted'] % err_params)

        if item is not None and self.context['request'].bar.id != item.bar.id:
            raise ValidationError(ERROR_MESSAGES['wrong_bar'] % err_params)

        return item


    def create(self, data):
        t = super(ThrowTransactionSerializer, self).create(data)
        stockitem = data['stockitem']
        qty = data['qty']

        iop = stockitem.create_operation(delta=-qty, unit='sell', transaction=t)

        t.moneyflow = iop.delta * stockitem.get_price()
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        iop = transaction.itemoperation_set.all()[0]
        stockitem = iop.target
        obj["stockitem"] = stockitem.id
        obj["qty"] = -iop.delta * stockitem.get_unit('sell')

        return obj



class DepositTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    def create(self, data):
        t = super(DepositTransactionSerializer, self).create(data)

        t.accountoperation_set.create(
            target=data["account"],
            delta=data["amount"])
        t.accountoperation_set.create(
            target=get_default_account(t.bar),
            delta=data["amount"])

        t.moneyflow = data["amount"]
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        for aop in transaction.accountoperation_set.all():
            if aop.target.owner != get_default_user():
                obj["account"] = aop.target.id
                obj["amount"] = aop.delta

        return obj


class WithdrawTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    def create(self, data):
        t = super(WithdrawTransactionSerializer, self).create(data)

        t.accountoperation_set.create(
            target=data["account"],
            delta=-data["amount"])
        t.accountoperation_set.create(
            target=get_default_account(t.bar),
            delta=-data["amount"])

        t.moneyflow = -data["amount"]
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        for aop in transaction.accountoperation_set.all():
            if aop.target.owner != get_default_user():
                obj["account"] = aop.target.id
                obj["amount"] = -aop.delta

        return obj


class GiveTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    def validate_account(self, account):
        account = super(GiveTransactionSerializer, self).validate_account(account)

        if self.context['request'].user == account.owner:
            raise serializers.ValidationError("Cannot give money to yourself")

        return account

    def create(self, data):
        t = super(GiveTransactionSerializer, self).create(data)

        t.accountoperation_set.create(
            target=Account.objects.get(owner=t.author, bar=t.bar),
            delta=-data["amount"])
        t.accountoperation_set.create(
            target=data["account"],
            delta=data["amount"])

        t.moneyflow = data["amount"]
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        from_op = transaction.accountoperation_set.all()[0]
        to_op = transaction.accountoperation_set.all()[1]
        if to_op.target.owner == transaction.author:
            from_op, to_op = to_op, from_op
        obj["account"] = to_op.target.id
        obj["amount"] = to_op.delta

        return obj


class RefundTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    motive = serializers.CharField()

    def create(self, data):
        t = super(RefundTransactionSerializer, self).create(data)

        t.accountoperation_set.create(
            target=data["account"],
            delta=data["amount"])
        t.accountoperation_set.create(
            target=get_default_account(t.bar),
            delta=data["amount"])
        t.transactiondata_set.create(
            label='motive',
            data=data["motive"])

        t.moneyflow = data["amount"]
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        for aop in transaction.accountoperation_set.all():
            if aop.target.owner != get_default_user():
                obj["account"] = aop.target.id
                obj["amount"] = aop.delta

        data = transaction.transactiondata_set.all()[0]
        obj["motive"] = data.data

        return obj

punishment_notification_mail = {
    'from_email': "babe@binets.polytechnique.fr",
    'subject': "[Chocapix] Notification d'amende",
    'message': u"""
Salut,

{name} a infligé une amende de {amount:.2f} € à ton compte dans le bar {bar}.
La raison invoquée est la suivante :
    « {cause} »

Ce mail a été envoyé automatiquement par Chocapix.
"""
}


class PunishTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    motive = serializers.CharField()

    def create(self, data):
        t = super(PunishTransactionSerializer, self).create(data)

        operation = t.accountoperation_set.create(
            target=data["account"],
            delta=-data["amount"])
        t.transactiondata_set.create(
            label='motive',
            data=data["motive"])

        t.moneyflow = -data["amount"]
        t.save()

        ## notify the account owner
        message = punishment_notification_mail.copy()
        if t.author.email:
            message["from_email"] = t.author.email
        account = operation.target
        if account.owner.email:
            message["recipient_list"] = [account.owner.email]
            message["message"] = message["message"].format(
                name=t.author.get_full_name(),
                amount=data["amount"],
                cause=data["motive"],
                bar=account.bar.name
            )
            send_mail(**message)

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        aop = transaction.accountoperation_set.all()[0]
        obj["account"] = aop.target.id
        obj["amount"] = aop.delta

        data = transaction.transactiondata_set.all()[0]
        obj["motive"] = data.data

        return obj


agios_notification_mail = {
    'subject': "[Chocapix] Notification d'agios",
    'message': u"""
Salut,

Tu viens de payer {amount:.2f} € d'agios dans le bar {bar}.
Ton nouveau solde est {solde:.2f} €.
Pense à donner rapidement un chèque à un respo bar.

Ce mail a été envoyé automatiquement par Chocapix.
"""
}

class AgiosTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    def create(self, data):
        t = super(AgiosTransactionSerializer, self).create(data)

        operation = t.accountoperation_set.create(
            target=data["account"],
            delta=-data["amount"])

        t.moneyflow = -data["amount"]
        t.save()

        ## notify the account owner
        message = agios_notification_mail.copy()
        message["from_email"] = "babe@binets.polytechnique.fr"
        account = operation.target
        if account.owner.email:
            message["recipient_list"] = [account.owner.email]
            message["message"] = message["message"].format(
                amount=data["amount"],
                solde=account.money,
                bar=account.bar.name
            )
            send_mail(**message)

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        aop = transaction.accountoperation_set.all()[0]
        obj["account"] = aop.target.id
        obj["amount"] = -aop.delta

        return obj


class BarInvestmentTransactionSerializer(BaseTransactionSerializer):
    amount = serializers.FloatField()
    motive = serializers.CharField(allow_blank=True)

    def create(self, data):
        t = super(BarInvestmentTransactionSerializer, self).create(data)

        t.accountoperation_set.create(
            target=get_default_account(t.bar),
            delta=-data["amount"])
        t.transactiondata_set.create(
            label='motive',
            data=data["motive"])

        t.moneyflow = data["amount"]
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        aop = transaction.accountoperation_set.all()[0]
        obj["amount"] = -aop.delta

        data = transaction.transactiondata_set.all()[0]
        obj['motive'] = data.data

        return obj




class MealTransactionSerializer(BaseTransactionSerializer):
    items = ItemQtySerializer(many=True)
    accounts = AccountRatioSerializer(many=True)
    name = serializers.CharField(allow_blank=True)

    def validate(self, data):
        if "accounts" not in data or len(data["accounts"]) < 1:
            raise ValidationError("There is no account in this meal")

        if "items" not in data or len(data["items"]) < 1:
            raise ValidationError("There is no item in this meal")

        return data

    def create(self, data):
        t = super(MealTransactionSerializer, self).create(data)

        s = ItemQtySerializer()
        s.context["transaction"] = t

        total_price = 0
        for i in data["items"]:
            total_price += ItemQtySerializer.create(s, i)

        total_ratio = 0
        for a in data["accounts"]:
            total_ratio += a["ratio"]
        for a in data["accounts"]:
            t.accountoperation_set.create(
                target=a["account"],
                delta=-total_price * a["ratio"] / total_ratio)

        t.transactiondata_set.create(
            label='name',
            data=data["name"])

        t.moneyflow = total_price
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        force_fuzzy = True
        obj["items"] = ItemQtySerializer.serializeOperations(transaction.itemoperation_set.all(), force_fuzzy)

        total_price = 0
        obj["accounts"] = []
        aops = transaction.accountoperation_set.all()
        for aop in aops:
            total_price += abs(aop.delta)
        for aop in aops:
            obj["accounts"].append({
                'account': aop.target.id,
                'ratio': abs(aop.delta) / total_price if total_price != 0 else 0
            })

        data = transaction.transactiondata_set.all()[0]
        obj[data.label] = data.data

        return obj


class ApproTransactionSerializer(BaseTransactionSerializer):
    items = BuyItemQtyPriceSerializer(many=True)

    def create(self, data):
        t = super(ApproTransactionSerializer, self).create(data)

        stockitem_map = {}
        total = 0
        for i in data["items"]:
            buyitem = i["buyitem"]
            qty = i["qty"]

            priceobj, _ = BuyItemPrice.objects.get_or_create(bar=t.bar, buyitem=buyitem)
            if "price" in i:
                if not i["occasional"]:
                    priceobj.price = i["price"] / qty
                    priceobj.save()
                total += i["price"]
            else:
                total += priceobj.price * qty

            try:
                stockitem = StockItem.objects.get(bar=t.bar, details=buyitem.details)
                if stockitem.id not in stockitem_map:
                    stockitem_map[stockitem.id] = {'stockitem': stockitem, 'delta': 0}
                stockitem_map[stockitem.id]['delta'] += qty * buyitem.itemqty

                if "price" in i:
                    if stockitem.qty <= 0:
                        stockitem.price = i["price"] / (qty*buyitem.itemqty)
                    else:
                        stockitem.price = (stockitem.qty * stockitem.price + i["price"]) / (stockitem.qty + qty*buyitem.itemqty)
                    stockitem.save()
            except:
                t.delete()
                raise Http404("Stockitem does not exist")


        for x in stockitem_map.values():
            x['stockitem'].create_operation(delta=x['delta'], unit='buy', transaction=t)

        t.accountoperation_set.create(
            target=get_default_account(t.bar),
            delta=-total)

        t.moneyflow = total
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        obj["items"] = []
        for iop in transaction.itemoperation_set.all():
            obj["items"].append({
                'stockitem': iop.target.id,
                'qty': iop.delta * iop.target.get_unit('sell')
            })

        aop = transaction.accountoperation_set.all()[0]

        return obj


class InventoryTransactionSerializer(BaseTransactionSerializer):
    items = ItemQtySerializer(many=True)

    def create(self, data):
        t = super(InventoryTransactionSerializer, self).create(data)

        total_price = 0

        for i in data["items"]:
            i["stockitem"].last_inventory = timezone.now()
            i["stockitem"].save()
            iop = i["stockitem"].create_operation(next_value=i["qty"], unit='sell', transaction=t, fixed=True)
            total_price += iop.delta * iop.target.get_price()

        t.moneyflow = total_price
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        obj["items"] = []
        for iop in transaction.itemoperation_set.all():
            obj["items"].append({
                'stockitem': iop.target.id,
                'qty': iop.delta * iop.target.get_unit('sell')
            })

        return obj


class CollectivePaymentTransactionSerializer(BaseTransactionSerializer):
    accounts = AccountRatioSerializer(many=True)
    amount = serializers.FloatField()
    motive = serializers.CharField(allow_blank=True)

    def create(self, data):
        t = super(CollectivePaymentTransactionSerializer, self).create(data)

        amount = data['amount']
        total_ratio = 0
        for a in data["accounts"]:
            total_ratio += a["ratio"]
        for a in data["accounts"]:
            t.accountoperation_set.create(
                target=a["account"],
                delta=-amount * a["ratio"] / total_ratio)

        t.transactiondata_set.create(
            label='motive',
            data=data["motive"])

        t.moneyflow = amount
        t.save()

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'request':self.context.get('request'), 'ignore_type': True}).data
        if transaction is None:
            return obj

        total_price = 0
        obj["accounts"] = []
        aops = transaction.accountoperation_set.all()
        for aop in aops:
            total_price += abs(aop.delta)
        for aop in aops:
            obj["accounts"].append({
                'account': aop.target.id,
                'ratio': abs(aop.delta) / total_price
            })

        data = transaction.transactiondata_set.all()[0]
        obj['motive'] = data.data

        return obj



serializers_class_map = {
    "": BaseTransactionSerializer,
    "buy": BuyTransactionSerializer,
    "throw": ThrowTransactionSerializer,
    "deposit": DepositTransactionSerializer,
    "withdraw": WithdrawTransactionSerializer,
    "give": GiveTransactionSerializer,
    "refund": RefundTransactionSerializer,
    "punish": PunishTransactionSerializer,
    "agios": AgiosTransactionSerializer,
    "barInvestment": BarInvestmentTransactionSerializer,
    "meal": MealTransactionSerializer,
    "appro": ApproTransactionSerializer,
    "inventory": InventoryTransactionSerializer,
    "collectivePayment": CollectivePaymentTransactionSerializer}

from django.db import models
from django.db.models import Q
from django.http import Http404
from rest_framework import viewsets
from rest_framework import serializers, decorators
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework import exceptions

from bars_api.models.user import User
from bars_api.models import VirtualField
from bars_api.models.bar import Bar
from bars_api.models.item import Item
from bars_api.models.account import Account
from bars_api.perms import PerBarPermissionsOrAnonReadOnly


class Transaction(models.Model):
    class Meta:
        app_label = 'bars_api'
    bar = models.ForeignKey(Bar)
    author = models.ForeignKey(User)
    type = models.CharField(max_length=25)
    timestamp = models.DateTimeField(auto_now_add=True)
    canceled = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)
    _type = VirtualField("Transaction")

    def __unicode__(self):
        return self.type + ": " \
            + unicode(list(self.accountoperation_set.all())
                      + list(self.itemoperation_set.all())
                      + list(self.transactiondata_set.all()))

    def check_integrity(self):
        t = self.type
        iops = self.itemoperation_set.all()
        aops = self.accountoperation_set.all()
        data = self.transactiondata_set.all()

        if t in ["buy", "throw"] and len(iops) != 1:
            return False

        if t in ["throw"] and len(aops) != 0:
            return False
        if t in ["buy", "throw", "appro", "inventory"] and len(aops) != 1:
            return False
        if t in ["give", "punish"] and len(aops) != 2:
            return False

        if t in ["meal", "punish"] and len(data) != 1:
            return False

        # TODO: Check money flow, owners, signs, labels, ...
        return True



class TransactionData(models.Model):
    class Meta:
        app_label = 'bars_api'
    transaction = models.ForeignKey(Transaction)
    label = models.CharField(max_length=128)
    data = models.TextField()


class BaseOperation(models.Model):
    class Meta:
        abstract = True
    transaction = models.ForeignKey(Transaction)
    prev_value = models.FloatField()
    fixed = models.BooleanField(default=False)  # Whether the operation was a delta or a fixed value
    delta = models.FloatField()  # Fixed if not self.fixed
    next_value = models.FloatField()  # Fixed if self.fixed

    def __unicode__(self):
        if self.fixed:
            return unicode(self.target) + "=" + unicode(self.next_value)
        else:
            return unicode(self.target) + "+=" + unicode(self.delta)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.prev_value = getattr(self.target, self.op_model_field)

        if self.fixed:
            self.delta = self.next_value - self.prev_value
        else:
            self.next_value = self.prev_value + self.delta

        if not self.pk:
            self.op_model.objects.filter(pk=self.target.id).update(**{self.op_model_field: self.next_value})

        super(BaseOperation, self).save(*args, **kwargs)

    def propagate(self):
        olders_or_self = (self.__class__.objects.select_related()
                          .filter(target=self.target)
                          .filter(transaction__timestamp__gte=self.transaction.timestamp)
                          .order_by('transaction__timestamp', 'pk'))

        next_prev = None
        for op in olders_or_self:
            if next_prev is not None:
                op.prev_value = next_prev
                op.save()

            if op.transaction.canceled:
                next_prev = op.prev_value
            else:
                next_prev = op.next_value

        self.op_model.objects.filter(pk=self.target.id).update(**{self.op_model_field: next_prev})

class ItemOperation(BaseOperation):
    class Meta:
        app_label = 'bars_api'
    target = models.ForeignKey(Item)

    op_model = Item
    op_model_field = 'qty'

class AccountOperation(BaseOperation):
    class Meta:
        app_label = 'bars_api'
    target = models.ForeignKey(Account)

    op_model = Account
    op_model_field = 'money'



# ######################### Transaction Serializers ########################## #

class BaseTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        read_only_fields = ('bar', 'author', 'timestamp', 'last_modified')

    def to_representation(self, transaction):
        if 'ignore_type' in self.context or transaction.type == "":
            obj = super(BaseTransactionSerializer, self).to_representation(transaction)
            try:
                author_account = Account.objects.get(owner=transaction.author, bar=transaction.bar)
                obj["author_account"] = author_account.id
            except:
                pass
            obj['_type'] = "Transaction"

            return obj
        else:
            serializer = serializers_class_map[transaction.type](transaction)
            # serializer.is_valid(raise_exception=True)
            try:
                return serializer.data
            except:
                return

    def create(self, data):
        request = self.context['request']
        bar = request.QUERY_PARAMS.get('bar', None)
        if bar is None:
            raise Http404()
        bar = Bar.objects.get(pk=bar)
        if request.user.has_perm('bars_api.add_' + data["type"] + 'transaction', bar):
            fields = Transaction._meta.get_all_field_names()
            attrs = {k: v for k, v in data.items() if k in fields}
            t = Transaction(**attrs)
            # t.author = User.objects.all()[0]
            t.author = request.user
            t.bar = bar
            t.save()
            return t

        else:
            raise exceptions.PermissionDenied()



class ItemQtySerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    qty = serializers.FloatField()

    def validate_qty(self, value):
        if value < 0:
            raise ValidationError("Quantity must be positive")
        return value


class ItemQtyPriceSerializer(ItemQtySerializer):
    price = serializers.FloatField(required=False)

    def validate_price(self, value):
        if value is not None and value < 0:
            raise ValidationError("Price must be positive")
        return value


class AccountAmountSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    amount = serializers.FloatField()

    def validate_amount(self, value):
        if value < 0:
            raise ValidationError("Amount must be positive")
        return value


class AccountRatioSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    ratio = serializers.FloatField()

    def validate_ratio(self, value):
        if value <= 0:
            raise ValidationError("Ratio must be positive")
        return value



class BuyTransactionSerializer(BaseTransactionSerializer, ItemQtySerializer):
    def create(self, data):
        t = super(BuyTransactionSerializer, self).create(data)

        t.itemoperation_set.create(
            target=data['item'],
            delta=-data['qty'])
        t.accountoperation_set.create(
            target=Account.objects.get(owner=t.author, bar=t.bar),
            delta=-data['qty'] * data['item'].price)

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
        if transaction is None:
            return obj

        iop = transaction.itemoperation_set.all()[0]
        obj["item"] = iop.target.id
        obj["qty"] = abs(iop.delta)

        aop = transaction.accountoperation_set.all()[0]
        obj["moneyflow"] = -aop.delta

        return obj


class ThrowTransactionSerializer(BaseTransactionSerializer, ItemQtySerializer):
    def create(self, data):
        t = super(ThrowTransactionSerializer, self).create(data)

        t.itemoperation_set.create(
            target=data["item"],
            delta=-data["qty"])

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
        if transaction is None:
            return obj

        iop = transaction.itemoperation_set.all()[0]
        obj["item"] = iop.target.id
        obj["qty"] = abs(iop.delta)

        obj["moneyflow"] = iop.delta * iop.target.price

        return obj


class GiveTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    def create(self, data):
        t = super(GiveTransactionSerializer, self).create(data)

        t.accountoperation_set.create(
            target=Account.objects.get(owner=t.author, bar=t.bar),
            delta=-data["amount"])
        t.accountoperation_set.create(
            target=data["account"],
            delta=data["amount"])

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
        if transaction is None:
            return obj

        from_op = transaction.accountoperation_set.all()[0]
        to_op = transaction.accountoperation_set.all()[1]
        if to_op.target.owner == transaction.author:
            from_op, to_op = to_op, from_op
        obj["account"] = to_op.target.id
        obj["amount"] = to_op.delta

        obj["moneyflow"] = to_op.delta

        return obj


class PunishTransactionSerializer(BaseTransactionSerializer, AccountAmountSerializer):
    motive = serializers.CharField()

    def create(self, data):
        t = super(PunishTransactionSerializer, self).create(data)

        t.accountoperation_set.create(
            target=data["account"],
            delta=-data["amount"])
        t.transactiondata_set.create(
            label='motive',
            data=data["motive"])

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
        if transaction is None:
            return obj

        aop = transaction.accountoperation_set.all()[0]
        obj["account"] = aop.target.id
        obj["amount"] = aop.delta

        data = transaction.transactiondata_set.all()[0]
        obj["motive"] = data.data

        obj["moneyflow"] = aop.delta

        return obj



class MealTransactionSerializer(BaseTransactionSerializer):
    items = ItemQtySerializer(many=True)
    accounts = AccountRatioSerializer(many=True)
    name = serializers.CharField(allow_blank=True)

    def create(self, data):
        t = super(MealTransactionSerializer, self).create(data)

        total_price = 0
        for i in data["items"]:
            t.itemoperation_set.create(
                target=i["item"],
                delta=-i["qty"])
            total_price += i["qty"] * i["item"].price

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

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
        if transaction is None:
            return obj

        obj["items"] = []
        for iop in transaction.itemoperation_set.all():
            obj["items"].append({
                'item': iop.target.id,
                'qty': abs(iop.delta)
            })

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
        obj[data.label] = data.data

        obj["moneyflow"] = total_price

        return obj


class ApproTransactionSerializer(BaseTransactionSerializer):
    items = ItemQtyPriceSerializer(many=True)

    def create(self, data):
        t = super(ApproTransactionSerializer, self).create(data)

        for i in data["items"]:
            item = i["item"]
            if "price" in i:
                item.buy_price = i["price"] / i["qty"]
                item.save()

            t.itemoperation_set.create(
                target=item,
                delta=i["qty"])

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
        if transaction is None:
            return obj

        total_price = 0
        obj["items"] = []
        for iop in transaction.itemoperation_set.all():
            obj["items"].append({
                'item': iop.target.id,
                'qty': abs(iop.delta)
            })
            total_price += iop.delta * iop.target.buy_price

        obj["moneyflow"] = total_price

        return obj


class InventoryTransactionSerializer(BaseTransactionSerializer):
    items = ItemQtySerializer(many=True)

    def create(self, data):
        t = super(InventoryTransactionSerializer, self).create(data)

        for i in data["items"]:
            t.itemoperation_set.create(
                target=i["item"],
                next_value=i["qty"],
                fixed=True)

        return t

    def to_representation(self, transaction):
        obj = BaseTransactionSerializer(transaction, context={'ignore_type': True}).data
        if transaction is None:
            return obj

        total_price = 0
        obj["items"] = []
        for iop in transaction.itemoperation_set.all():
            obj["items"].append({
                'item': iop.target.id,
                'qty': iop.delta
            })
            total_price += iop.delta * iop.target.price

        obj["moneyflow"] = total_price

        return obj




serializers_class_map = {
    "": BaseTransactionSerializer,
    "buy": BuyTransactionSerializer,
    "throw": ThrowTransactionSerializer,
    "give": GiveTransactionSerializer,
    "punish": PunishTransactionSerializer,
    "meal": MealTransactionSerializer,
    "appro": ApproTransactionSerializer,
    "inventory": InventoryTransactionSerializer}

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    permission_classes = (PerBarPermissionsOrAnonReadOnly,)

    def get_serializer_class(self):
        data = self.request.data
        if "type" in data:
            return serializers_class_map[data["type"]]
        else:
            return serializers_class_map[""]

    def get_queryset(self):
        queryset = Transaction.objects.all()

        bar = self.request.QUERY_PARAMS.get('bar', None)
        if bar is not None:
            queryset = queryset.filter(bar=bar)

        user = self.request.QUERY_PARAMS.get('user', None)
        if user is not None:
            queryset = queryset.filter(
                Q(accountoperation__target__owner=user) |
                Q(author=user)
            )

        account = self.request.QUERY_PARAMS.get('account', None)
        if account is not None:
            queryset = queryset.filter(
                Q(accountoperation__target=account) |
                Q(author__account=account)
            )

        item = self.request.QUERY_PARAMS.get('item', None)
        if item is not None:
            queryset = queryset.filter(itemoperation__target=item)

        type = self.request.QUERY_PARAMS.get('type', None)
        if type is not None:
            queryset = queryset.filter(type=type)

        queryset = queryset.order_by('-timestamp')
        # queryset = queryset.order_by('-timestamp').distinct('timestamp')

        page = int(self.request.QUERY_PARAMS.get('page', 0))
        if page != 0:
            page_size = int(self.request.QUERY_PARAMS.get('page_size', 10))
            queryset = queryset[(page - 1) * page_size: page * page_size]

        return queryset


    @decorators.detail_route(methods=['put'])
    def cancel(self, request, pk=None):
        transaction = Transaction.objects.select_related().get(pk=pk)
        if request.user.has_perm('bars_api.change_transaction', transaction):
            transaction.canceled = True
            transaction.save()

            for aop in transaction.accountoperation_set.all():
                aop.propagate()

            for iop in transaction.itemoperation_set.all():
                iop.propagate()

            serializer = self.get_serializer_class()(transaction)
            return Response(serializer.data)

        else:
            raise exceptions.PermissionDenied()

    @decorators.detail_route(methods=['put'])
    def restore(self, request, pk=None):
        transaction = Transaction.objects.get(pk=pk)
        if request.user.has_perm('bars_api.change_transaction', transaction):
            transaction.canceled = False
            transaction.save()

            for aop in transaction.accountoperation_set.all():
                aop.propagate()

            for iop in transaction.itemoperation_set.all():
                iop.propagate()

            serializer = self.get_serializer_class()(transaction)
            return Response(serializer.data)

        else:
            raise exceptions.PermissionDenied()

# encoding: utf8
from django.core.mail import send_mail
from django.db import models
from bars_django.utils import VirtualField, permission_logic
from bars_core.perms import BarRolePermissionLogic
from bars_core.models.bar import Bar
from bars_core.models.user import User
from bars_items.models.stockitem import StockItem
from bars_core.models.account import Account
from bars_transactions.perms import TransactionAuthorPermissionLogic


@permission_logic(TransactionAuthorPermissionLogic(field_name='author'))
class Transaction(models.Model):
    class Meta:
        app_label = 'bars_transactions'
    bar = models.ForeignKey(Bar)
    author = models.ForeignKey(User)
    type = models.CharField(max_length=25)
    timestamp = models.DateTimeField(auto_now_add=True)
    canceled = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)
    _type = VirtualField("Transaction")
    moneyflow = models.FloatField(default=0)

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

    def compute_moneyflow(self):
        t = self.type
        iops = self.itemoperation_set.all()
        aops = self.accountoperation_set.all()
        data = self.transactiondata_set.all()

        if t in ["buy", "withdraw", "agios", "barInvestment", "appro"]:
            return -aops[0].delta

        if t == "throw":
            return iops[0].delta * iops[0].target.get_price()

        if t in ["deposit", "punish"]:
            return aops[0].delta

        if t == "give":
            from_op = transaction.aops[0]
            to_op = transaction.aops[1]
            if to_op.target.owner == self.author:
                from_op, to_op = to_op, from_op
            return to_op.delta

        if t == "refund":
            for aop in aops:
                if aop.target.owner != get_default_user():
                    return aop.delta

        if t in ["meal", "collectivePayment"]:
            m = 0
            for aop in aops:
                m += abs(aop.delta)
            return m

        if t == "inventory":
            m = 0
            for iop in iops:
                m += iop.delta * iop.target.get_price()
            return m



class TransactionData(models.Model):
    class Meta:
        app_label = 'bars_transactions'
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
        app_label = 'bars_transactions'
    target = models.ForeignKey(StockItem)
    fuzzy = models.BooleanField(default=False)

    op_model = StockItem
    op_model_field = 'qty'


switching_to_negative_notification_mail = {
    'subject': "[Chocapix] Notification de passage en négatif",
    'message': u"""
Salut,

Tu viens de payer {amount:.2f} € dans le bar {bar}, ce qui te fait passer en négatif.
Ton nouveau solde est {solde:.2f} €.
Pense à donner rapidement un chèque à un respo bar.

Ce mail a été envoyé automatiquement par Chocapix.
"""
}

class AccountOperation(BaseOperation):
    class Meta:
        app_label = 'bars_transactions'
    target = models.ForeignKey(Account)

    def save(self, *args, **kwargs):
        if ((self.target.money >= 0) and (self.target.money + self.delta < 0) and (self.target.owner != self.transaction.author) and (not self.pk)):
            ## if the transaction empties the account of the user, notify the account owner
            message = switching_to_negative_notification_mail.copy()
            if self.transaction.author.email:
                message["from_email"] = self.transaction.author.email
            else:
                message["from_email"] = "babe@binets.polytechnique.fr"
            if self.target.owner.email:
                message["recipient_list"] = [self.target.owner.email]
                message["message"] = message["message"].format(
                    amount = -self.delta,
                    solde = self.target.money + self.delta,
                    bar = self.target.bar.name
                )
                send_mail(**message)
        super(AccountOperation, self).save(*args, **kwargs)

    op_model = Account
    op_model_field = 'money'

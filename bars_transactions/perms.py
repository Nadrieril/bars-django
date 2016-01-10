from datetime import timedelta
from django.utils import timezone
from permission.logics import AuthorPermissionLogic
from bars_core.perms import debug_perm, BarRolePermissionLogic

class TransactionAuthorPermissionLogic(AuthorPermissionLogic):
    @debug_perm("Logic (transaction)")
    def has_perm(self, user, perm, obj=None):
        if not user.is_authenticated() or not user.is_active:
            return False
    
        bar_role_perm = BarRolePermissionLogic().has_perm(user, perm, obj)
        
        if obj is not None and perm == 'bars_transactions.change_transaction':
            # Nobody can cancel a punishment that he received
            if obj.type == "punish" and obj.accountoperation_set.all()[0].target.owner == user:
                return False
            # We check general bar-related permissions
            if bar_role_perm:
                return True
            # Otherwise, general rule for transaction update
            threshold = obj.bar.settings.transaction_cancel_threshold
            if timezone.now() - obj.timestamp > timedelta(hours=threshold):
                return False

        # For other cases
        return bar_role_perm or super(TransactionAuthorPermissionLogic, self).has_perm(user, perm, obj)
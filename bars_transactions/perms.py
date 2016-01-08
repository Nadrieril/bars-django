from datetime import timedelta
from django.utils import timezone
from permission.logics import AuthorPermissionLogic
from bars_core.perms import debug_perm
from bars_core.perms import BarRolePermissionLogic



class TransactionAuthorPermissionLogic(AuthorPermissionLogic):
    @debug_perm("Logic (transaction)")

        #Here we define the permissions that users need to cancel, create some transaction
        #AuthorPermissionLogic is to be sure that you can cancel the operation you are responsible for
        #We use BarRolePermissionLogic to enable or not an action according to the roles of the user

    def has_perm(self, user, perm, obj=None):
        if not user.is_authenticated() or not user.is_active:
            return False

        permission = BarRolePermissionLogic().has_perm(user, perm, obj)
        if obj is not None and perm == 'bars_transactions.change_transaction':
            threshold = obj.bar.settings.transaction_cancel_threshold
            if timezone.now() - obj.timestamp > timedelta(hours=threshold) and not permission: #Basic user that cannot cancel operation
                return False

            if permission and obj.type == "punish" and obj.accountoperation_set.all()[0].target.owner == user: #Prevent the staff to cancel punishment against him
                return False

        if not permission:
            return super(TransactionAuthorPermissionLogic, self).has_perm(user, perm, obj)
        else:
            return True

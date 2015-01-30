from django.db.models.loading import get_model
from rest_framework.permissions import DjangoObjectPermissions
from permission.utils.field_lookup import field_lookup
from permission.logics import PermissionLogic, AuthorPermissionLogic

# For reference
perms_list = [
    'bars_api.add_buytransaction',
    'bars_api.add_throwtransaction',
    'bars_api.add_givetransaction',
    'bars_api.add_punishtransaction',
    'bars_api.add_mealtransaction',
    'bars_api.add_approtransaction',
    'bars_api.add_inventorytransaction',

    # 'bars_api.add_bar',
    # 'bars_api.add_user',
    'bars_api.add_role',
    'bars_api.add_account',
    'bars_api.add_item',
    # 'bars_api.add_transaction',
    'bars_api.add_news',

    # 'bars_api.change_bar',
    # 'bars_api.change_user',
    'bars_api.change_role',
    'bars_api.change_account',
    'bars_api.change_item',
    'bars_api.change_transaction',
    'bars_api.change_news',

    # 'bars_api.delete_bar',
    # 'bars_api.delete_user',
    'bars_api.delete_role',
    'bars_api.delete_account',
    'bars_api.delete_item',
    'bars_api.delete_transaction',
    'bars_api.delete_news',
]

Role = None  # Prevent circular imports
Bar = None
def _has_perm_in_bar(user, perm, bar):
    global Role
    if Role is None:
        Role = get_model('bars_api', 'Role')

    roles = Role.objects.filter(user=user, bar=bar)
    for r in roles:
        if perm in r.get_permissions():
            return True
    return False

# ## Per-bar permissions
# Django restframework module
class PerBarPermissionsOrAnonReadOnly(DjangoObjectPermissions):
    # Already handled by BarRolePermissionLogic
    # def has_object_permission(self, request, view, obj):

    def has_permission(self, request, view):
        if request.method in ('GET', 'OPTIONS', 'HEAD'):
            return True

        global Bar
        if Bar is None:
            Bar = get_model('bars_api', 'Bar')

        bar = request.QUERY_PARAMS.get('bar', None)
        if bar is not None:
            bar = Bar.objects.get(pk=bar)
            model_cls = getattr(view, 'model', None)
            queryset = getattr(view, 'queryset', None)

            if model_cls is None and queryset is not None:
                model_cls = queryset.model

            assert model_cls, ('Cannot apply permissions on a view that'
                               ' does not have `.model` or `.queryset` property.')

            perms = self.get_required_permissions(request.method, model_cls)

            print "Rest: " + unicode(perms) + "@" + unicode(bar)
            for perm in perms:
                if request.user.has_perm(perm, bar):
                    return True

        return super(DjangoObjectPermissions, self).has_permission(request, view)


# Django model permissions
class BarPermissionBackend(object):
    def has_perm(self, user, perm, obj=None):
        global Bar
        if Bar is None:
            Bar = get_model('bars_api', 'Bar')
        if not user.is_authenticated():
            return False

        print "Backend: " + perm + "@" + unicode(obj)
        if obj is None:
            return False
        elif user.is_active and isinstance(obj, Bar):
            return _has_perm_in_bar(user, perm, obj)

        return False


# ## Per-object permissions
# Django permissions module
class BarRolePermissionLogic(PermissionLogic):
    def __init__(self, field_name=None):
        self.field_name = field_name or 'bar'

    def has_perm(self, user, perm, obj=None):
        if not user.is_authenticated():
            return False

        if obj is None:
            method = perm.split(".")[1].split("_")[0]
            return method in ('change', 'delete')
        elif user.is_active:
            bar = field_lookup(obj, self.field_name)
            if bar is None:
                return False
            return _has_perm_in_bar(user, perm, bar)

        return False


PERMISSION_LOGICS = (
    ('bars_api.Account', BarRolePermissionLogic()),
    ('bars_api.Item', BarRolePermissionLogic()),
    # ('bars_api.News', BarRolePermissionLogic()),
    ('bars_api.Role', BarRolePermissionLogic()),
    ('bars_api.Transaction', BarRolePermissionLogic()),
    ('bars_api.Transaction', AuthorPermissionLogic(field_name='author')),
)

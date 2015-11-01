from django.conf.urls import patterns, include, url
from rest_framework import routers

from django.contrib import admin
admin.autodiscover()

import permission
permission.autodiscover()

from bars_core.models.bar import BarViewSet, BarSettingsViewSet
from bars_core.models.user import UserViewSet, ResetPasswordView
from bars_core.models.role import RoleViewSet
from bars_core.models.account import AccountViewSet
from bars_core.models.loginattempt import LoginAttemptViewSet

from bars_items.models.sellitem import SellItemViewSet
from bars_items.models.stockitem import StockItemViewSet
from bars_items.models.itemdetails import ItemDetailsViewSet
from bars_items.models.buyitem import BuyItemViewSet, BuyItemPriceViewSet
from bars_items.models.suggesteditem import SuggestedItemViewSet

from bars_transactions.views import TransactionViewSet

from bars_news.models import NewsViewSet

from bars_bugtracker.models import BugReportViewSet

from bars_menus.models import MenuViewSet

router = routers.DefaultRouter()

router.register('bar', BarViewSet)
router.register('barsettings', BarSettingsViewSet)
router.register('user', UserViewSet)
router.register('role', RoleViewSet)
router.register('account', AccountViewSet)
router.register('loginattempt', LoginAttemptViewSet)

router.register('buyitem', BuyItemViewSet)
router.register('buyitemprice', BuyItemPriceViewSet)
router.register('itemdetails', ItemDetailsViewSet)
router.register('sellitem', SellItemViewSet)
router.register('stockitem', StockItemViewSet)

router.register('transaction', TransactionViewSet)

router.register('news', NewsViewSet)

router.register('bugreport', BugReportViewSet)

router.register('menu', MenuViewSet)
router.register('suggested_items',SuggestedItemViewSet)


urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^api-token-auth/', 'rest_framework_jwt.views.obtain_jwt_token'),
    url(r'^api-token-auth/', 'bars_core.auth.obtain_jwt_token'),
    url(r'^reset-password/$', ResetPasswordView.as_view()),
    url(r'^', include(router.urls)),
)

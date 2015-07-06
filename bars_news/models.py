from django.db import models
from rest_framework import serializers, viewsets, filters

from bars_django.utils import VirtualField, permission_logic, CurrentBarCreateOnlyDefault, CurrentUserCreateOnlyDefault
from bars_core.models.bar import Bar
from bars_core.models.user import User
from bars_core.perms import PerBarPermissionsOrAnonReadOnly, BarRolePermissionLogic


@permission_logic(BarRolePermissionLogic())
class News(models.Model):
    class Meta:
        app_label = 'bars_news'
    bar = models.ForeignKey(Bar)
    author = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    text = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News

    _type = VirtualField("News")
    bar = serializers.PrimaryKeyRelatedField(read_only=True, default=CurrentBarCreateOnlyDefault())
    author = serializers.PrimaryKeyRelatedField(read_only=True, default=CurrentUserCreateOnlyDefault())



class NewsFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        bars = request.query_params.getlist('bar')
        if len(bars) != 0:
            return queryset.filter(bar__in=bars)
        else:
            return queryset


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = (PerBarPermissionsOrAnonReadOnly,)
    filter_backends = (NewsFilterBackend, filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = {
        'timestamp': ['lte', 'gte'],
        'author': ['exact']}
    search_fields = ('name', 'text')

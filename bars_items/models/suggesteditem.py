from django.db import models
from rest_framework import decorators, serializers, viewsets, filters
from rest_framework.response import Response

from bars_django.utils import VirtualField, permission_logic, CurrentBarCreateOnlyDefault, CurrentUserCreateOnlyDefault
from bars_core.models.bar import Bar
from bars_core.models.user import User
from bars_core.perms import PerBarPermissions, PerBarPermissionsOrAnonReadOnly, BarRolePermissionLogic

@permission_logic(BarRolePermissionLogic())
class SuggestedItem(models.Model):
    class Meta:
        app_label = 'bars_items'
    bar = models.ForeignKey(Bar)
    name = models.CharField(max_length=100)
    voters_list = models.ManyToManyField(User)
    timestamp = models.DateTimeField(auto_now_add=True)
    already_added = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

class SuggestedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuggestedItem

    _type = VirtualField("SuggestedItem")
    bar = serializers.PrimaryKeyRelatedField(read_only=True, default=CurrentBarCreateOnlyDefault())
    voters_list = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=CurrentUserCreateOnlyDefault(), many=True)

class SuggestedItemViewSet(viewsets.ModelViewSet):
    queryset = SuggestedItem.objects.all()
    serializer_class = SuggestedItemSerializer
    permission_classes = (PerBarPermissionsOrAnonReadOnly,)
    filter_fields = {
        'timestamp': ['lte', 'gte'],
        }#'author': ['exact']
    search_fields = ('name',)
    
    @decorators.detail_route(methods=['post'])
    def vote(self, request, pk=None):
        try:
            suggesteditem = SuggestedItem.objects.get(pk=pk)
        except SuggestedItem.DoesNotExist:
            raise Http404('SuggestedItem (id=%d) does not exist' % pk)

        if request.user.is_authenticated() and request.user.is_active:
            if not request.user in suggesteditem.voters_list.all():
                suggesteditem.voters_list.add(request.user)
                suggesteditem.save()
                srz = SuggestedItemSerializer(suggesteditem)
                return Response(srz.data, 200)
            else:
                srz = SuggestedItemSerializer(suggesteditem)
                return Response(srz.data, 202)
        else:
            return Response('You are not allowed to perform this operation', 401)

    @decorators.detail_route(methods=['post'])
    def unvote(self, request, pk=None):
        try:
            suggesteditem = SuggestedItem.objects.get(pk=pk)
        except SuggestedItem.DoesNotExist:
            raise Http404('SuggestedItem (id=%d) does not exist' % pk)

        if request.user.is_authenticated() and request.user.is_active:
            if request.user in suggesteditem.voters_list.all():
                suggesteditem.voters_list.remove(request.user)
                suggesteditem.save()
                srz = SuggestedItemSerializer(suggesteditem)
                return Response(srz.data, 200)
            else:
                srz = SuggestedItemSerializer(suggesteditem)
                return Response(srz.data, 202)
        else: 
            srz = SuggestedItemSerializer(suggesteditem)
            return Response(srz.data, 401)

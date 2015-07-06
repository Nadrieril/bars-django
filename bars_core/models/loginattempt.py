from django.db import models
from rest_framework import serializers, viewsets, permissions

from bars_django.utils import VirtualField
from bars_core.models.user import User


class LoginAttempt(models.Model):
    class Meta:
        app_label = 'bars_core'
    user = models.ForeignKey(User, null=True)
    success = models.BooleanField(default=False)
    sent_username = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=15)

    def __unicode__(self):
        return "%s at %s (success=%s)" % (unicode(self.sent_username), unicode(self.timestamp), unicode(self.success))


class LoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempt

    _type = VirtualField("LoginAttempt")


class LoginAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoginAttempt.objects.all()
    serializer_class = LoginAttemptSerializer
    filter_fields = ['user', 'success']
    search_fields = ('ip',)

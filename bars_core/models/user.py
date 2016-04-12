#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import string
from django.db import models
from django.db.models import Prefetch
from django.core.mail import send_mail
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, _user_has_module_perms, _user_has_perm
from rest_framework import viewsets, serializers, decorators, exceptions, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from permission.logics import OneselfPermissionLogic
from bars_django.utils import VirtualField, permission_logic
from bars_core.perms import RootBarRolePermissionLogic
from bars_core.models.loginattempt import LoginAttempt


class UserManager(BaseUserManager):
    def get_queryset(self):
        return super(UserManager, self).get_queryset().prefetch_related(
            'role_set',
        )

    def create_user(self, username, password):
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        user = self.create_user(username, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


@permission_logic(OneselfPermissionLogic())
@permission_logic(RootBarRolePermissionLogic())
class User(AbstractBaseUser):
    class Meta:
        app_label = 'bars_core'
    username = models.CharField(max_length=128, unique=True)
    firstname = models.CharField(max_length=128, blank=True)
    lastname = models.CharField(max_length=128, blank=True)
    pseudo = models.CharField(max_length=128, blank=True)
    email = models.EmailField(max_length=254, blank=True)

    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)

    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    previous_login = models.DateTimeField(blank=True, auto_now_add=True) # to display "last connection" on frontend
    current_login = models.DateTimeField(blank=True, auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [] # TODO: require email !

    def has_perm(self, perm, obj=None):
        if self.is_active and self.is_superuser:
            return True

        return _user_has_perm(self, perm, obj)

    def has_perms(self, perm_list, obj=None):
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return "%s %s" % (self.lastname, self.firstname)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        read_only_fields = ('is_active', 'last_modified', 'previous_login', )
        exclude = ('is_staff', 'is_superuser', 'current_login', 'last_login', )
        extra_kwargs = {
            'password': { 'write_only': True, 'required':False }
        }

    _type = VirtualField("User")

    def validate(self, data):
        """Check valid email"""
        from django.core.validators import validate_email
        if 'email' not in data:
            raise serializers.ValidationError("Please give us your email")
        validate_email(data['email'])
        return data

    def create(self, data):
        u = super(UserSerializer, self).create(data)
        u.set_password(data.get('password', '0000')) # TODO: Generate random password and send email
        u.save()
        return u


from bars_core.perms import RootBarPermissionsOrObjectPermissions
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (RootBarPermissionsOrObjectPermissions,)

    @decorators.list_route()
    def me(self, request):
        """
        Return current user data.
        """
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    @decorators.list_route(methods=['put'])
    def change_password(self, request):
        """
        Change current user's password.
        ---
        parameters_strategy: replace
        parameters:
            - name: old_password
              required: true
              type: string
            - name: password
              required: true
              type: string
        """
        user = request.user

        data = request.data
        if not user.check_password(data['old_password']):
            raise exceptions.PermissionDenied()

        if data['password'] == "":
            return Response("'password' field cannot be empty", 400)

        user.set_password(data['password'])
        user.save()
        return Response('Password changed', 200)

    @decorators.detail_route()
    def stats(self, request, pk):
        """
        Return consumption stats of the given user (pk).
        Response format: [["*date*": value, ...], ...]
        ---
        omit_serializer: true
        parameters:
            - name: bar
              required: false
              type: string
              paramType: query
            - name: type
              required: false
              type: string
              description: The types of transactions to consider in stats computing (type=buy&type=meal&...)
              paramType: query
            - name: interval
              required: false
              type: string
              paramType: query
            - name: date_start
              required: false
              type: datetime
              paramType: query
            - name: date_end
              required: false
              type: datetime
              paramType: query
        """
        from bars_stats.utils import compute_transaction_stats
        f = lambda qs: qs.filter(accountoperation__target__owner=pk)
        aggregate = models.Sum('accountoperation__delta')

        stats = compute_transaction_stats(request, f, aggregate)
        return Response(stats, 200)


reset_mail = {
    'from_email': 'babe@binets.polytechnique.fr',
    'subject': 'Mot de passe Chocapix',
    'message': u"""
Salut,

Ton mot de passe Chocapix a été réinitialisé.
C'est maintenant "{password}".
Rappel: ton login est "{login}".

Cordialement,
Les membres du BABE
"""
}
class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        """
        Reset the password of the user whose email is passed in parameter.
        ---
        parameters:
            - name: email
              type: string
              required: true
        """
        email = request.data.get('email')
        if email == '':
            return Response("'email' field cannot be empty", 400)
        user = User.objects.get(email=email)

        password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))

        mail = reset_mail.copy()
        mail['recipient_list'] = [user.email]
        mail['message'] = mail['message'].format(email=user.email, password=password, name=user.get_full_name(), login=user.username)
        send_mail(**mail)

        user.set_password(password)
        user.save()

        return Response('Password reset', 200)


def get_default_user():
    """
    Default user is a fictive user, who has an account in each bar.
    It is used for comptability purposes.
    """
    if get_default_user._cache is None:
        get_default_user._cache, _ = User.objects.get_or_create(username="bar", firstname="Bar", is_active=False)
    return get_default_user._cache
get_default_user._cache = None

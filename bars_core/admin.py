# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import Group
from django import forms

from bars_core.models.user import User
from bars_core.models.bar import Bar, BarSettings
from bars_core.models.role import Role
from bars_core.models.account import Account
from bars_core.models.loginattempt import LoginAttempt

class BarForm(ActionForm):
    bar = forms.ModelChoiceField(queryset=Bar.objects.all())

class UserAdmin(admin.ModelAdmin):
    list_display   = ('username', 'firstname', 'lastname', 'email', 'pseudo')
    list_filter    = ('account__bar',)
    ordering       = ('pseudo', )
    search_fields  = ('lastname', 'firstname')
    exclude = None
    actions = ['admin', 'treso', 'respo_appro', 'respo_facho', 'respo_news', 'respo_inventaire']
    action_form = BarForm

    def admin(self, request, queryset):
        for user in queryset:
            bar = request.POST.get('bar')
            Role.objects.create(name="admin", bar=Bar.objects.get(id=bar), user=user)
            Role.objects.create(name="staff", bar=Bar.objects.get(id="root"), user=user)
    admin.short_description = "Donner les droits de respo bar"

    def treso(self, request, queryset):
        for user in queryset:
            bar = request.POST.get('bar')
            Role.objects.create(name="treasurer", bar=Bar.objects.get(id=bar), user=user)
    treso.short_description = "Donner les droits de trésorier"

    def respo_appro(self, request, queryset):
        for user in queryset:
            bar = request.POST.get('bar')
            Role.objects.create(name="appromanager", bar=Bar.objects.get(id=bar), user=user)
            Role.objects.create(name="itemcreator", bar=Bar.objects.get(id="root"), user=user)
    respo_appro.short_description = "Donner les droits de respo appro"

    def respo_facho(self, request, queryset):
        for user in queryset:
            bar = request.POST.get('bar')
            Role.objects.create(name="policeman", bar=Bar.objects.get(id=bar), user=user)
    respo_facho.short_description = "Donner les droits de respo facho"

    def respo_news(self, request, queryset):
        for user in queryset:
            bar = request.POST.get('bar')
            Role.objects.create(name="newsmanager", bar=Bar.objects.get(id=bar), user=user)
    respo_news.short_description = "Donner les droits de respo news"

    def respo_inventaire(self, request, queryset):
        for user in queryset:
            bar = request.POST.get('bar')
            Role.objects.create(name="inventorymanager", bar=Bar.objects.get(id=bar), user=user)
    respo_inventaire.short_description = "Donner les droits de respo inventaire"


class RoleAdmin(admin.ModelAdmin):
   list_display   = ('user', 'bar', 'name')
   ordering       = ('bar', 'user', 'name')
   list_filter    = ('bar', 'name', )
   search_fields  = ('user__username', 'user__firstname' )
   exclude = None

class AccountAdmin(admin.ModelAdmin):
    list_display   = ('__unicode__', 'owner', 'owner_firstname', 'owner_lastname', 'bar', 'money')
    ordering       = ('bar', )
    list_filter    = ('bar', )
    search_fields  = ('owner__lastname', 'owner__firstname', 'owner__username' )
    exclude = None

    def owner_firstname(self, obj):
        return obj.owner.firstname
    owner_firstname.short_description = 'Owner firstname'
    owner_firstname.admin_order_field = 'owner__firstname'

    def owner_lastname(self, obj):
        return obj.owner.lastname
    owner_lastname.short_description = 'Owner lastname'
    owner_lastname.admin_order_field = 'owner__lastname'

admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Bar)
admin.site.register(BarSettings)
admin.site.register(Role, RoleAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(LoginAttempt)

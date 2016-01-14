from django.contrib import admin

# Register your models here.
from ipsconnect3.models import ConnectUser
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, ReadOnlyPasswordHashField

from django.contrib.admin.sites import NotRegistered
from registration.models import RegistrationProfile
from registration.admin import RegistrationAdmin
from registration.users import UsernameField


class ConnectUserChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField(label="Password",
            help_text=("Passwords are only stored in the IPS Connect 3 master, "
                        "so there is no way to see this user's password.")
    )
    def clean_password(self):
        """
        There is no password, so we can't return any initial value
        """
        return ''


class ConnectUserAdmin(UserAdmin):
    """
    A version of UserAdmin modified to account for
    the fields on ConnectUser that differ from User
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('displayname', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_banned', 'is_staff', 'is_superuser',
            'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'id', 'displayname', 'email', 'is_staff', 'is_superuser', 'is_active', 'is_banned')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_banned', 'groups')
    search_fields = ('username', 'displayname', 'email', 'id')
    ordering = ('id',)
    
    form = ConnectUserChangeForm
    add_fieldsets = () # disable adding Users through the Admin

admin.site.register(ConnectUser, ConnectUserAdmin)


# Fix RegistrationAdmin search fields
class ConnectRegistrationAdmin(RegistrationAdmin):
    def user_id(obj):
        return obj.user.id
    user_id.admin_order_field = 'user__id'
    
    list_display = ('user', user_id, 'activation_key_expired')
    search_fields = ('user__{0}'.format(UsernameField()),
                         'user__displayname', 'user__id')

try:
    admin.site.unregister(RegistrationProfile)
except NotRegistered:
    pass
admin.site.register(RegistrationProfile, ConnectRegistrationAdmin)

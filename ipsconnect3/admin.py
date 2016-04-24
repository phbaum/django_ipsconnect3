from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

# Register your models here.
from ipsconnect3.models import ConnectUser
from ipsconnect3 import utils
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, ReadOnlyPasswordHashField

from django.contrib.admin.sites import NotRegistered
from registration import signals
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
                         
    def activate_users(self, request, queryset):
        """
        Activates the selected users if they are not already
        activated.
        Overrides the RegistrationAdmin method with an API call
        to the IPS Connect 3 master.
        """
        users_activated = 0
        for profile in queryset:
            error = ""
            result = utils.request_validate(uid=profile.user.id, ip_address=utils.get_ip_address(request))
            if result.get('status') == 'SUCCESS':
                activated_user = RegistrationProfile.objects.activate_user(profile.activation_key)
                if activated_user:
                    signals.user_activated.send(sender=self.__class__,
                                                user=activated_user,
                                                request=request)
                    users_activated += 1
                else:
                    error = "There was a problem with the Registration Profile"
                    
            elif result.get('status') == 'NO_USER':
                error = "The user was not found in the IPS Connect master database"
            elif result.get('status') == 'BAD_KEY':
                error = "The IPS Connect master key was invalid"

            if error:
                self.message_user(
                    request,
                    "Failed to activate user '{user}'. {error}.".format(
                        user=profile.user.displayname, error=error
                    ),
                    level='ERROR'
                )
                break
        if users_activated > 0:
            bit = "users were" if users_activated > 1 else "user was"
            self.message_user(request, "{num} {users} successfully activated.".format(num=users_activated, users=bit))
    activate_users.short_description = _("Activate users")
    

try:
    admin.site.unregister(RegistrationProfile)
except NotRegistered:
    pass
admin.site.register(RegistrationProfile, ConnectRegistrationAdmin)

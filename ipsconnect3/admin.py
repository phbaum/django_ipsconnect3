from django.contrib import admin

# Register your models here.
from ipsconnect3.models import ConnectUser
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

class ConnectUserAdmin(UserAdmin):
    """
    A version of UserAdmin modified to account for
    the fields on ConnectUser that differ from User
    """
    fieldsets = (
        ('Personal info', {'fields': ('username','displayname', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_banned', 'is_staff', 'is_superuser',
            'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'id', 'displayname', 'email', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'displayname', 'email')
    ordering = ('id',)
    
    add_fieldsets = () # disable adding Users through the Admin

admin.site.register(ConnectUser, ConnectUserAdmin)

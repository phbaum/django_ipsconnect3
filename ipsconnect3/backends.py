from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from ipsconnect3.models import ConnectUser
from ipsconnect3.util import request_login

class IPSConnect3Backend(object):
    """
    Authenticate against an IPS Connect 3 master
    """
    def authenticate(self, username=None, password=None):
        user = None
        uid = None
        id_type = None
        # First, try to find the user in our local database so we can pass the ID
        try:
            user = ConnectUser.objects.get(username=username)
        except ConnectUser.DoesNotExist:
            user = None
            uid = username
            id_type = 'username'
        else:
            uid = user.id
            id_type = 'id'

        result = request_login(id_type, uid, password)
        
        if result.get('connect_status') == 'SUCCESS':
            # Update or create the user in the database.
            if user is None: # Create the user.
                model = get_user_model()
                user = model.objects.create_user(
                    id=int(result['connect_id']),
                    username = result['connect_username'],
                    displayname = result['connect_displayname'],
                    email = result['connect_email'],
                )
            else: # User exists, just update the fields.
                user.username = result['connect_username']
                user.displayname = result['connect_displayname']
                user.email = result['connect_email']
                user.save()
            user.connect_login_data = result
            return user
        # if result.get('connect_status') == 'ACCOUNT_LOCKED':
        #     raise PermissionDenied()
        else:
            return None
    
    
    def register(self, name=None, password=None):
        
        return
        
    def logout(self, user_id=None):
        return
    
    
    def get_user(self, user_id):
        try:
            return ConnectUser.objects.get(pk=user_id)
        except ConnectUser.DoesNotExist:
            return None
            
    
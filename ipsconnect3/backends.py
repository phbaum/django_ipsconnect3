from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from ipsconnect3.models import ConnectUser
from ipsconnect3 import utils

class IPSConnect3Backend(object):
    """
    Authenticate against an IPS Connect 3 master
    """
    def authenticate(self, username=None, password=None):
        UserModel = get_user_model()
        user = None
        uid = None
        id_type = None
        # First, try to find the user in our local database so we can pass the ID
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            uid = username
            id_type = 'username'
        else:
            uid = user.id
            id_type = 'id'

        result = utils.request_login(id_type, uid, password)
        
        if result.get('connect_status') == 'SUCCESS':
            # Update or create the user in the database.
            user = self._create_or_update_user(
                user=user,
                uid=int(result['connect_id']),
                username=result['connect_username'], 
                displayname=result['connect_displayname'],
                email=result['connect_email'],
            )
            user.connect_login_data = result
            return user
            
        elif result.get('connect_status') == 'VALIDATING':
            user = self._create_or_update_user(
                user=user,
                uid=int(result['connect_id']),
                username=result['connect_username'], 
                displayname=result['connect_displayname'],
                email=result['connect_email'],
                validating=True,
            )
            user.connect_login_data = result
            return user
            
        elif result.get('connect_status') == 'WRONG_AUTH':
            return None
        
        elif result.get('connect_status') == 'NO_USER':
            if user is not None and settings.IPSCONNECT3_DELETE_MISSING:
                # We have the user in the local database, but it's not in the master any more
                # => Delete the user
                user.delete()
            return None
                
        elif result.get('connect_status') == 'ACCOUNT_LOCKED':
            raise PermissionDenied()
            
        else:
            return None
    
    
    def get_user(self, user_id):
        try:
            return ConnectUser.objects.get(pk=user_id)
        except ConnectUser.DoesNotExist:
            return None
            
    def _create_or_update_user(self, user=None, uid=None,
                               username=None, displayname=None,
                               email=None, validating=False):
        """
        Creates the user in the local database or updates
        the fields if a user with that id already exists.
        """
        UserModel = get_user_model()
        if user is None:
            user = UserModel.objects.create_user(
                id=uid,
                username=username,
                displayname=displayname,
                email=email,
            )
        else:
            user.username = username
            user.displayname = displayname
            user.email = email
        if validating:
            user.is_active = False
        # TODO - add validation system?
        user.save()
        return user

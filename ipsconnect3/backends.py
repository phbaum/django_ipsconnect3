from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from ipsconnect3 import utils

class IPSConnect3Backend(object):
    """
    Authenticate against an IPS Connect 3 master
    """
    DELETE_MISSING_USER = getattr(settings, 'IPSCONNECT3_DELETE_MISSING_USER', False)
    MASTER_CAN_VALIDATE = getattr(settings, 'IPSCONNECT3_MASTER_CAN_VALIDATE', True)
    
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
                validating=False,
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
            if user is not None and self.DELETE_MISSING_USER:
                # We have the user in the local database, but it's not in the master any more
                # => Delete the user
                user.delete()
            return None
                
        elif result.get('connect_status') == 'ACCOUNT_LOCKED':
            raise PermissionDenied()
            
        else:
            return None
    
    
    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
            
    def _create_or_update_user(self, user=None, uid=None,
                               username=None, displayname=None,
                               email=None, validating=True):
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
        if validating == False and self.MASTER_CAN_VALIDATE:
            user.is_active = True
        else:
            user.is_active = False
        user.save()
        return user

===========
IPSConnect3
===========

IPSConnect3 is an app that lets you authenticate against 
an InvisionPower IPS Connect 3.x master, which is used by IP.Board 3.x.

It comes with its own pluggable User model and a backend that synchronises
the data supplied by the master on every successful login.

The User model does **not** contain a password field, because it sends 
the password directly to the IPS Connect master, which authenticates the user.

Quick start
-----------

1. Add "ipsconnect3" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'ipsconnect3',
    )

2. Include the ipsconnect3 URLconf in your project urls.py like this::

    url(r'^connect/', include('ipsconnect3.urls', namespace='connect', app_name='ipsconnect3')),

3. Run `python manage.py migrate` to create the ipsconnect3 models.

4. Adjust the django.contrib.auth settings::

    AUTH_USER_MODEL = 'ipsconnect3.ConnectUser'
    AUTHENTICATION_BACKENDS = ['ipsconnect3.backends.IPSConnect3Backend']
    
5. Add the minimum IPSConnect3 settings::

    IPSCONNECT3_URL = 'http://forum.example.com/ipb/interface/ipsconnect/ipsconnect.php'
    IPSCONNECT3_KEY = '519ac............' # found in the Admin CP's Tools & Settings > Log In Management

6. Optionally add extra settings::

    LOGIN_URL = 'connect:login'
    LOGOUT_URL = 'connect:logout'
    LOGIN_REDIRECT_URL = 'main:home'
    IPSCONNECT3_MASTER_CAN_VALIDATE = True # Should the local user be validated if a user is validated in the IPS Connect master? Defaults to True
    IPSCONNECT3_DELETE_MISSING_USER = False # Should the local user be deleted if a user is missing in the IPS Connect master? Defaults to False
    IPSCONNECT3_SUCCESS_URL = 'main:home'


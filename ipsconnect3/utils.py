import base64
import hashlib
import requests
import urllib
import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect

#
# HTTP GET Requests
#

def request_base(params):
    url = settings.IPSCONNECT3_URL
    # encode params with encoding of IPS Connect master
    charset = getattr(settings, 'IPSCONNECT3_MASTER_CHARSET', 'utf-8')
    params = {k: v.encode(charset) if isinstance(v, unicode) else v for k, v in params.items()}
    response = {}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        response = r.json()
    return response        
    
def request_login(id_type, uid, password):
    password_hash = hashlib.md5(password).hexdigest()
    return request_base({
        'act':      'login',
        'id':       uid,
        'idType':   id_type,
        'password': password_hash,
    })

def request_check(username='', displayname='', email=''):
    """
    Checks with the IPS Connect master application for duplicate values
    of username, displayname and email.
    
    Note that the IPS documentation is wrong in this respect
    - If the value provided is free, the result will be True
    - If the value provided is taken, the result will be False
    - If no value was provided at all, the result is None
    """
    key = settings.IPSCONNECT3_KEY
    return request_base({
        'act':          'check',
        'key':          key,
        'username':     username,
        'displayname':  displayname,
        'email':        email,
    })

def request_register(username, displayname, email, password, revalidate_url=''):
    key = settings.IPSCONNECT3_KEY
    password_hash = hashlib.md5(password).hexdigest()
    revalidate_b64 = base64.b64encode(revalidate_url)
    return request_base({
        'act': 'register',
        'key':  key,
        'username': username,
        'displayname': displayname,
        'email': email,
        'password': password_hash,
        'revalidateurl': revalidate_b64,
    })

def request_validate(uid):
    return request_base({
        'act': 'validate',
        'key': get_user_key_hash(uid),
        'id': uid,
    })
    
def request_change(uid, username='', displayname='', email='', password=''):
    return request_base({
        'act': 'change',
        'id': uid,
        'key': get_user_key_hash(uid),
        'username': username,
        'displayname': displayname,
        'email': email,
        'password': password,
        # 'redirect': '',
        # 'redirectHash': '',
    })
    
def request_delete(uid):
    # uid was meant to be an array, but I can't get that to work
    # reliably with the IPS Connect master script
    uid_json = json.dumps(uid)
    return request_base({
        'act': 'delete',
        'id': uid,
        'key': get_user_key_hash(uid_json)
    })

#
# HTTP Redirects
#

def redirect_base(params):
    """
    Returns a HttpResponseRedirect
    """
    url = settings.IPSCONNECT3_URL
    # encode params with encoding of IPS Connect master
    charset = getattr(settings, 'IPSCONNECT3_MASTER_CHARSET', 'utf-8')
    params = {k: v.encode(charset) if isinstance(v, unicode) else v for k, v in params.items()}
    param_string = urllib.urlencode(params)
    location = "{url}?{params}".format(url=url, params=param_string)
    return HttpResponseRedirect(location)
    
def redirect_login(id_type, uid, password, redirect_url):
    password_hash = hashlib.md5(password).hexdigest()
    redirect_b64 = base64.b64encode(redirect_url)
    return redirect_base({
        'act': 'login',
        'idType': id_type,
        'id': uid,
        'password': password_hash,
        'key': get_user_key_hash(uid),
        'redirect': redirect_b64,
        'redirectHash': get_redirect_hash(redirect_b64),
        'noparams': '1',
    })
    
def redirect_logout(user_id, redirect_url):
    redirect_b64 = base64.b64encode(redirect_url)
    return redirect_base({
        'act': 'logout',
        'id': user_id,
        'key': get_user_key_hash(user_id),
        'redirect': redirect_b64,
        'redirectHash': get_redirect_hash(redirect_b64),
        'noparams': '1',
    })





def get_combined_hash(thing):
    """
    Returns an MD5 hash of the joined IPS Connect Key
    and the parameter thing
    """
    return hashlib.md5('{0}{1}'.format(settings.IPSCONNECT3_KEY, thing)).hexdigest()

def get_user_key_hash(user_id):
    return get_combined_hash(user_id)
    
def get_redirect_hash(redirect):
    return get_combined_hash(redirect)


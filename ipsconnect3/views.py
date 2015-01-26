from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from django.contrib.auth import login as _login, logout as _logout

from ipsconnect3.util import redirect_login, redirect_logout
from ipsconnect3.forms import LoginForm

# Create your views here.
def login(request, already_auth_url, success_url, login_template):
    """
    
    """
    # Send the user back to the already_auth_url if he is already authenticated
    if request.user.is_authenticated():
        return HttpResponseRedirect(already_auth_url)
    
    context = {}
    if 'next' in request.GET:
        context['next'] = request.GET['next']
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        # authentication happens during form validation
        if form.is_valid():
            # logs the user in and creates the session
            _login(request, form.user)
            id_type = 'id'
            uid = form.user.id
            password = form.cleaned_data.get('password')
            if 'next' in request.POST and request.POST['next'] != '':
                redirect_url = request.POST['next']
            else:
                redirect_url = success_url
            # redirect to the IPS Connect master
            return redirect_login(id_type, uid, password, redirect_url)
    else:
        form = LoginForm()
    
    context['form'] = form
    return render(request, login_template, context)
    
def logout(request, success_url):
    """
    """
    user_id = request.user.id
    _logout(request)
    if user_id is not None:
        return redirect_logout(user_id, success_url)
    else:
        return HttpResponseRedirect(success_url)

def register(request):
    """
    """
    pass
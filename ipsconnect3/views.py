from django.shortcuts import render, resolve_url, redirect
# from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

# Avoid shadowing the login() and logout() views below.
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model, authenticate

from ipsconnect3 import utils
from ipsconnect3.forms import LoginForm, RegistrationForm

# Create your views here.
def login(request, 
          success_url='main:home',
          template_name='main/login.html'):
    """
    doc
    """
    # Send the user back to the success_url if he is already authenticated
    if request.user.is_authenticated():
        return redirect(success_url)
    
    context = {}
    if 'next' in request.GET:
        context['next'] = request.GET['next']
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        # authentication happens during form validation
        if form.is_valid():
            # logs the user in and creates the session
            auth_login(request, form.user)
            id_type = 'id'
            uid = form.user.id
            password = form.cleaned_data.get('password')
            if 'next' in request.POST and request.POST['next'] != '':
                redirect_url = request.POST['next']
            else:
                redirect_url = success_url
            # redirect to the IPS Connect master
            redirect_url = request.build_absolute_uri(resolve_url(redirect_url))
            return utils.redirect_login(id_type, uid, password, redirect_url)
    else:
        form = LoginForm()
    
    context['form'] = form
    return render(request, template_name, context)


def logout(request, success_url='main:home'):
    """
    """
    user_id = request.user.id
    auth_logout(request)
    if user_id is not None:
        success_url = request.build_absolute_uri(resolve_url(success_url))
        return utils.redirect_logout(user_id, success_url)
    else:
        return redirect(success_url)


def register(request, template_name='main/register.html', success_url='main:home'):
    """
    View that registers the user with the IPS Connect master
    """
    context = {}
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            displayname = username
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password2')
            
            # TODO - move to function?
            # Register the user at the IPS Connect master
            result = utils.request_register(
                username=username,
                displayname=displayname,
                email=email,
                password=password,
            )
            if result.get('status') == 'SUCCESS':
                # Create the user in our database
                uid = int(result['id'])
                UserModel = get_user_model()
                user = UserModel.objects.create_user(
                    id=uid,
                    username=username,
                    displayname=displayname,
                    email=email,
                )
                
                # Also log the user in after successful registration
                authed_user = authenticate(username=username, password=password)
                auth_login(request, authed_user)
                id_type = 'id'
                success_url = request.build_absolute_uri(resolve_url(success_url))
                return utils.redirect_login(id_type, uid, password, success_url)
            elif result.get('status') == 'FAIL':
                raise Exception("Registering with the IPS Connect master failed")
            else:
                raise Exception("Unknown error during registration with the IPS Connect master")
            
            return redirect(success_url)
        else:
            pass
    else:
        form = RegistrationForm()
    
    context['form'] = form
    return render(request, template_name, context)

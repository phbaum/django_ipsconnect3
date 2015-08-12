from django.conf import settings
# Avoid shadowing the login() and logout() views below.
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model, authenticate, REDIRECT_FIELD_NAME
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
# from django.http import HttpResponseRedirect
from django.shortcuts import render, resolve_url, redirect
from django.views.generic.edit import FormView

from registration import signals
from registration.models import RegistrationProfile
from registration.views import RegistrationView as BaseRegistrationView
from registration.views import ActivationView as BaseActivationView

from ipsconnect3 import utils
from ipsconnect3.forms import LoginForm, RegistrationForm, ReactivationForm


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


def logout(request, success_url=settings.IPSCONNECT3_SUCCESS_URL):
    """
    """
    user_id = request.user.id
    auth_logout(request)
    if user_id is not None:
        success_url = request.build_absolute_uri(resolve_url(success_url))
        return utils.redirect_logout(user_id, success_url)
    else:
        return redirect(success_url)
    
        
        
class LoginView(FormView):
    """
    
    """
    form_class = LoginForm
    template_name = 'registration/login.html'
    success_url = settings.IPSCONNECT3_LOGIN_SUCCESS_URL
    
    def form_valid(self, form):
        request = self.request
        # logs the user in and creates the session
        auth_login(request, form.user)
        id_type = 'id'
        uid = form.user.id
        password = form.cleaned_data.get('password')
        
        # TODO: smarter redirect logic
        if 'next' in request.POST and request.POST['next'] != '':
            redirect_url = request.POST['next']
        else:
            redirect_url = self.success_url
            
        # redirect to the IPS Connect master
        redirect_url = request.build_absolute_uri(resolve_url(redirect_url))
        return utils.redirect_login(id_type, uid, password, redirect_url)


class RegistrationView(BaseRegistrationView):
    """
    
    """
    form_class = RegistrationForm
    SEND_ACTIVATION_EMAIL = True
    template_name='registration/registration_form.html'
    success_url = 'ipsconnect3:registration_complete'
    revalidate_url = 'ipsconnect3:registration_reactivate'
    
    def register(self, request, form):
        """
        """
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
            revalidate_url=request.build_absolute_uri(resolve_url(self.revalidate_url))
        )
        if result.get('status') == 'SUCCESS':
            # Create the user in our database
            uid = int(result['id'])
            UserModel = get_user_model()
            new_user_instance = UserModel.objects.create_user(
                id=uid,
                username=username,
                displayname=displayname,
                email=email,
            )
            
            # Django Sites logic
            if Site._meta.installed:
                site = Site.objects.get_current()
            else:
                site = RequestSite(request)
                     
            new_user = RegistrationProfile.objects.create_inactive_user(
                new_user=new_user_instance,
                site=site,
                send_email=self.SEND_ACTIVATION_EMAIL,
                request=request,
            )
            signals.user_registered.send(sender=self.__class__,
                                         user=new_user,
                                         request=request)
            return new_user
            
        elif result.get('status') == 'FAIL':
            raise Exception("Registering with the IPS Connect master failed")
        else:
            raise Exception("Unknown error during registration with the IPS Connect master")
        return None
        

class ActivationView(BaseActivationView):
    """
    """
    success_url = 'ipsconnect3:registration_activation_complete'
    
    def activate(self, request, activation_key):
        """
        Given an an activation key, look up and activate the user
        account corresponding to that key (if possible).

        After successful activation, the signal
        ``registration.signals.user_activated`` will be sent, with the
        newly activated ``User`` as the keyword argument ``user`` and
        the class of this backend as the sender.

        """
        activated_user = RegistrationProfile.objects.activate_user(activation_key)
        if activated_user:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated_user,
                                        request=request)
            
            result = utils.request_validate(uid=activated_user.id)
            if result.get('status') == 'SUCCESS':
                return activated_user
            elif result.get('status') == 'NO_USER':
                raise Exception("User to activate not found in the IPS Connect master database")
            elif result.get('status') == 'BAD_KEY':
                raise Exception("Invalid IPS Connect master key")
        return None

    def get_success_url(self, request, user):
        return self.success_url
    

class ReactivationView(FormView):
    """
    
    """
    form_class = ReactivationForm
    http_method_names = ['get', 'post']
    template_name = 'registration/reactivate.html'
    success_url = 'ipsconnect3:registration_reactivation_complete'
        
    def form_valid(self, form):
        user = form.user
        request = self.request
        # Django Sites logic
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        
        # Delete existing registration profile for this user
        try:
            registration_profile = RegistrationProfile.objects.get(user=user)
        except RegistrationProfile.DoesNotExist:
            pass
        else:
            registration_profile.delete()
        
        registration_profile = RegistrationProfile.objects.create_profile(user)
        registration_profile.send_activation_email(site, request)
        
        success_url = self.get_success_url(request, user)
        try:
            to, args, kwargs = success_url
            return redirect(to, *args, **kwargs)
        except ValueError:
            return redirect(success_url)
            
    def get_success_url(self, request, user): 
        return self.success_url
            

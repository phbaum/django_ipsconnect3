from django.conf import settings
# Avoid shadowing the login() and logout() views below.
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model, authenticate, REDIRECT_FIELD_NAME
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
# from django.http import HttpResponseRedirect
from django.shortcuts import render, resolve_url, redirect
from django.utils.http import is_safe_url
from django.views.generic.edit import FormView

from registration import signals
from registration.models import RegistrationProfile
from registration.views import RegistrationView as BaseRegistrationView
from registration.views import ActivationView as BaseActivationView

from ipsconnect3 import utils
from ipsconnect3.forms import LoginForm, RegistrationForm, ReactivationForm


# Create your views here.
class LoginView(FormView):
    """
    
    """
    form_class = LoginForm
    template_name = 'registration/login.html'
    success_url = settings.LOGIN_REDIRECT_URL
    redirect_field_name = REDIRECT_FIELD_NAME
    current_app = None
    
    _redirect_to = ''
    
    def form_valid(self, form):
        # logs the user in and creates the session
        auth_login(self.request, form.user)
        id_type = 'id'
        uid = form.user.id
        password = form.cleaned_data.get('password')
            
        # redirect to the IPS Connect master
        redirect_url = self.request.build_absolute_uri(resolve_url(self._redirect_to))
        return utils.redirect_login(id_type, uid, password, redirect_url)
        
    def dispatch(self, request, *args, **kwargs):
        """
        Handle the redirect for both GET and POST
        """
        if request.method == 'POST':
            self._redirect_to = request.POST.get(self.redirect_field_name, '')
        else:
            self._redirect_to = request.GET.get(self.redirect_field_name, '')
        if not is_safe_url(url=self._redirect_to, host=request.get_host()):
            self._redirect_to = resolve_url(self.success_url)
        return super(LoginView, self).dispatch(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context[self.redirect_field_name] = self._redirect_to
        return context


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


class RegistrationView(BaseRegistrationView):
    """
    
    """
    form_class = RegistrationForm
    SEND_ACTIVATION_EMAIL = True
    template_name='registration/registration_form.html'
    success_url = 'ipsconnect3:registration_complete'
    revalidate_url = 'ipsconnect3:registration_reactivate'
    
    def register(self, form):
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
            revalidate_url=self.request.build_absolute_uri(resolve_url(self.revalidate_url)),
            ip_address=utils.get_ip_address(self.request)
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
            site = get_current_site(self.request)
                     
            new_user = RegistrationProfile.objects.create_inactive_user(
                new_user=new_user_instance,
                site=site,
                send_email=self.SEND_ACTIVATION_EMAIL,
                request=self.request,
            )
            signals.user_registered.send(sender=self.__class__,
                                         user=new_user,
                                         request=self.request)
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
    
    def activate(self, activation_key):
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
                                        request=self.request)
            
            result = utils.request_validate(uid=activated_user.id, ip_address=utils.get_ip_address(self.request))
            if result.get('status') == 'SUCCESS':
                return activated_user
            elif result.get('status') == 'NO_USER':
                raise Exception("User to activate not found in the IPS Connect master database")
            elif result.get('status') == 'BAD_KEY':
                raise Exception("Invalid IPS Connect master key")
        return None

    def get_success_url(self, user):
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
        # Django Sites logic
        site = get_current_site(self.request)
        
        # Delete existing registration profile for this user
        try:
            registration_profile = RegistrationProfile.objects.get(user=user)
        except RegistrationProfile.DoesNotExist:
            pass
        else:
            registration_profile.delete()
        
        registration_profile = RegistrationProfile.objects.create_profile(user)
        registration_profile.send_activation_email(site, self.request)
        
        success_url = self.get_success_url(user)
        try:
            to, args, kwargs = success_url
            return redirect(to, *args, **kwargs)
        except ValueError:
            return redirect(success_url)
            
    def get_success_url(self, user): 
        return self.success_url
            

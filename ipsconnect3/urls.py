from django.conf.urls import patterns, url
from django.conf import settings
from django.views.generic.base import TemplateView

from ipsconnect3 import views

success_url = settings.IPSCONNECT3_SUCCESS_URL

urlpatterns = patterns('',
    # url(r'^login/$', views.login, {'success_url':success_url, 'template_name':'registration/login.html',}, name='login'),
    url(r'^login/$', 
        views.LoginView.as_view(), 
        name='login'),
    url(r'^logout/$', 
        views.logout, {'success_url': success_url,}, 
        name='logout'),
    
    url(r'^register/$', 
        views.RegistrationView.as_view(), 
        name='register'),
    url(r'^register/complete/$', 
        TemplateView.as_view(template_name='registration/registration_complete.html'), 
        name='registration_complete'),
    url(r'^register/closed/$', 
        TemplateView.as_view(template_name='registration/registration_closed.html'), 
        name='registration_disallowed'),
    url(r'^activate/complete/$', 
        TemplateView.as_view(template_name='registration/activation_complete.html'), 
        name='registration_activation_complete'),
    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
    # that way it can return a sensible "invalid key" message instead of a
    # confusing 404.
    url(r'^activate/(?P<activation_key>\w+)/$', 
        views.ActivationView.as_view(), 
        name='registration_activate'),
    
    url(r'^reactivate/$', 
        views.ReactivationView.as_view(), 
        name='registration_reactivate'),
    url(r'^reactivate/complete/$', 
        TemplateView.as_view(template_name='registration/reactivation_complete.html'), 
        name='registration_reactivation_complete'),
)

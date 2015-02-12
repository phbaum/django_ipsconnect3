from django.conf.urls import patterns, url
from django.conf import settings

from ipsconnect3 import views

success_url = settings.IPSCONNECT3_SUCCESS_URL

urlpatterns = patterns('',
    url(r'^login/$', views.login, {'success_url':success_url, 'template_name':'main/login.html',}, name='login'),
    url(r'^logout/$', views.logout, {'success_url': success_url,}, name='logout'),
    url(r'^register/$', views.register, {'success_url': success_url, 'template_name': 'main/register.html', }, name='register'),
)

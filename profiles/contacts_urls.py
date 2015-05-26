from django.conf.urls import patterns, url

from profiles import views

urlpatterns = patterns('',
    url(r'^$', views.contacts_list, name='contacts_list'),
    url(r'export/$', views.contacts_export, name='contacts_export'),
)

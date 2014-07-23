from django.conf.urls import patterns, url

from profiles import views, AJAX

urlpatterns = patterns('',
    url(r'^$', views.profile_form, name='profile_form'),
    url(r'list/$', views.contacts_list, name='profile_list'),
    url(r'steward/$', views.steward_forms, name='steward_forms'),
    url(r'actions/edit/$', AJAX.profile_edit, name='profile_edit'),
    url(r'actions/create/$', AJAX.user_create, name='user_create'),
    url(r'export/$', views.contacts_export, name='export'),
)

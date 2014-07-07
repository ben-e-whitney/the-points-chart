from django.conf.urls import patterns, url

from profiles import views

urlpatterns = patterns('',
    url(r'list/$', views.contacts_list, name='profile_list'),
    url(r'steward/$', views.steward_forms, name='steward_forms'),
    url(r'actions/edit/$', views.profile_edit, name='profile_edit'),
    url(r'export/$', views.contacts_export, name='export'),
)

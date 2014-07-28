from django.conf.urls import patterns, url

from steward import views, AJAX
import profiles.AJAX

urlpatterns = patterns('',
    url(r'^$', views.steward_forms, name='steward_forms'),
    url(r'actions/create/user/$', AJAX.user_create, name='user_create'),
    url(r'actions/edit/group_profile/$', profiles.AJAX.group_profile_edit,
        name='group_profile_create'),
)

from django.conf.urls import patterns, url

from steward import views
from steward.forms import UserFormCreator
from profiles.forms import GroupProfileForm

urlpatterns = patterns(
    '',
    url(r'^overview/$', views.users_stats_summarize, name='overview'),
    url(r'^creating/$', views.steward_creating_forms, name='creating'),
    url(r'^editing/$', views.steward_editing_forms, name='editing'),
    url(r'actions/create/user/$', lambda request:
        UserFormCreator(request).create_from_request(request),
        name='user_create'),
    url(r'actions/edit/user/$', lambda request:
        UserFormCreator(request).edit_from_request(request),
        name='user_edit'),
    url(r'actions/edit/group_profile/$', GroupProfileForm.edit_from_request,
        name='group_profile_edit'),
)

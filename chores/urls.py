from django.conf.urls import patterns, url

from chores import views
from chores import AJAX
from chores.forms import ChoreSkeletonForm, ChoreFormCreator

urlpatterns = patterns('',
    url(r'^$', views.chores_list, name='chores_list'),
    # This needs to come after all other patterns with only one slash.
    url(r'^actions/fetch/updates/$', AJAX.updates_fetch,
        name='chore_updates_fetch'),
    url(r'^actions/fetch/chores/$', AJAX.chores_fetch, name='chores_fetch'),
    url(r'^actions/create/chore_skeleton/$',
        ChoreSkeletonForm.create_from_request, name='chore_skeleton_create'),
    url(r'^actions/edit/chore_skeleton/$', ChoreSkeletonForm.edit_from_request,
        name='chore_skeleton_edit'),
    url(r'^actions/create/chore/$', lambda request:
        ChoreFormCreator(request).create_from_request(request),
        name='chore_create'),
    url(r'^actions/edit/chore/$', lambda request:
        ChoreFormCreator(request).edit_from_request(request),
        name='chore_edit'),
    url(r'^actions/$', AJAX.act, name='action'),
    url(r'^calendars/(?P<username>.+?)/$', views.calendar_create,
        name='calendar_create'),
    url(r'^(?P<username>[a-zA-Z0-9_@+.-]+?)/$', views.user_stats_list,
        name='user_stats_list'),
)

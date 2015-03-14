from django.conf.urls import patterns, url

from chores import views
from chores import AJAX

urlpatterns = patterns('',
    url(r'^$', views.chores_list, name='chores_list'),
    # This needs to come after all other patterns with only one slash.
    url(r'^actions/fetch/updates/$', AJAX.updates_fetch,
        name='chore_updates_fetch'),
    url(r'^actions/fetch/chores/$', AJAX.chores_fetch, name='chores_fetch'),
    url(r'^actions/create/chore_skeleton/$', AJAX.chore_skeleton_create,
        name='chore_skeleton_create'),
    url(r'^actions/edit/chore_skeleton/$', AJAX.chore_skeleton_edit,
        name='chore_skeleton_edit'),
    url(r'^actions/create/chore/$', AJAX.chore_create, name='chore_create'),
    url(r'^actions/edit/chore/$', AJAX.chore_edit, name='chore_edit'),
    url(r'^actions/$', AJAX.act, name='action'),
    url(r'^calendars/(?P<username>.+?)/$', views.calendar_create,
        name='calendar_create'),
    url(r'^(?P<username>[a-zA-Z0-9_@+.-]+?)/$', views.user_stats_list,
        name='user_stats_list'),
)

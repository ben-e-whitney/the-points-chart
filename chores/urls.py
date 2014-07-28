from django.conf.urls import patterns, url

from chores import views
from chores import AJAX

urlpatterns = patterns('',
    url(r'^$', views.chores_list, name='chores_list'),
    url(r'^summary/$', views.users_stats_summarize,
        name='users_stats_summarize'),
    # This needs to come after all other patterns with only one slash.
    url(r'^(?P<username>[a-zA-Z0-9_@+.-]+?)/$', views.user_stats_list,
        name='user_stats_list'),
    url(r'^actions/create/chore_skeleton/$', AJAX.chore_skeleton_create,
        name='chore_skeleton_create'),
    url(r'^actions/edit/chore_skeleton/$', AJAX.chore_skeleton_edit,
        name='chore_skeleton_edit'),
    url(r'^actions/create/chore/$', AJAX.chore_create,
        name='chore_create'),
    # This needs to come after all other named actions (or better yet, we
    # should fix this system).
    url(r'^actions/(?P<method_name>[a-z_]+?)/(?P<chore_id>[0-9]+)/$', AJAX.act,
        name='action'),
    url(r'^calendars/(?P<username>.+?)/$', views.calendar_create,
        name='calendar_create'),
)

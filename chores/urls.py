from django.conf.urls import patterns, url

from chores import views
from chores import AJAX

urlpatterns = patterns('',
    # url(r'^$', views.index, name='index'),
    # url(r'^(?P<coop_short_name>.+?)/chores/$', views.all_chores,
        # name='all_chores'),
    url(r'^$', views.all_users, name='all_users'),
    url(r'^(?P<username>[a-zA-Z0-9_@+.-]+?)/$' , views.one_user ,
        name='one_user'),
    url(r'^actions/(?P<method_name>[a-z_]+?)/(?P<chore_id>[0-9]+)/$', AJAX.act,
        name='action'),
    # url(r'^sign_up/(?P<chore_id>.+?)/$',  AJAX.sign_up,  name='sign_up'),
    # url(r'^sign_off/(?P<chore_id>.+?)/$', AJAX.sign_off, name='sign_off'),
    # url(r'^void/(?P<chore_id>.+?)/$',     AJAX.void,     name='void'),
    # url(r'^revert_sign_up/(?P<chore_id>.+?)/$',  AJAX.revert_sign_up,
        # name='sign_up'),
    # url(r'^revert_sign_off/(?P<chore_id>.+?)/$', AJAX.revert_sign_off,
        # name='sign_off'),
    # url(r'^revert_void/(?P<chore_id>.+?)/$',     AJAX.revert_void,
        # name='void'),
    url(r'^calendars/(?P<username>.+?)/$', views.create_calendar,
        name='create_calendar'),
)

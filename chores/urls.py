from django.conf.urls import patterns, url

from chores import views
from chores import AJAX

urlpatterns = patterns('', url(r'^$', views.index, name='index'),
    # TODO: not allow just anything as a coop_short_name? Maybe the error
    # handling is better done in the view function, though.
    # url(r'^(?P<coop_short_name>.+?)/chores/$', views.all_chores,
        # name='all_chores'),
    url(r'^all/$', views.all_users, name='all_users'),
    url(r'^(?P<username>[a-zA-Z0-9_@+.-]+?)/$' , views.one_user ,
        name='one_user'),
    url(r'^sign_up/(?P<chore_id>.+?)/$',  AJAX.sign_up,  name='sign_up'),
    url(r'^sign_off/(?P<chore_id>.+?)/$', AJAX.sign_off, name='sign_off'),
    url(r'^calendars/(?P<username>.+?)/$', views.create_calendar,
        name='create_calendar'),
)

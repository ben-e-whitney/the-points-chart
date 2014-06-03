from django.conf.urls import patterns, url

from chores import views

urlpatterns = patterns('', url(r'^$', views.index, name='index'),
    # TODO: not allow just anything as a coop_short_name? Maybe the error
    # handling is better done in the view function, though.
    # url(r'^(?P<coop_short_name>.+?)/chores/$', views.all_chores,
        # name='all_chores'),
    url(r'^all/$', views.all, name='all'),
    url(r'^me/$' , views.me , name='me'),
    url(r'^sign_up/(?P<instance_id>.+?)/$',  views.sign_up,  name='sign_up'),
    url(r'^sign_off/(?P<instance_id>.+?)/$', views.sign_off, name='sign_off'),
    url(r'^calendars/(?P<username>.+?)/$', views.create_calendar,
        name='create_calendar'),
)

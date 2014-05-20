from django.conf.urls import patterns, url

from coops import views

urlpatterns = patterns('', url(r'^$', views.index, name='index'),
    # TODO: not allow just anything as a coop_short_name? Maybe the error
    # handling is better done in the view function, though.
    url(r'^(?P<coop_short_name>.+?)/chores/$', views.all_chores,
        name='all_chores'),
)

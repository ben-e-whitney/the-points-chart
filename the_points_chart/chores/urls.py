from django.conf.urls import patterns, url

from chores import views

urlpatterns = patterns('', url(r'^$', views.index, name='index'),
   url(r'^(?P<chore_id>\d+)/description/$', views.description,
       name='description'))

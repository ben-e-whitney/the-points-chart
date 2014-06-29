from django.conf.urls import patterns, url

from profiles import views

urlpatterns = patterns('', url(r'^$', views.profile_form, name='profile_form'),
                       url(r'actions/edit/$', views.profile_edit,
                           name='profile_edit'),
                       url(r'export/$', views.export, name='export'),
)

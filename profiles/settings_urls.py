from django.conf.urls import patterns, url

from profiles import views, AJAX

urlpatterns = patterns('',
    url(r'^$', views.user_profile_form, name='user_profile_form'),
    url(r'actions/edit/profile/$', AJAX.user_profile_edit,
        name='user_profile_edit'),
)

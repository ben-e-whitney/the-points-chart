from django.conf.urls import patterns, url

from profiles import views
from profiles.forms import UserProfileForm

urlpatterns = patterns('',
    url(r'^$', views.user_profile_form, name='user_profile_form'),
    url(r'actions/edit/profile/$', UserProfileForm.edit_from_request,
        name='user_profile_edit'),
)

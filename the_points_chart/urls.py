from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='/chores/')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^chores/', include('chores.urls')),
    url(r'^steward/', include('steward.urls')),
    url(r'^stewardships/', include('stewardships.urls')),
    url(r'^settings/', include('profiles.settings_urls')),
    url(r'^contacts/', include('profiles.contacts_urls')),
    url(r'^login/', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/', 'django.contrib.auth.views.logout',
        {'next_page': '/login/'}, name='logout'),
    url(r'^about/', 'utilities.views.about', name='about'),
)

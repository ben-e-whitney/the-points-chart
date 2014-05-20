from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'the_points_chart.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    # url(r'^chores/', include('chores.urls')),
    url(r'^coops/', include('coops.urls')),
    url(r'^login/', 'django.contrib.auth.views.login',
        name='login'),
)

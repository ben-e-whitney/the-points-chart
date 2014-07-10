from django.conf.urls import patterns, url

from stewardships import AJAX

urlpatterns = patterns('',
    url(r'^actions/create/classical_stewardship_skeleton/$',
        AJAX.classical_stewardship_skeleton_create,
        name='classical_stewardship_form_create'),
    url(r'^actions/create/classical_stewardship/$',
        AJAX.classical_stewardship_create,
        name='classical_stewardship_create'),
    url(r'^actions/create/special_points/$',
        AJAX.special_points_create, name='special_points_create'),
    url(r'^actions/create/loan/$',
        AJAX.loan_create, name='loan_create'),
    url(r'^actions/create/absence/$',
        AJAX.absence_create, name='absence_create'),
    url(r'^actions/create/share_change/$',
        AJAX.share_change_create, name='share_change_create'),
)

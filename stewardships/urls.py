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
    url(r'^actions/edit/classical_stewardship_skeleton/$',
        AJAX.classical_stewardship_skeleton_edit,
        name='classical_stewardship_form_edit'),
    url(r'^actions/edit/classical_stewardship/$',
        AJAX.classical_stewardship_edit,
        name='classical_stewardship_edit'),
    url(r'^actions/edit/special_points/$',
        AJAX.special_points_edit, name='special_points_edit'),
    url(r'^actions/edit/loan/$',
        AJAX.loan_edit, name='loan_edit'),
    url(r'^actions/edit/absence/$',
        AJAX.absence_edit, name='absence_edit'),
    url(r'^actions/edit/share_change/$',
        AJAX.share_change_edit, name='share_change_edit'),
)
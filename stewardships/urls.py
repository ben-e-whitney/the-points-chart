from django.conf.urls import patterns, url

from stewardships.forms import (ClassicalStewardshipSkeletonForm,
    ClassicalStewardshipFormCreator, SpecialPointsFormCreator, LoanFormCreator,
    AbsenceFormCreator, ShareChangeFormCreator)

urlpatterns = patterns(
    '',
    url(r'^actions/create/classical_stewardship_skeleton/$',
        ClassicalStewardshipSkeletonForm.create_from_request,
        name='classical_stewardship_form_create'),
    url(r'^actions/create/classical_stewardship/$', lambda request:
        ClassicalStewardshipFormCreator(request).create_from_request(request),
        name='classical_stewardship_create'),
    url(r'^actions/create/special_points/$', lambda request:
        SpecialPointsFormCreator(request).create_from_request(request),
        name='special_points_create'),
    url(r'^actions/create/loan/$', lambda request:
        LoanFormCreator(request).create_from_request(request),
        name='loan_create'),
    url(r'^actions/create/absence/$', lambda request:
        AbsenceFormCreator(request).create_from_request(request),
        name='absence_create'),
    url(r'^actions/create/share_change/$', lambda request:
        ShareChangeFormCreator(request).create_from_request(request),
        name='share_change_create'),
    url(r'^actions/edit/classical_stewardship_skeleton/$',
        ClassicalStewardshipSkeletonForm.edit_from_request,
        name='classical_stewardship_form_edit'),
    url(r'^actions/edit/classical_stewardship/$', lambda request:
        ClassicalStewardshipFormCreator(request).edit_from_request(request),
        name='classical_stewardship_edit'),
    url(r'^actions/edit/special_points/$', lambda request:
        SpecialPointsFormCreator(request).edit_from_request(request),
        name='special_points_edit'),
    url(r'^actions/edit/loan/$', lambda request:
        LoanFormCreator(request).edit_from_request(request),
        name='loan_edit'),
    url(r'^actions/edit/absence/$', lambda request:
        AbsenceFormCreator(request).edit_from_request(request),
        name='absence_edit'),
    url(r'^actions/edit/share_change/$', lambda request:
        ShareChangeFormCreator(request).edit_from_request(request),
        name='share_change_edit'),
)

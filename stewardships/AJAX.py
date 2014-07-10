from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

import json
import pytz
import datetime
from profiles.AJAX import make_form_response
from stewardships.models import StewardshipSkeleton, BenefitChangeSkeleton
from stewardships.forms import (ClassicalStewardshipSkeletonForm,
    ClassicalStewardshipFormCreator, SpecialPointsFormCreator, LoanFormCreator,
    AbsenceFormCreator, ShareChangeFormCreator)
from chores.models import Signature
# from stewardships.views import get_chore_sentences, calculate_balance


# TODO: another permissions test here, and for the rest. And require logins for
# all of these! Many access `request.user.profile.coop`.
@login_required()
def classical_stewardship_skeleton_create(request):
    form = ClassicalStewardshipSkeletonForm(request.POST)
    if form.is_valid():
        # TODO: could these be set when the form is first made?
        skeleton = form.save(commit=False)
        skeleton.coop = request.user.profile.coop
        skeleton.category = StewardshipSkeleton.STEWARDSHIP
        skeleton.save()
    return make_form_response(form)

def classical_stewardship_create(request):
    form = ClassicalStewardshipFormCreator(request.user.profile.coop)(
        request.POST)
    if form.is_valid():
        stewardship = form.save(commit=False)
        signed_up = Signature()
        signed_up.sign(User.objects.get(pk=form.data['cooper']))
        stewardship.signed_up = signed_up
        for signature in ('signed_off', 'voided'):
            sig = Signature()
            sig.save()
            setattr(stewardship, signature, sig)
        stewardship.save()
    return make_form_response(form)

# TODO: get rid of this once the functions are set.
# BenefitChangeSkeleton needs what Skeleton needs: `coop`, `short_name`,
    # `short_description`.
# StewardshipSkeleton needs `category` and `point_value`.
# Timecard needs `start_date`, `stop_date`, `signed_up`, `signed_off`, and
    # `voided`.

def loan_create(request):
    coop = request.user.profile.coop
    form = LoanFormCreator(coop)(request.POST)
    if form.is_valid():
        skeleton = StewardshipSkeleton(
            coop=request.user.profile.coop,
            category=StewardshipSkeleton.LOAN,
            short_name='Loan',
            point_value=form.data['point_value'],
            short_description=form.data['short_description']
        )
        skeleton.save()
        loan = form.save(commit=False)
        loan.skeleton = skeleton
        signed_up = Signature()
        signed_up.sign(User.objects.get(pk=form.data['cooper']))
        loan.signed_up = signed_up
        for signature in ('signed_off', 'voided'):
            sig = Signature()
            sig.save()
            setattr(loan, signature, sig)
        loan.start_date, loan.stop_date = coop.profile.get_cycle_endpoints(
            # TODO: find where the data is stored as an integer.
            int(form.cleaned_data.get('cycle'))
        )
        loan.save()
    return make_form_response(form)

def special_points_create(request):
    form = SpecialPointsFormCreator(request.user.profile.coop)(request.POST)
    if form.is_valid():
        skeleton = StewardshipSkeleton(
            coop=request.user.profile.coop,
            category=StewardshipSkeleton.SPECIAL_POINTS,
            short_name='Special Points',
            point_value=form.data['point_value'],
            short_description=form.data['short_description']
        )
        skeleton.save()
        special_points = form.save(commit=False)
        special_points.skeleton = skeleton
        signed_up = Signature()
        signed_up.sign(User.objects.get(pk=form.data['cooper']))
        special_points.signed_up = signed_up
        for signature in ('signed_off', 'voided'):
            sig = Signature()
            sig.save()
            setattr(special_points, signature, sig)
        special_points.stop_date = special_points.start_date
        special_points.save()
    return make_form_response(form)

def absence_create(request):
    form = AbsenceFormCreator(request.user.profile.coop)(request.POST)
    if form.is_valid():
        # First create the skeleton, and then the actual absence.
        skeleton = BenefitChangeSkeleton(
            coop=request.user.profile.coop,
            short_name='Absence',
            short_description=form.data['short_description']
        )
        skeleton.save()
        absence = form.save(commit=False)
        absence.skeleton = skeleton
        # TODO: make this into a function.
        signed_up = Signature()
        signed_up.sign(User.objects.get(pk=form.data['cooper']))
        absence.signed_up = signed_up
        for signature in ('signed_off', 'voided'):
            sig = Signature()
            sig.save()
            setattr(absence, signature, sig)
        print('about to save')
        absence.save()
    return make_form_response(form)

def share_change_create(request):
    coop = request.user.profile.coop
    form = ShareChangeFormCreator(coop)(request.POST)
    if form.is_valid():
        # First create the skeleton, and then the actual absence.
        skeleton = BenefitChangeSkeleton(
            coop=request.user.profile.coop,
            short_name='Share Change',
            short_description=form.data['short_description']
        )
        skeleton.save()
        share_change = form.save(commit=False)
        share_change.skeleton = skeleton
        # TODO: make this into a function.
        signed_up = Signature()
        signed_up.sign(User.objects.get(pk=form.data['cooper']))
        share_change.signed_up = signed_up
        for signature in ('signed_off', 'voided'):
            sig = Signature()
            sig.save()
            setattr(share_change, signature, sig)
        share_change.start_date, share_change.stop_date = (
            coop.profile.get_cycle_endpoints(
                int(form.cleaned_data.get('cycle'))
            )
        )
        share_change.save()
    return make_form_response(form)

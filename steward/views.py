from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms

import decimal
import itertools

from chores.models import ChoreSkeleton, Chore
from stewardships.models import (StewardshipSkeleton, Stewardship, ShareChange,
    Absence)

from profiles.forms import GroupProfileForm
from chores.forms import ChoreSkeletonForm, ChoreFormCreator
from stewardships.forms import (ClassicalStewardshipSkeletonForm,
    ClassicalStewardshipFormCreator, SpecialPointsFormCreator,
    AbsenceFormCreator, LoanFormCreator, ShareChangeFormCreator)
from steward.forms import UserFormCreator, ChoiceFormCreator

from utilities.views import DisplayInformation, format_balance
from chores.views import calculate_load_info

# TODO: include also lists of all stewardships, absences, etc.
def users_stats_summarize(request, coop=None):
    if coop is None:
        coop = request.user.profile.coop
    cycles = [{
        'cycle_num'  : cycle_num,
        'cycle_start': cycle_start,
        'cycle_stop' : cycle_stop
    } for cycle_num, cycle_start, cycle_stop in coop.profile.cycles()]
    accounts = calculate_load_info(coop=coop)
    accounts.sort(key=lambda x: x['user'].profile.nickname)
    # TODO: could move around to iterate through only once.
    # TODO: `users` is used in a pretty hacky way in the template.
    users = [row['user'] for row in accounts]
    user_ids = [row['user'].id for row in accounts]
    accounts = {
        row['user'].id: [
            format_balance(load=cycle_load, balance=cycle_balance)
            for cycle_load, cycle_balance in zip(row['load'], row['balance'])
        ]
        for row in accounts
    }

    display_info = DisplayInformation('rows', {'sections': [None],
        'subsections': [users]}, user_ids, lambda x: x, None)
    return {
        'point_cycles': cycles,
        'rows': display_info.create_template_data(accounts)
    }

@login_required()
@user_passes_test(lambda user: user.profile.points_steward)
def steward_forms(request):
    coop = request.user.profile.coop
    #TODO: could pull out common action for these two. Seems like overkill.
    HTML_create_form = lambda html_id, name, main_form, choice_objects: {
        'html_id': '{html_id}_create_form'.format(html_id=html_id),
        'title': 'Create a New {nam}'.format(nam=name),
        'main_form': main_form
    }
    #TODO: change to 'Edit or Delete a {nam}' once you get deleting working.
    HTML_edit_form = lambda html_id, name, main_form, choice_objects: {
        'html_id': '{html_id}_edit_form'.format(html_id=html_id),
        'title': 'Edit a {nam}'.format(nam=name),
        'main_form': main_form,
        'selector_form': ChoiceFormCreator(choice_objects)
    }
    credit_and_edit_args = (
        ('chore_skeleton', 'Chore Skeleton', ChoreSkeletonForm(),
             ChoreSkeleton.objects.for_coop(coop)),
        ('chore', 'Chore', ChoreFormCreator(request)(),
             Chore.objects.for_coop(coop)),
        ('classical_stewardship_skeleton', 'Stewardship Skeleton',
             ClassicalStewardshipSkeletonForm(),
             StewardshipSkeleton.objects.all().classical().for_coop(coop)),
        ('classical_stewardship', 'Stewardship',
             ClassicalStewardshipFormCreator(request)(),
             Stewardship.objects.all().classical().for_coop(coop)),
        ('special_points', 'Special Points Grant',
             SpecialPointsFormCreator(request)(),
             Stewardship.objects.all().special_points().for_coop(coop)),
        ('loan', 'Loan', LoanFormCreator(request)(),
             Stewardship.objects.all().loan().for_coop(coop)),
        ('absence', 'Absence', AbsenceFormCreator(request)(),
             Absence.objects.for_coop(coop)),
        ('share_change', 'Share Change', ShareChangeFormCreator(request)(),
             ShareChange.objects.for_coop(coop)),
        ('user', 'User', UserFormCreator(request)(), coop.user_set.all()),
    )
    create_only_args = ()
    edit_only_args = (
        ('group_profile', 'Group Profile', GroupProfileForm(),
         (coop.profile,)),
    )
    create_forms = [HTML_create_form(*args) for args in itertools.chain(
        credit_and_edit_args, create_only_args)]
    edit_forms = [HTML_edit_form(*args) for args in itertools.chain(
        credit_and_edit_args, edit_only_args)]
    render_dictionary = {'create_forms': create_forms,
                         'edit_forms': edit_forms}
    render_dictionary.update(users_stats_summarize(request, coop=coop))
    return render(request, 'steward/steward_forms.html', render_dictionary)


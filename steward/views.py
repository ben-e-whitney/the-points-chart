from django.db import connection, reset_queries

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

from utilities.views import TableElement, TableParent, format_balance
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
    accounts.sort(key=lambda row: row['user'].username)
    accounts = [{
        'username': row['user'].username,
        'formatted_balances': [
            format_balance(load=cycle_load, balance=cycle_balance)
            for cycle_load, cycle_balance in zip(row['load'], row['balance'])
        ],
    } for row in accounts]
    max_width = max(*[len(balance['formatted_value']) for row in accounts
                      for balance in row['formatted_balances']])
    def element_maker(balance):
        value = balance['formatted_value']
        content = '{sgn}{pad}{val}'.format(sgn=value[0],
            pad='0'*(max_width-len(value)), val=value[1:])
        return TableElement(title=balance['html_title'],
            CSS_classes=balance['CSS_class'], content=content)
    balance_sections = (TableParent(children=[
        TableParent(title=row['username'], children=[
            element_maker(balance) for balance in row['formatted_balances']
        ])
        for row in accounts
    ]),)
    return {
        'point_cycles': cycles,
        'balance_sections': balance_sections,
    }

@login_required()
@user_passes_test(lambda user: user.profile.points_steward)
def steward_forms(request):

    reset_queries()

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
             ChoreSkeleton.objects.for_coop(coop).prefetch_related()),
        ('chore', 'Chore', ChoreFormCreator(request)(),
             Chore.objects.for_coop(coop).prefetch_related('skeleton',
                'signed_up__who__profile', 'signed_off__who__profile',
                'voided__who__profile')),
        ('classical_stewardship_skeleton', 'Stewardship Skeleton',
             ClassicalStewardshipSkeletonForm(), (StewardshipSkeleton.objects
                .all().classical().for_coop(coop))),
        ('classical_stewardship', 'Stewardship',
             ClassicalStewardshipFormCreator(request)(), (Stewardship.objects
                .all().classical().for_coop(coop)
                .prefetch_related('skeleton'))),
        ('special_points', 'Special Points Grant',
             SpecialPointsFormCreator(request)(),
             (Stewardship.objects.all().special_points().for_coop(coop)
                .prefetch_related('signed_up__who__profile'))),
        ('loan', 'Loan', LoanFormCreator(request)(), (Stewardship.objects
            .all().loan().for_coop(coop)
            .prefetch_related('signed_up__who__profile'))),
        ('absence', 'Absence', AbsenceFormCreator(request)(),
             Absence.objects.for_coop(coop)
             .prefetch_related('signed_up__who__profile')),
        ('share_change', 'Share Change', ShareChangeFormCreator(request)(),
             ShareChange.objects.for_coop(coop).prefetch_related(
                 'signed_up__who__profile')),
        ('user', 'User', UserFormCreator(request)(),
             coop.user_set.all().prefetch_related('profile')),
    )
    create_only_args = ()
    edit_only_args = (
        ('group_profile', 'Group Profile', GroupProfileForm(),
         (coop.profile,)),
    )
    create_forms = [HTML_create_form(*args) for args in itertools.chain(
        credit_and_edit_args, create_only_args)]
    print('total after making create_forms: {lcn}'.format(
        lcn=len(connection.queries)))
    edit_forms = [HTML_edit_form(*args) for args in itertools.chain(
        credit_and_edit_args, edit_only_args)]
    print('total after making edit_forms: {lcn}'.format(
        lcn=len(connection.queries)))
    render_dictionary = {'create_forms': create_forms,
                         'edit_forms': edit_forms}
    render_dictionary.update(users_stats_summarize(request, coop=coop))
    print('total after calling users_stats_summarize: {lcn}'.format(
        lcn=len(connection.queries)))
    return render(request, 'steward/steward_forms.html', render_dictionary)

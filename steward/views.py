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

class HTMLForm:
    def __init__(self, **kwargs):
        #TODO: rename the form fields here (and in the view).
        self.name = kwargs.get('name')
        self.html_name = self.name.replace(' ', '')
        self.main_form = kwargs.get('form')()
        self.create_title = 'Create a New {nam}'.format(nam=self.name)
        self.edit_title = 'Edit a {nam}'.format(nam=self.name)
        if 'choices' in kwargs.keys():
            self.selector_form = ChoiceFormCreator(kwargs.get(
                'choices'))

def make_forms(request):
    coop = request.user.profile.coop
    return (
        HTMLForm(name='Chore Skeleton', form=ChoreSkeletonForm,
                 choices=(ChoreSkeleton.objects.for_coop(coop)
                          .prefetch_related())),
        HTMLForm(name='Chore', form=ChoreFormCreator(request),
                 choices=Chore.objects.for_coop(coop).prefetch_related(
                     'skeleton', 'signed_up__who__profile',
                     'signed_off__who__profile', 'voided__who__profile')),
        HTMLForm(name='Stewardship Skeleton',
                 form=ClassicalStewardshipSkeletonForm,
                 choices=(StewardshipSkeleton.objects.all().classical()
                          .for_coop(coop))),
        HTMLForm(name='Stewardship',
                 form=ClassicalStewardshipFormCreator(request),
                 choices=(Stewardship.objects.all().classical().for_coop(coop)
                          .prefetch_related('skeleton'))),
        HTMLForm(name='Special Points Grant',
                 form=SpecialPointsFormCreator(request),
                 choices=(Stewardship.objects.all().special_points()
                          .for_coop(coop)
                          .prefetch_related('signed_up__who__profile'))),
        HTMLForm(name='Loan', form=LoanFormCreator(request),
                 choices=(Stewardship.objects.all().loan().for_coop(coop)
                          .prefetch_related('signed_up__who__profile'))),
        HTMLForm(name='Absence', form=AbsenceFormCreator(request),
                 choices=(Absence.objects.for_coop(coop)
                          .prefetch_related('signed_up__who__profile'))),
        HTMLForm(name='Share Change', form=ShareChangeFormCreator(request),
                 choices=ShareChange.objects.for_coop(coop).prefetch_related(
                     'signed_up__who__profile')),
        HTMLForm(name='User', form=UserFormCreator(request),
                 choices=coop.user_set.all().prefetch_related('profile')),
        HTMLForm(name='Group Profile', form=GroupProfileForm,
                 choices=(coop.profile,)),
    )

# TODO: include also lists of all stewardships, absences, etc.
@login_required()
@user_passes_test(lambda user: user.profile.points_steward)
def users_stats_summarize(request):
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
    return render(request, 'steward/overview.html', {
        'point_cycles': cycles,
        'balance_sections': balance_sections,
    })
@login_required()
@user_passes_test(lambda user: user.profile.points_steward)
def steward_creating_forms(request):
    return render(request, 'steward/creating_forms.html',
                  {'forms': (form for form in make_forms(request)
                             if form.name != 'Group Profile')})

@login_required()
@user_passes_test(lambda user: user.profile.points_steward)
def steward_editing_forms(request):
    return render(request, 'steward/editing_forms.html',
                  {'forms': make_forms(request)})

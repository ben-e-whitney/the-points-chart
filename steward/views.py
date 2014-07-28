from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django import forms

# Create your views here.

from chores.models import ChoreSkeleton

from profiles.forms import GroupProfileForm
from chores.forms import ChoreSkeletonForm, ChoreForm
from stewardships.forms import (ClassicalStewardshipSkeletonForm,
    ClassicalStewardshipFormCreator, SpecialPointsFormCreator,
    AbsenceFormCreator, LoanFormCreator, ShareChangeFormCreator)
from steward.forms import UserFormCreator, ChoiceFormCreator

# TODO: put steward test here.
@login_required()
def steward_forms(request):
    coop = request.user.profile.coop
    HTML_create_form = lambda html_id, title, main_form: {
        'html_id': '{html_id}_create_form'.format(html_id=html_id),
        'title': title, 'main_form': main_form
    }
    HTML_edit_form = lambda html_id, title, main_form, choice_objects: {
        'html_id': '{html_id}_edit_form'.format(html_id=html_id),
        'title': title, 'main_form': main_form,
        'selector_form': ChoiceFormCreator(choice_objects)
    }
    create_forms = [HTML_create_form(*args) for args in (
        ('chore_skeleton', 'Create a New Chore Skeleton', ChoreSkeletonForm()),
        ('chore', 'Create a New Chore', ChoreForm()),
        ('classical_stewardship_skeleton', 'Create a New '
                 'Stewardship Skeleton', ClassicalStewardshipSkeletonForm()),
        ('classical_stewardship', 'Create a New Stewardship',
                 ClassicalStewardshipFormCreator(request)),
        # TODO: rename this to 'Special Points Grant'?
        ('special_points', 'Create a New Special Points',
                 SpecialPointsFormCreator(request)),
        ('absence', 'Create a New Absence', AbsenceFormCreator(request)),
        ('loan', 'Create a New Loan', LoanFormCreator(request)),
        ('share_change', 'Create a New Share Change',
                 ShareChangeFormCreator(request)),
        ('user', 'Create a New User', UserFormCreator(request)),
    )]
    edit_forms = [HTML_edit_form(*args) for args in (
        ('chore_skeleton', 'Edit or Delete a Chore Skeleton',
             ChoreSkeletonForm(), ChoreSkeleton.objects.for_coop(coop)),
    )]
    no_choice_edit_forms = [
        HTML_create_form('group_profile_edit_form', 'Edit the Co-op Profile',
                         GroupProfileForm(instance=coop.profile)),
    ]
    return render(request, 'steward/steward_forms.html',
                  {'create_forms': create_forms, 'edit_forms': edit_forms,
                   'no_choice_edit_forms': no_choice_edit_forms})

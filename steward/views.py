from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django import forms

# Create your views here.

from chores.models import ChoreSkeleton, Chore
from stewardships.models import (StewardshipSkeleton, Stewardship, ShareChange,
    Absence)

from profiles.forms import GroupProfileForm
from chores.forms import ChoreSkeletonForm, ChoreFormCreator
from stewardships.forms import (ClassicalStewardshipSkeletonForm,
    ClassicalStewardshipFormCreator, SpecialPointsFormCreator,
    AbsenceFormCreator, LoanFormCreator, ShareChangeFormCreator)
from steward.forms import UserFormCreator, ChoiceFormCreator

# TODO: put steward test here.
@login_required()
def steward_forms(request):
    coop = request.user.profile.coop
    #TODO: could pull out common action for these two. Seems like overkill.
    HTML_create_form = lambda html_id, name, main_form, choice_objects: {
        'html_id': '{html_id}_create_form'.format(html_id=html_id),
        'title': 'Create a New {nam}'.format(nam=name), 'main_form': main_form
    }
    HTML_edit_form = lambda html_id, name, main_form, choice_objects: {
        'html_id': '{html_id}_edit_form'.format(html_id=html_id),
        'title': 'Edit or Delete a {nam}'.format(nam=name),
        'main_form': main_form,
        'selector_form': ChoiceFormCreator(choice_objects)
    }
    #TODO: making it so that all the classes get called. Making a note in case
    #you run into problems.
    credit_and_edit_args = (
        ('chore_skeleton', 'Chore Skeleton', ChoreSkeletonForm(),
             ChoreSkeleton.objects.for_coop(coop)),
        ('chore', 'Chore', ChoreFormCreator(request)(),
             Chore.objects.for_coop(coop)),
        #TODO: don't think the `classical` call is working. Update: changed
        #something (adding `all` call).
        ('classical_stewardship_skeleton', 'Stewardship Skeleton',
             ClassicalStewardshipSkeletonForm(),
             StewardshipSkeleton.objects.all().classical().for_coop(coop)),
        ('classical_stewardship', 'Stewardship',
             ClassicalStewardshipFormCreator(request)(),
             Stewardship.objects.all().classical().for_coop(coop)),
        # TODO: rename this to 'Special Points Grant'?
        ('special_points', 'Special Points',
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
    create_only_args = (

    )
    edit_only_args = (
        ('chore_skeleton', 'Edit or Delete a Chore Skeleton',
             ChoreSkeletonForm(), ChoreSkeleton.objects.for_coop(coop)),
    )
    #TODO: Can't use the exact same thing as above. Make HTML_edit_only_form or
    #whatever.
    no_choice_edit_forms = []
    #no_choice_edit_forms = [
        #HTML_create_form('group_profile_edit_form', 'Edit the Co-op Profile',
                         #GroupProfileForm(instance=coop.profile)),
    #]

    create_forms = [HTML_create_form(*args) for args in credit_and_edit_args]
    edit_forms = [HTML_edit_form(*args) for args in credit_and_edit_args]
    edit_forms = []
    return render(request, 'steward/steward_forms.html',
                  {'create_forms': create_forms, 'edit_forms': edit_forms,
                   'no_choice_edit_forms': no_choice_edit_forms})

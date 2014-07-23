from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.template import loader, Context

import datetime
import json

from profiles.forms import UserProfileForm, UserFormCreator
from chores.forms import ChoreSkeletonForm, ChoreForm
from stewardships.forms import (ClassicalStewardshipSkeletonForm,
    ClassicalStewardshipFormCreator, SpecialPointsFormCreator, LoanFormCreator,
    AbsenceFormCreator, ShareChangeFormCreator)

from profiles.models import UserProfile, GroupProfile

@login_required()
def contacts_list(request):
    coop = request.user.profile.coop
    coopers = coop.user_set.all().order_by('profile__first_name')
    # TODO: consider putting stewardship or any other info here. Consider also
    # any highlighting of self, presidents, etc.
    # contacts = sorted(map(lambda x: x.profile, coopers), key=lambda y:
                      # y.first_name)
    return render(request, 'profiles/contacts.html',
                  dictionary={'coop': coop, 'coopers': coopers})

# TODO: try getting it exported as a PDF.
@login_required()
def contacts_export(request):
    coop = request.user.get_profile().coop
    coopers = coop.user_set.all()
    contacts = sorted(map(lambda x: x.get_profile(), coopers), key=lambda y:
                      y.first_name)
    contacts.remove(request.user.get_profile())
    # Here we are assuming that the site is using the UTC timezone.
    # TODO: check if this works as you are expecting.
    current_time = datetime.datetime.now().isoformat()\
        .replace('-', '').replace(':', '')+'Z'
    response = HttpResponse(content_type='text/vcard')
    response['Content-Disposition'] = ('attachment; '
        'filename="{sho}_contacts.vcf"'.format(
            sho=coop.profile.short_name.replace(' ', '_')))
    template = loader.get_template('profiles/contacts.vcf')
    # TODO: this seems to be working fine. Return to it when you better
    # understand when to use RequestContext.
    context = Context({'coop': coop, 'contacts': contacts,
                       'current_time': current_time})
    response.write(template.render(context))
    return response

@login_required()
def profile_form(request):
    return render(request, 'profiles/profile_form.html',
                  {'form': UserProfileForm(instance=request.user.profile)})
# TODO: what is the idiomatic way to do this? Better as a lambda expression?
class HTMLForm():
    def __init__(self, html_id, title, form_content):
        self.html_id = html_id
        self.title = title
        self.form_content = form_content

# TODO: put steward test here.
@login_required()
def steward_forms(request):
    HTML_form = lambda html_id, title, form_content: {'html_id': html_id,
        'title': title, 'form_content': form_content}
    coop = request.user.profile.coop
    forms = [HTML_form(*args) for args in (
        ('chore_skeleton_form', 'Create a New Chore Skeleton',
                 ChoreSkeletonForm()),
        ('chore_form', 'Create a New Chore', ChoreForm()),
        ('classical_stewardship_skeleton_form', 'Create a New '
                 'Stewardship Skeleton', ClassicalStewardshipSkeletonForm()),
        ('classical_stewardship_form', 'Create a New Stewardship',
                 ClassicalStewardshipFormCreator(coop)),
        # TODO: rename this to 'Special Points Grant'?
        ('special_points_form', 'Create a New Special Points',
                 SpecialPointsFormCreator(coop)),
        ('absence_form', 'Create a New Absence', AbsenceFormCreator(coop)),
        ('loan_form', 'Create a New Loan', LoanFormCreator(coop)),
        ('share_change_form', 'Create a New Share Change',
                 ShareChangeFormCreator(coop)),
        ('user_form', 'Create a New User', UserFormCreator(coop))
    )]
    return render(request, 'profiles/steward_forms.html', {'forms': forms})

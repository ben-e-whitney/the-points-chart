from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json

from utilities.AJAX import make_form_response
from profiles.forms import UserProfileForm, GroupProfileForm

#TODO: figure out what needs to be changed so that these are done in the same
#way as the other forms.
@login_required()
def profile_edit(request):
    # TODO: remove.
    form = UserProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
    return make_form_response(form)

@login_required()
def group_profile_edit(request):
    print('in group_profile_edit')
    try:
        form = GroupProfileForm(request.POST,
                                instance=request.user.profile.coop.profile)
    except Exception as e:
        print('error in making form')
        print(e)
        raise e
    if form.is_valid():
        print('form is valid')
        form.save()
    else:
        print('form is not valid')
    return make_form_response(form)


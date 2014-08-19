from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json

from utilities.AJAX import make_form_response, edit_function_creator
from profiles.models import UserProfile, GroupProfile
from profiles.forms import UserProfileForm, GroupProfileForm

user_profile_edit = edit_function_creator(
    model=UserProfile,
    model_form=UserProfileForm,
    get_id=lambda request: request.user.profile.id,
)

#TODO: figure out what needs to be changed so that this is done in the same
#way as the other forms.
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


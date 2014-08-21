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

group_profile_edit = edit_function_creator(
    model=GroupProfile,
    model_form=GroupProfileForm
)

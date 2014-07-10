from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json

from profiles.forms import UserProfileForm

# TODO: this should be stored in some site-wide directory.
def make_form_response(form):
    # TODO: remove.
    # print(form.errors)
    # print(form.non_field_errors())
    return HttpResponse(json.dumps({
        'errors': {
            field: ' '.join(form.errors[field]) for field in form.errors
        },
        'non_field_errors': list(form.non_field_errors())
    }), status=200 if form.is_valid() else 400)

@login_required()
def profile_edit(request):
    # TODO: remove.
    # print(request)
    form = UserProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
    return make_form_response(form)

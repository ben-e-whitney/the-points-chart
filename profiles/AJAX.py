from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json

from profiles.forms import UserProfileForm, GroupProfileForm

# TODO: this should be stored in some site-wide directory.
def make_form_response(form):
    # TODO: remove all this.
    print('***in make_form_response***')
    print(form.errors)
    print(form.non_field_errors())
    print({
        'errors': {
            field: ' '.join(form.errors[field]) for field in form.errors if
            field != '__all__'
        },
    })

    try:
        x = HttpResponse(json.dumps({
            'errors': {
                field: ' '.join(form.errors[field]) for field in form.errors if
                field != '__all__'
            },
            'non_field_errors': list(form.non_field_errors())
        }), status=200 if form.is_valid() else 400)
    except Exception as e:
        print('error trying to make the HttpResponse')
        print(e)
        raise e
    return HttpResponse(json.dumps({
        #TODO: there should be a better way of doing this.
        'errors': {
            field: ' '.join(form.errors[field]) for field in form.errors if
            field != '__all__'
        },
        'non_field_errors': list(form.non_field_errors())
    }), status=200 if form.is_valid() else 400)

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


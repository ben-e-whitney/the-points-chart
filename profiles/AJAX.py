from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json

from profiles.models import UserProfile
from profiles.forms import UserProfileForm, UserFormCreator

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
def user_create(request):
    print('***in user_create***')
    coop = request.user.profile.coop
    form = UserFormCreator(coop)(request.POST)
    if form.is_valid():
        print('form is valid')
        new_user = form.save()
        coop.user_set.add(new_user)
        try:
            profile = UserProfile(user=new_user, coop=coop,
                                  nickname=form.cleaned_data['nickname'],
                                  email_address=form.cleaned_data['email_address'],
                                  presence=form.cleaned_data['presence'],
                                  share=form.cleaned_data['share']
            )
            profile.save()
        except Exception as e:
            print('error in making the profile')
            print(e)
            raise e
        # TODO: email new user here with instructions. CC steward (maybe just
        # CC the person who made the request, to allow for other people to
        # create users in the future).
    else:
        print('form is not valid')
        print(form.errors)
    return make_form_response(form)

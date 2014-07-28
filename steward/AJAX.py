from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from profiles.AJAX import make_form_response
from steward.forms import UserFormCreator
from chores.AJAX import create_function_creator, edit_function_creator

@login_required()
def user_create(request):
    print('***in user_create***')
    coop = request.user.profile.coop
    form = UserFormCreator(coop)(request.POST)
    if form.is_valid():
        print('form is valid')
        try:
            # The field clean method (or something) checks that the username
            # isn't already taken.
            new_user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                email=None
            )
            coop.user_set.add(new_user)
        except Exception as e:
            print('error in making the user')
            print(e)
            raise e
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

user_create = create_function_creator(
    model=User,
    model_form_callable=UserFormCreator
)

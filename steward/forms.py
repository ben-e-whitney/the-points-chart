from django import forms
from django.contrib.auth.models import User
from django.db.models.fields import BLANK_CHOICE_DASH

from chores.forms import BasicForm
from profiles.models import UserProfile

def ChoiceFormCreator(choices):
    class ChoiceForm(forms.Form):
        choice = forms.ChoiceField(choices=BLANK_CHOICE_DASH+list(
            (choice.id, choice.__str__()) for choice in choices))
        class Meta:
            fields = ['choice']
    return ChoiceForm

def UserFormCreator(request):
    coop = request.user.profile.coop
    class UserForm(BasicForm):
        nickname = forms.CharField(max_length=2**6)
        share = forms.FloatField(initial=1, min_value=0)
        # TODO: should this allow floats (and same with the model)?
        presence = forms.IntegerField(initial=coop.profile.cycle_length,
                                      min_value=1)
        # TODO: email them once their account has been created.
        email_address = forms.EmailField()

        class Meta:
            model = User
            fields = ['username', 'password', 'nickname', 'share', 'presence']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['username'].help_text = None


        def create_object(self, request=None):
            coop = request.user.profile.coop
            try:
                # The field clean method (or something) checks that the username
                # isn't already taken.
                new_user = User.objects.create_user(
                    username=self.cleaned_data['username'],
                    password=self.cleaned_data['password'],
                    email=None
                )
                coop.user_set.add(new_user)
            except Exception as e:
                print('error in making the user')
                print(e)
                raise e
            try:
                profile = UserProfile(user=new_user, coop=coop,
                                      nickname=self.cleaned_data['nickname'],
                                      email_address=self.cleaned_data['email_address'],
                                      presence=self.cleaned_data['presence'],
                                      share=self.cleaned_data['share']
                )
                profile.save()
            except Exception as e:
                print('error in making the profile')
                print(e)
                raise e
            # TODO: email new user here with instructions. CC steward (maybe just
            # CC the person who made the request, to allow for other people to
            # create users in the future).
            return self

    return UserForm

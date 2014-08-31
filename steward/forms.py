from django import forms
from django.contrib.auth.models import User
from django.db.models.fields import BLANK_CHOICE_DASH

from utilities.forms import BasicForm
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
        email_address = forms.EmailField()

        class Meta:
            model = User
            fields = ['username', 'nickname', 'share', 'presence']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            #TODO: this we need. What about the rest?
            self.fields['username'].help_text = None
            if 'instance' in kwargs.keys():
                kwargs['instance'].password = None
                for field_name in ('email_address', 'nickname', 'share',
                                   'presence'):
                    self.fields[field_name].initial = getattr(
                        kwargs['instance'].profile, field_name)

        def save(self, commit=True, request=None, **kwargs):
            # The field clean method (or something) checks that the username
            # isn't already taken.
            new_user = super().save(commit=False)
            new_user.set_password(self.cleaned_data['username'])
            new_user.email = self.cleaned_data['email_address']
            coop = request.user.profile.coop
            try:
                profile = new_user.profile
                profile_already_there = True
            except UserProfile.DoesNotExist:
                profile = UserProfile(
                    user=new_user,
                    coop=coop,
                    public_calendar=True,
                    points_steward=False,
                    birthday=None,
                )
                profile_already_there = False
            profile.nickname      = self.cleaned_data['nickname']
            profile.email_address = self.cleaned_data['email_address']
            profile.presence      = self.cleaned_data['presence']
            profile.share         = self.cleaned_data['share']
            #TODO: this could result in orphaned profiles if `save` is called
            #with `commit` equal to `False` and the returned `new_user` isn't
            #later saved.
            #TODO: using `profile_already_there` to try to avoid this. Bad.
            if profile_already_there:
                #This gets run when editing.
                profile.save()
            else:
                #This gets run when creating.
                pass
            #TODO: Unsure this is consistent with how other forms use `commit`.
            if commit:
                #Avoid saving twice.
                if not profile_already_there:
                    profile.save()
                new_user.save()
                if not profile_already_there:
                    #TODO: can this be done before the profile is saved (and
                    #before `new_user` is saved)?
                    profile.user = new_user
                    profile.save()
                coop.user_set.add(new_user)
            # TODO: email new user here with instructions. CC steward (maybe
            # just CC the person who made the request, to allow for other
            # people to create users in the future).
            return new_user

    return UserForm

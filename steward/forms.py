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
            fields = ['username', 'nickname', 'share', 'presence']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            #TODO: this we need. What about the rest?
            self.fields['username'].help_text = None
            if 'instance' in kwargs.keys():
                #TODO: password is going to need doing. Ugh.
                kwargs['instance'].password = None
                for field_name in ('email_address', 'share', 'presence'):
                    self.fields[field_name].initial = getattr(
                        kwargs['instance'].profile, field_name)

        def save(self, commit=True, request=None, **kwargs):
            # The field clean method (or something) checks that the username
            # isn't already taken.
            new_user = super().save(commit=False)
            new_user.password = self.cleaned_data['username']
            new_user.email=self.cleaned_data['email_address']
            coop = request.user.profile.coop
            profile = UserProfile(
                user=new_user, coop=coop,
                nickname=self.cleaned_data['nickname'],
                email_address=self.cleaned_data['email_address'],
                presence=self.cleaned_data['presence'],
                share=self.cleaned_data['share']
            )
            profile.save()
            if commit:
                new_user.save()
                new_user.profile = profile
                coop.user_set.add(new_user)
            # TODO: email new user here with instructions. CC steward (maybe
            # just CC the person who made the request, to allow for other
            # people to create users in the future).
            return new_user

        @classmethod
        def edit_object(cls, request=None, object_id=None):
            print('in user_form.edit_object')
            form = cls(request.POST,
                       instance=cls.Meta.model.objects.get(pk=object_id))
            if form.is_valid():
                user = form.save()
                for field_name in ('nickname', 'email_address', 'presence',
                                   'share'):
                    setattr(user.profile, field_name,
                            form.cleaned_data[field_name])
                user.profile.save()
            return form

    return UserForm

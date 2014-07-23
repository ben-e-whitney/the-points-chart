from django import forms
from django.contrib.auth.models import User

from chores.forms import BasicForm
from profiles.models import UserProfile

# TODO: add password editing here.
class UserProfileForm(BasicForm):
    # TODO: add in a password field.
    class Meta:
        model = UserProfile
        fields = ['nickname', 'first_name', 'middle_name', 'last_name',
                  'email_address', 'phone_number', 'phone_carrier']

    def clean(self):
        super().clean()
        # if self.receive_email_reminders and self.email_address = '':
            # raise ValidationError('...')
        # if self.receive_text_reminders and (self.phone_number = '' or
                                            # self.phone_carrier is None):
            # raise ValidationError('...')
        return self.cleaned_data

def UserFormCreator(coop):
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
    return UserForm

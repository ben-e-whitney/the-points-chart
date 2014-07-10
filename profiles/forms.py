from django import forms

from profiles.models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nickname', 'first_name', 'middle_name', 'last_name',
                  'email_address', 'phone_number', 'phone_carrier']
    error_css_class = 'form_error'

    def clean(self):
        super().clean()
        # if self.receive_email_reminders and self.email_address = '':
            # raise ValidationError('...')
        # if self.receive_text_reminders and (self.phone_number = '' or
                                            # self.phone_carrier is None):
            # raise ValidationError('...')
        return self.cleaned_data

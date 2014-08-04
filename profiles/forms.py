from utilities.forms import BasicForm
from profiles.models import UserProfile, GroupProfile

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

class GroupProfileForm(BasicForm):
    class Meta:
        model = GroupProfile
        fields = ['full_name', 'short_name', 'short_description',
                  'time_zone', 'email_prefix', 'release_buffer']

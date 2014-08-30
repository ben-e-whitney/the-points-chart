from utilities.forms import BasicForm
from profiles.models import UserProfile, GroupProfile

class UserProfileForm(BasicForm):
    # TODO: add in a password field.
    class Meta:
        model = UserProfile
        fields = ['nickname', 'first_name', 'middle_name', 'last_name',
                  'email_address', 'phone_number', 'public_calendar']

    def clean(self):
        super().clean()
        # if self.receive_email_reminders and self.email_address = '':
            # raise ValidationError('...')
        # if self.receive_text_reminders and (self.phone_number = '' or
                                            # self.phone_carrier is None):
            # raise ValidationError('...')
        return self.cleaned_data

    def save(self, commit=True, request=None, **kwargs):
        profile = super().save(commit=False)
        profile.user     = request.user
        profile.coop     = request.user.profile.coop
        profile.share    = request.user.profile.share
        profile.presence = request.user.profile.presence
        if commit:
            profile.save()
        return profile

class GroupProfileForm(BasicForm):
    class Meta:
        model = GroupProfile
        fields = ['full_name', 'short_name', 'short_description',
                  'time_zone', 'email_prefix', 'release_buffer']

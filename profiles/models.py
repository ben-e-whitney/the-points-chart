from django.db import models

# Create your models here.

from django.contrib.auth.models import User, Group
from django.forms import ModelForm
from django.core.exceptions import ValidationError

import localflavor.us.models
import timezone_field
import datetime

# TODO: look into the 'unique' field option
# <https://docs.djangoproject.com/en/dev/ref/models/fields/#unique>
# Some things should definitely not be unique, though -- for example
# Stewardships, since we want to allow them to switch hands partway through a
# semester in case someone leaves or can't do it.

# TODO!! Apparently AUTH_PROFILE_MODULE is deprecated. So look into that.
# TODO: how should profiles be handled again? Not subclasses. Just do the same
# thing for both group and user profiles.

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, primary_key=True,
                                 related_name='profile')
    # TODO: careful. group.name doesn't a priori need to be unique, which is
    # going to cause problems if you use 'coops/Dudley/chores'.
    # Idea: do like 'thepointschart.com/dudley/chores' and only forbid a given
    # user from being a member of two Groups with the same name. That would
    # probably be fine. Seems clear that 'thepointschart.com/group_id/chores'
    # is the way to go, but it is so ugly.
    # Possible way out: if a user were to be a member of two co-ops, force two
    # different accounts. This isn't ever going to happen anyway.
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    full_name  = models.CharField(max_length=2**6)
    time_zone = timezone_field.TimeZoneField()
    # Preferences.
    email_prefix = models.CharField(max_length=2**6, default='[Points]',
                                    null=True, blank=True)
    start_date = models.DateField()
    cycle_length = models.PositiveSmallIntegerField()
    # TODO: better name?
    release_buffer = models.PositiveSmallIntegerField()
    def __str__(self):
        return 'GroupProfile for {gro}'.format(gro=self.group.name)

    def cycles(self, start_date=None, stop_date=None):
        if start_date is None:
            start_date = self.start_date
        window_width = datetime.timedelta(days=self.cycle_length)
        if stop_date is None:
            stop_date = datetime.date.today()+datetime.timedelta(
                days=self.release_buffer)
        assert window_width > datetime.timedelta(days=0)
        assert stop_date >= start_date
        cycle_num = 1
        window = [start_date, start_date+window_width]
        while stop_date >= window[0]:
            yield cycle_num, window[0], window[1]
            window = [window[1]+datetime.timedelta(days=1),
                      window[1]+datetime.timedelta(days=1)+window_width]
            cycle_num += 1


class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True, related_name='profile')
    coop = models.ForeignKey(Group)
    # Want to allow for a middle name, so I'm going to leave the first_name and
    # last_name fields in User blank and just keep everything here. Can't just
    # do nickname and full name because we'll need a split for exporting
    # contacts.
    nickname    = models.CharField(max_length=2**6)
    first_name  = models.CharField(max_length=2**6, null=True, blank=True)
    middle_name = models.CharField(max_length=2**6, null=True, blank=True)
    last_name   = models.CharField(max_length=2**6, null=True, blank=True)
    email_address = models.EmailField()

    # TODO: At least for now, this complains if we give it 'blank=True'.
    phone_number = localflavor.us.models.PhoneNumberField()
    # TODO: somewhere this needs to be checked against a table of carriers and
    # gateways. Where to do this? Actually, this should probably be a choice
    # between a dropdown list of options.
    phone_carrier = models.CharField(max_length=2**6, blank=True, null=True)

    # A standard load of 100% will be stored as 1 here.
    share = models.DecimalField(max_digits=3, decimal_places=2)
    presence = models.PositiveSmallIntegerField()
    def __str__(self):
        return 'UserProfile for {use}'.format(use=self.user.username)
    # TODO: add methods here to calculate presence and share?

class UserProfileForm(ModelForm):
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

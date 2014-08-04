from django.db import models

# Create your models here.

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

import localflavor.us.models
import timezone_field
import datetime

# TODO: look into the 'unique' field option
# <https://docs.djangoproject.com/en/dev/ref/models/fields/#unique>
# Some things should definitely not be unique, though -- for example
# Stewardships, since we want to allow them to switch hands partway through a
# semester in case someone leaves or can't do it.

# TODO: how should profiles be handled again? Not subclasses. Just do the same
# thing for both group and user profiles.

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
    # This value should be in days.
    presence = models.PositiveSmallIntegerField()
    def __str__(self):
        return 'UserProfile for {use}'.format(use=self.user.username)
    # TODO: add methods here to calculate presence and share?

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, primary_key=True,
                                 related_name='profile')
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    full_name  = models.CharField(max_length=2**6)
    time_zone = timezone_field.TimeZoneField()
    # Preferences.
    email_prefix = models.CharField(max_length=2**6, default='[Points]',
                                    null=True, blank=True)
    start_date = models.DateField()
    # TODO: if this is changed in the middle of the semester it could cause
    # havoc (writing this just after making cycle-picker for new Loans and
    # ShareChanges). Maybe this should not be editable by anyone but an admin.
    cycle_length = models.PositiveSmallIntegerField()
    # TODO: better name?
    release_buffer = models.PositiveSmallIntegerField()
    def __str__(self):
        return 'GroupProfile for {gro}'.format(gro=self.group.name)

    def cycles(self, start_date=None, stop_date=None):

        def ceil_integer_division(x, y):
            return x//y+(1 if x%y else 0)

        if start_date is None:
            start_date = self.start_date
        window_width = datetime.timedelta(days=self.cycle_length)
        if stop_date is None:
            stop_date = datetime.date.today()+datetime.timedelta(
                days=self.release_buffer)
        assert window_width > datetime.timedelta(days=0)
        assert stop_date >= start_date
        num_cycles = ceil_integer_division((stop_date-start_date).days,
                                           self.cycle_length)
        num_width = len(str(num_cycles))
        window = [start_date, start_date+window_width]
        for cycle_index in range(num_cycles):
            yield str(1+cycle_index).zfill(num_width), window[0], window[1]
            window = [window[1]+datetime.timedelta(days=1),
                      window[1]+datetime.timedelta(days=1)+window_width]

    def get_cycle_endpoints(self, cycle_num):
        cycle_start_date = self.start_date+datetime.timedelta(
            days=1+self.cycle_length)*(cycle_num-1)
        cycle_stop_date = cycle_start_date+datetime.timedelta(
            days=self.cycle_length)
        return (cycle_start_date, cycle_stop_date)

    def get_cycle(self, cycle_start_date, cycle_stop_date):
        for cycle_num, start_date, stop_date in self.cycles():
            if cycle_start_date == start_date and cycle_stop_date == stop_date:
                return int(cycle_num)
        else:
            raise ValueError('No cycle matched.')

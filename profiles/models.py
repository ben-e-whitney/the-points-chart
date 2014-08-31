from django.db import models

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

class UserProfile(models.Model):
    #`null` and `blank` are set to be `True` to make editing of users by the
    #steward easier.
    user = models.OneToOneField(User, blank=True, related_name='profile')
    coop = models.ForeignKey(Group)
    # Want to allow for a middle name, so I'm going to leave the first_name and
    # last_name fields in User blank and just keep everything here. Can't just
    # do nickname and full name because we'll need a split for exporting
    # contacts.
    nickname    = models.CharField(max_length=2**6)
    #TODO: see <https://docs.djangoproject.com/en/dev/ref/models/fields/#null>.
    #Convention is to not use `null` here.
    first_name  = models.CharField(max_length=2**6, blank=True)
    middle_name = models.CharField(max_length=2**6, blank=True)
    last_name   = models.CharField(max_length=2**6, blank=True)
    email_address = models.EmailField()
    birthday = models.DateField(null=True, blank=True)

    # TODO: This complains if we give it 'blank=True'.
    phone_number = localflavor.us.models.PhoneNumberField()
    # TODO: somewhere this needs to be checked against a table of carriers and
    # gateways. Where to do this? Actually, this should probably be a choice
    # between a dropdown list of options.
    phone_carrier = models.CharField(max_length=2**6, blank=True)
    public_calendar = models.BooleanField()
    points_steward  = models.BooleanField()

    # A standard load of 100% will be stored as 1 here.
    share = models.DecimalField(max_digits=3, decimal_places=2)
    # This value should be in days.
    presence = models.PositiveSmallIntegerField()
    def __str__(self):
        return 'UserProfile for {use}'.format(use=self.user.username)
    # TODO: add methods here to calculate presence and share for a given cycle?

class GroupProfile(models.Model):
    #`null` and `blank` chosen to mirror `UserProfile` setup.
    group = models.OneToOneField(Group, null=True, blank=True,
                                 related_name='profile')
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    full_name  = models.CharField(max_length=2**6)
    time_zone = timezone_field.TimeZoneField()
    email_prefix = models.CharField(max_length=2**6, default='[Points]',
                                    blank=True)
    start_date = models.DateField()
    # TODO: if this is changed in the middle of the semester it could cause
    # havoc (writing this just after making cycle-picker for new Loans and
    # ShareChanges). Maybe this should not be editable by anyone but an admin.
    cycle_length = models.PositiveSmallIntegerField()
    release_buffer = models.PositiveSmallIntegerField()
    def __str__(self):
        return 'GroupProfile for {gro}'.format(gro=self.group.name)

    def now(self):
        return datetime.datetime.now(self.time_zone)

    def today(self):
        return self.now().date()

    def cycles(self, start_date=None, stop_date=None):

        def ceil_integer_division(x, y):
            return x//y+(1 if x%y else 0)

        if start_date is None:
            start_date = self.start_date
        window_width = datetime.timedelta(days=self.cycle_length)
        if stop_date is None:
            stop_date = (datetime.datetime.now(self.time_zone).date()+
                datetime.timedelta(days=self.release_buffer))
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

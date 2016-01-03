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
    """
    Contains settings for and information about a User.

    Attributes:
        user: corresponding User.
        coop: Group to which `user`belongs.
        nickname: display name for `user`.
        first_name: first name of `user` (used in contact).
        middle_name: middle name of `user` (used in contact).
        last_name: last name of `user` (used in contact).
        email_address: email address of `user`.
        birthday: birthday of `user`.
        phone_number: phone number of `user`.
        phone_carrier: carrier that provides service for `phone_number`.
            Currently unused.
        public_calendar: flag for whether to allow web access for `user`'s
            chores.
        points_steward: flag for whether `user` is the points steward.
        share: default points share for `user`, as a multiple of the default
            share.
        presence: default presence for `user`, in days per cycle.
        cached_balance: previously calculated points balance for `user`.
            Currently unused.
    """
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
    cached_balance = models.FloatField(null=True, blank=True)

    def __str__(self):
        """
        Return string representation of `self`.
        """
        return 'UserProfile for {use}'.format(use=self.user.username)

def bound_dates(*keywords):
    def decorator(f):
        def inner(self, *args, **kwargs):
            for keyword in keywords:
                value = kwargs.get(keyword, None)
                #If the keyword argument is not provided, we will trust the
                #method to handle things appropriately.
                if value is not None and (value < self.start_date or
                                          value > self.stop_date):
                    raise ValueError('Invalid date.')
            else:
                return f(self, *args, **kwargs)
        return inner
    return decorator

class GroupProfile(models.Model):
    """
    Contains settings for an information about a Group.

    Attributes:
        group: corresponding Group.
        short_name: short name for `group`.
        full_name: long name for `group`.
        short_description: short description for `group`.
        time_zone: time zone to use for the co-op's Chores, Stewardships, etc.
        email_address: email address for `group`.
        email_prefix: prefix to use in subjects of emails sent to
            `email_address`. For example, if the prefix is 'Points', subjects
            will begin with '[Points]'. Currently unused.
        start_date: date on which to start chart for `group`.
        stop_date: date on which to stop chart for `group`.
        cycle_length: length in days of `group`'s points cycle.
        release_buffer: length of time in days before start of new cycle that
            users of `group` should be able to see new chores.
    """
    #`null` and `blank` chosen to mirror `UserProfile` setup.
    group = models.OneToOneField(Group, null=True, blank=True,
                                 related_name='profile')
    short_name = models.CharField(max_length=2**6)
    full_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    time_zone = timezone_field.TimeZoneField()
    #TODO: activate at some point.
    #email_address = models.EmailField()
    email_prefix = models.CharField(max_length=2**6, default='[Points]',
                                    blank=True)
    start_date = models.DateField()
    stop_date = models.DateField()
    # TODO: if this is changed in the middle of the semester it could cause
    # havoc (writing this just after making cycle-picker for new Loans and
    # ShareChanges). Maybe this should not be editable by anyone but an admin.
    cycle_length = models.PositiveSmallIntegerField()
    release_buffer = models.PositiveSmallIntegerField()

    def __str__(self):
        """
        Return string representation of `self`.
        """
        return 'GroupProfile for {gro}'.format(gro=self.group.name)

    def now(self):
        """
        Return the current date and time in `self`'s time zone.
        """
        return datetime.datetime.now(self.time_zone)

    def today(self):
        """
        Return the current date in `self`'s time zone.
        """
        return self.now().date()

    #TODO: as of this writing this function isn't actually used anywhere.
    @bound_dates('date')
    def find_cycle(self, date=None):
        """
        Return the number of the cycle that contains `date`.

        Arguments:
            date: date in question.
        """
        if date < self.start_date or date > self.stop_date:
            raise ValueError('Invalid date.')
        else:
            return 1+(date-self.start_date).days//self.cycle_length

    @bound_dates('start_date', 'stop_date')
    def cycles(self, start_date=None, stop_date=None):
        """
        Yield cycles from `start_date` to `stop_date`.

        Keyword arguments:
            start_date: date at which to start cycles.
            stop_date: date at which to end cycles.
            offset: number of cycles by which to shift time interval.
        """
        if start_date is None:
            start_date = self.start_date
        if stop_date is None:
            stop_date = min(self.today()+datetime.timedelta(
                days=self.release_buffer), self.stop_date)
        if stop_date < start_date:
            raise ValueError('`stop_date` cannot come before `start_date`.')
        start_cycle = self.find_cycle(start_date)
        stop_cycle = self.find_cycle(stop_date)
        num_width = len(str(stop_cycle))
        intercycle_window = datetime.timedelta(days=self.cycle_length)
        intracycle_window = datetime.timedelta(days=self.cycle_length-1)
        for cycle_index in range(start_cycle, stop_cycle+1):
            first_day = self.start_date+(cycle_index-1)*intercycle_window
            last_day = first_day+intracycle_window
            yield str(cycle_index).zfill(num_width), first_day, last_day

    def get_cycle_endpoints(self, cycle_num):
        """
        Return the start and stop date of a cycle.

        Arguments:
            cycle_num: number of the cycle in question.
        """
        cycle_start_date = self.start_date+datetime.timedelta(
            days=self.cycle_length)*(cycle_num-1)
        cycle_stop_date = cycle_start_date+datetime.timedelta(
            days=self.cycle_length-1)
        if (cycle_start_date < self.start_date or
                cycle_stop_date > self.stop_date):
            raise ValueError('Invalid cycle number.')
        return (cycle_start_date, cycle_stop_date)

    @bound_dates('start_date', 'stop_date')
    def get_cycle(self, start_date=None, stop_date=None):
        """
        Return the number of the cycle with the given start and stop dates.

        Arguments:
            start_date: start date.
            stop_date: stop date.
        """
        for cycle_num, cycle_start_date, cycle_stop_date in self.cycles(
                stop_date=self.stop_date):
            if start_date == cycle_start_date and stop_date == cycle_stop_date:
                return int(cycle_num)
        else:
            raise ValueError('No cycle matched.')

    def points_steward(self):
        """
        Return the User that is the points steward of `self`.
        """
        return self.group.user_set.get(profile__points_steward=True)

from django.db import models

# Create your models here.

from django.contrib.auth.models import User, Group
import timezone_field
import localflavor.us.models

# TODO: look into the 'unique' field option
# <https://docs.djangoproject.com/en/dev/ref/models/fields/#unique>
# Some things should definitely not be unique, though -- for example Chores,
# since we want to allow partway through a semester

# TODO!! Apparently AUTH_PROFILE_MODULE is deprecated. So look into that.

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
    full_name  = models.CharField(max_length=2**6)
    short_description = models.TextField()
    time_zone = timezone_field.TimeZoneField()
    # Preferences.
    email_prefix = models.CharField(max_length=2**6, default='[Points]',
                                    null=True, blank=True)
    def __str__(self):
        return 'GroupProfile for {gro}'.format(gro=self.group.name)

class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True)
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
    # gateways. Where to do this?
    phone_carrier = models.CharField(max_length=2**6, blank=True, null=True)
    # Preferences. # TODO: how should this be done?
    coop = models.ForeignKey(Group)
    def __str__(self):
        return 'UserProfile for {use}'.format(use=self.user.username)


# import pytz
# coop = Coop(short_name='Dudley', short_description='3 Sac and 05.',
            # time_zone=pytz.timezone('UTC'), email_prefix='[Points]')
# coop.save()
# cooper = Cooper(full_name='Alex Traub', display_name='Alex', coop=coop)
# cooper.save()
